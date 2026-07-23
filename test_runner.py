import unittest
import subprocess
import os

class TestRunner(unittest.TestCase):
    def test_help_argument_parsing(self):
        result = subprocess.run(
            ['python', 'runner.py', '--help'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertIn('--opt', result.stdout)
        self.assertIn('--festivities', result.stdout)
        self.assertIn('--auto-festivities', result.stdout)
        self.assertIn('--prev-year', result.stdout)
        self.assertEqual(result.returncode, 0)

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
