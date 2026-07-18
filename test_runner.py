import unittest
import subprocess
import os

class TestRunner(unittest.TestCase):
    def test_dlv_argument_parsing(self):
        # We can't easily mock argparse inside the script execution without refactoring main,
        # but we can test that calling the script with --help works.
        result = subprocess.run(
            ['python', 'runner.py', '--help'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertIn('--opt', result.stdout)
        self.assertIn('--dlv', result.stdout)
        self.assertIn('--clingo', result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_missing_opt_argument(self):
        result = subprocess.run(
            ['python', 'runner.py', '--dlv'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('the following arguments are required: --opt', result.stderr)

    def test_invalid_opt_argument(self):
        result = subprocess.run(
            ['python', 'runner.py', '--opt', 'invalid_opt'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid choice', result.stderr)

if __name__ == '__main__':
    unittest.main()
