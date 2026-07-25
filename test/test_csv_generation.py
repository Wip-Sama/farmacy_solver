import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import tempfile
import csv
from datetime import date
from terminal_display import generate_csv_report, parse_pharmacy_mapping
from runner_core import parse_prev_year_csv, generate_dynamic_constraints

class TestCSVGeneration(unittest.TestCase):
    def setUp(self):
        self.schedule = {
            1: [1, 2],
            2: [3, 4]
        }
        self.fest_dict = {
            date(2025, 1, 6): "Epifania",
            date(2025, 1, 7): "Festa"
        }

    def test_parse_pharmacy_mapping_string(self):
        mapping = parse_pharmacy_mapping("1,BUCCARELLI; 2,SANMICHELE")
        self.assertEqual(mapping[1], "BUCCARELLI")
        self.assertEqual(mapping[2], "SANMICHELE")

    def test_csv_mode_compact(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.schedule, path, year=2025, festivities_dict=self.fest_dict, csv_mode="compact")
            with open(path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertTrue(rows[0][0].startswith('# Metadata'))
            self.assertIn("Mode=compact", rows[0][0])
            self.assertEqual(rows[1][:3], ['Settimana', 'Data Inizio', 'Festività'])
            self.assertEqual(rows[1][3:], ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10'])
            self.assertEqual(rows[2][0], "1")
            self.assertEqual(rows[2][3], "1") # F1
            self.assertEqual(rows[2][4], "1") # F2
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_csv_mode_tiny(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.schedule, path, year=2025, festivities_dict=self.fest_dict, csv_mode="tiny")
            with open(path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertTrue(rows[0][0].startswith('# Metadata'))
            self.assertIn("Mode=tiny", rows[0][0])
            self.assertEqual(rows[1], ['Settimana', 'Data Inizio', 'Festività', 'Farmacie di Turno'])
            self.assertEqual(rows[2][0], "1")
            self.assertEqual(rows[2][3], "F1-F2")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_csv_mode_extended(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.schedule, path, year=2025, festivities_dict=self.fest_dict, csv_mode="extended")
            with open(path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertTrue(rows[0][0].startswith('# Metadata'))
            self.assertEqual(rows[1][:4], ['Settimana', 'Data', 'Giorno', 'Festività'])
            self.assertEqual(rows[1][4:], ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10'])
            self.assertEqual(len(rows), 16)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_csv_direction_row_and_mapping(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        mapping_str = "1,BUCCARELLI; 2,SANMICHELE; 3,DAVID; 4,CENTRALE"
        try:
            generate_csv_report(
                self.schedule, path, year=2025, festivities_dict=self.fest_dict,
                csv_direction="row", csv_map_pharmacies=mapping_str
            )
            with open(path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            
            self.assertTrue(rows[0][0].startswith('# Metadata'))
            self.assertIn("Direction=row", rows[0][0])
            self.assertEqual(rows[1][0], "Gennaio")
            self.assertEqual(rows[2][:4], ["Giorno", "Lu-Do", "Festività", "Farmacie di Turno"])
            self.assertEqual(len(rows), 34)
            # Jan 6 (row 8): Epifania, pharmacies BUCCARELLI-SANMICHELE
            self.assertEqual(rows[8][0], "6")
            self.assertEqual(rows[8][2], "Epifania")
            self.assertEqual(rows[8][3], "BUCCARELLI-SANMICHELE")

            past_fest = parse_prev_year_csv(path)
            self.assertIn(("epifania", 1), past_fest)
            self.assertIn(("epifania", 2), past_fest)
            self.assertIn(("festa", 1), past_fest)
            self.assertIn(("festa", 2), past_fest)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_prev_year_parsing_normal_csv(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(self.schedule, path, year=2025, festivities_dict=self.fest_dict, csv_mode="normal")
            past_fest = parse_prev_year_csv(path)
            self.assertIn(("epifania", 1), past_fest)
            self.assertIn(("epifania", 2), past_fest)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_first_day_of_week_saturday(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)
        try:
            generate_csv_report(
                self.schedule, path, year=2026, festivities_dict=self.fest_dict,
                first_day_of_week="saturday"
            )
            with open(path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertTrue(rows[0][0].startswith('# Metadata'))
            self.assertIn("FirstDayOfWeek=saturday", rows[0][0])
            self.assertEqual(rows[2][0], "1")
            self.assertEqual(rows[2][1], "2026-01-01")
            self.assertEqual(rows[3][0], "2")
            self.assertEqual(rows[3][1], "2026-01-03")
        finally:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    unittest.main()
