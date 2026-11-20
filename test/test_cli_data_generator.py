import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, "..")))

from cli.data_generator import parse_validator_summary, run_validation


class TestParseValidatorSummary(unittest.TestCase):
    """Test parse_validator_summary function with various validator outputs."""

    def test_success_output(self):
        """Test parsing SUCCESS line."""
        output = """
========================================================
 CSV Schedule Validation: /path/to/schedule.csv
 Validation Mode: Python Rules Inspection
========================================================
 SUCCESS: CSV schedule adheres to all ASP rules!
  - At least 2 pharmacies per week
  - Summer Marina requirement satisfied (Criterio 3)
  - Max 1 Marina pharmacy per week (Criterio 4)
  - No consecutive-week assignments (Criterio 2)
  - Midweek festivity historical uniqueness verified
========================================================
"""
        result = parse_validator_summary(output)
        self.assertIn("SUCCESS", result)
        self.assertIn("CSV schedule adheres to all ASP rules", result)

    def test_failure_with_errors(self):
        """Test parsing FAILURE line with error details."""
        output = """
========================================================
 CSV Schedule Validation: /path/to/schedule.csv
 Validation Mode: Python Rules Inspection
========================================================
 FAILURE: Found 3 validation errors:
  [ERROR] Week 5: Expected at least 2 assigned pharmacies, found 1 (F3)
  [ERROR] Consecutive Week Violation between Week 10 and Week 11: Pharmacy F4 assigned on both weeks.
  [ERROR] Week 15 (Summer period 25..35): Expected at least 1 pharmacy in Marina (7..10), found 0
========================================================
"""
        result = parse_validator_summary(output)
        self.assertIn("FAILURE", result)
        self.assertIn("Found 3 validation errors", result)
        self.assertIn("Week 5", result)
        self.assertIn("Consecutive Week Violation", result)
        self.assertIn("Summer period", result)

    def test_failure_truncation(self):
        """Test that very long error output is truncated."""
        error_lines = "\n".join([f"  [ERROR] Very long error message #{i}" for i in range(50)])
        output = f" FAILURE: Found 50 validation errors:\n{error_lines}\n"
        result = parse_validator_summary(output)
        self.assertIn("FAILURE", result)
        # Should be truncated to ~500 chars
        self.assertLess(len(result), 600)
        if len(result) > 500:
            self.assertTrue(result.endswith("..."))

    def test_empty_output(self):
        """Test handling of empty validator output."""
        result = parse_validator_summary("")
        self.assertEqual(result, "No validator output")

    def test_no_success_or_failure_marker(self):
        """Test fallback to last line when no SUCCESS/FAILURE marker."""
        output = "Some random line 1\nSome random line 2\nFinal line"
        result = parse_validator_summary(output)
        self.assertEqual(result, "Final line")

    def test_only_whitespace(self):
        """Test handling of whitespace-only output."""
        result = parse_validator_summary("   \n  \n   ")
        self.assertEqual(result, "No validator output")


class TestRunValidation(unittest.TestCase):
    """Test run_validation function with various scenarios."""

    def test_missing_csv_file(self):
        """Test behavior when CSV file does not exist."""
        nonexistent_path = "/nonexistent/path/schedule.csv"
        result_code, result_detail = run_validation(nonexistent_path, None)
        self.assertEqual(result_code, "NOT_RUN_NO_CSV")
        self.assertIn("CSV output missing", result_detail)
        self.assertIn(nonexistent_path, result_detail)

    @patch('subprocess.run')
    def test_validation_success(self, mock_run):
        """Test successful validation result."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=" SUCCESS: CSV schedule adheres to all ASP rules!\n",
            stderr=""
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_csv = f.name
            f.write("week,pharmacy\n1,1\n1,2\n")
        try:
            result_code, result_detail = run_validation(temp_csv, None)
            self.assertEqual(result_code, "VALID")
            self.assertIn("SUCCESS", result_detail)
        finally:
            os.unlink(temp_csv)

    @patch('subprocess.run')
    def test_validation_failure(self, mock_run):
        """Test failed validation result."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=" FAILURE: Found 2 validation errors:\n  [ERROR] Week 5: Expected at least 2 assigned pharmacies\n  [ERROR] Consecutive Week Violation\n",
            stderr=""
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_csv = f.name
            f.write("week,pharmacy\n1,1\n")
        try:
            result_code, result_detail = run_validation(temp_csv, None)
            self.assertEqual(result_code, "INVALID")
            self.assertIn("FAILURE", result_detail)
            self.assertIn("validation errors", result_detail)
        finally:
            os.unlink(temp_csv)

    @patch('subprocess.run')
    def test_validation_error(self, mock_run):
        """Test unexpected validator exit code."""
        mock_run.return_value = MagicMock(
            returncode=127,
            stdout="",
            stderr="Command not found"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_csv = f.name
            f.write("week,pharmacy\n1,1\n1,2\n")
        try:
            result_code, result_detail = run_validation(temp_csv, None)
            self.assertEqual(result_code, "VALIDATION_ERROR")
            self.assertIn("Unexpected validator exit code", result_detail)
        finally:
            os.unlink(temp_csv)

    @patch('subprocess.run')
    def test_validation_with_prev_year(self, mock_run):
        """Test validation with previous year CSV parameter."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=" SUCCESS: CSV schedule adheres to all ASP rules!\n",
            stderr=""
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_csv = f.name
            f.write("week,pharmacy\n1,1\n1,2\n")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
            prev_csv = f2.name
            f2.write("week,pharmacy\n1,1\n1,2\n")
        try:
            result_code, _result_detail = run_validation(temp_csv, prev_csv)
            self.assertEqual(result_code, "VALID")
            # Verify that --prev-year was passed to subprocess
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn("--prev-year", call_args)
            self.assertIn(prev_csv, call_args)
        finally:
            os.unlink(temp_csv)
            os.unlink(prev_csv)


if __name__ == '__main__':
    unittest.main()
