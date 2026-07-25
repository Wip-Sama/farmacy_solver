import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import subprocess

class TestRunner(unittest.TestCase):
    def test_help_argument_parsing(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        runner_path = os.path.join(root_dir, 'runner.py')
        result = subprocess.run(
            [sys.executable, runner_path, '--help'],
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
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        runner_path = os.path.join(root_dir, 'runner.py')
        result = subprocess.run(
            [sys.executable, runner_path, '--opt', 'invalid_opt'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid choice', result.stderr)

if __name__ == '__main__':
    unittest.main()
