import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import tempfile
from csv_utils import generate_csv_report
from validate_csv import validate_csv

class TestCSVValidation(unittest.TestCase):
    def setUp(self):
        # Valid 2-week schedule: 1 Centro (1..6) and 1 Marina (7..10) per week, no consecutive overlaps
        self.valid_schedule = {
            1: [1, 7],
            2: [2, 8]
        }
        self.invalid_count_schedule = {
            1: [1] # Only 1 pharmacy (< 2)
        }
        self.invalid_marina_pair_schedule = {
            1: [7, 8] # 2 Marina pharmacies (violates Criterio 4)
        }
        self.invalid_summer_schedule = {
            25: [1, 2] # Summer week 25 with 0 Marina (violates Criterio 3)
        }
        self.consecutive_overlap_schedule = {
            1: [1, 7],
            2: [1, 8] # Pharmacy 1 on consecutive weeks
        }

    def test_valid_schedule_passes(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.valid_schedule, path, year=2025)
            is_valid, errors = validate_csv(path)
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_invalid_count_fails(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.invalid_count_schedule, path, year=2025)
            is_valid, errors = validate_csv(path)
            self.assertFalse(is_valid)
            self.assertTrue(any("at least 2 assigned pharmacies" in e for e in errors))
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_invalid_marina_pair_fails(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.invalid_marina_pair_schedule, path, year=2025)
            is_valid, errors = validate_csv(path)
            self.assertFalse(is_valid)
            self.assertTrue(any("Criterio 4" in e for e in errors))
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_invalid_summer_marina_fails(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.invalid_summer_schedule, path, year=2025)
            is_valid, errors = validate_csv(path)
            self.assertFalse(is_valid)
            self.assertTrue(any("Summer" in e for e in errors))
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_consecutive_overlap_fails(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.consecutive_overlap_schedule, path, year=2025)
            is_valid, errors = validate_csv(path)
            self.assertFalse(is_valid)
            self.assertTrue(any("Consecutive Week Violation" in e for e in errors))
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_asp_validation(self):
        from validate_csv import validate_csv_asp
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.valid_schedule, path, year=2025)
            is_coherent, status, errors = validate_csv_asp(path)
            self.assertTrue(is_coherent)
            self.assertEqual(status, "SATISFIABLE (Coherent)")
        finally:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    unittest.main()
