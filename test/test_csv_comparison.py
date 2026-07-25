import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import tempfile
from csv_utils import generate_csv_report, read_csv_schedule

class TestCSVComparison(unittest.TestCase):
    def setUp(self):
        self.sched1 = {1: [1, 7], 2: [2, 8]}
        self.sched2 = {1: [1, 7], 2: [3, 9]}

    def test_compare_read(self):
        fd1, path1 = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd1)
        fd2, path2 = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd2)

        try:
            generate_csv_report(self.sched1, path1, year=2025, csv_mode="compact")
            generate_csv_report(self.sched2, path2, year=2025, csv_mode="compact")

            read1, meta1, _, _, _ = read_csv_schedule(path1)
            read2, meta2, _, _, _ = read_csv_schedule(path2)

            self.assertEqual(read1[1], {1, 7})
            self.assertEqual(read1[2], {2, 8})
            self.assertEqual(read2[2], {3, 9})
        finally:
            if os.path.exists(path1):
                os.remove(path1)
            if os.path.exists(path2):
                os.remove(path2)

if __name__ == '__main__':
    unittest.main()
