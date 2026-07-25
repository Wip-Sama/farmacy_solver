import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import tempfile
import csv
from datetime import date
from runner_core import (
    get_italian_holidays,
    parse_festivities,
    get_week_number_for_date,
    parse_prev_year_csv,
    generate_dynamic_constraints
)
from terminal_display import parse_schedule, generate_csv_report

class TestFestivities(unittest.TestCase):

    def test_get_italian_holidays_2025(self):
        holidays = get_italian_holidays(2025)
        self.assertEqual(holidays[date(2025, 1, 1)], "Capodanno")
        self.assertEqual(holidays[date(2025, 4, 25)], "Liberazione")
        self.assertEqual(holidays[date(2025, 5, 1)], "Festa del Lavoro")
        self.assertEqual(holidays[date(2025, 12, 25)], "Natale")
        self.assertEqual(holidays[date(2025, 12, 26)], "Santo Stefano")
        # Easter 2025 is April 20, Pasquetta is April 21
        self.assertEqual(holidays[date(2025, 4, 21)], "Pasquetta")

    def test_parse_festivities(self):
        # Auto festivities
        auto_dict = parse_festivities(None, True, 2025)
        self.assertIn(date(2025, 12, 25), auto_dict)

        # Custom festivities
        custom_args = ["TestFest,2025-07-04,2025-07-05", "SingleDay,2025-08-01"]
        fest_dict = parse_festivities(custom_args, False, 2025)
        self.assertEqual(fest_dict[date(2025, 7, 4)], "TestFest")
        self.assertEqual(fest_dict[date(2025, 7, 5)], "TestFest")
        self.assertEqual(fest_dict[date(2025, 8, 1)], "SingleDay")

    def test_parse_prev_year_csv(self):
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Settimana", "Data", "Festività", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"])
            writer.writerow([1, "2024-01-01", "Capodanno", "", "1", "", "1", "", "", "", "", "", ""])

        try:
            past_fest = parse_prev_year_csv(path)
            self.assertIn(("capodanno", 2), past_fest)
            self.assertIn(("capodanno", 4), past_fest)
            self.assertNotIn(("capodanno", 1), past_fest)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_generate_dynamic_constraints_with_festivities(self):
        fest_dict = {date(2025, 12, 25): "Natale"}  # Thursday (mid-week)
        dyn_path = generate_dynamic_constraints(
            reschedule_csv=None,
            reschedule_from=None,
            unavailables=None,
            unavailable_intervals=None,
            start_week=1,
            end_week=52,
            festivities_dict=fest_dict
        )

        try:
            with open(dyn_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn('festivita("natale"', content)
            self.assertIn('turno_festivo', content)
        finally:
            if os.path.exists(dyn_path):
                os.remove(dyn_path)

    def test_parse_schedule_and_csv_generation(self):
        mock_output = """
        turno(16, 1) turno(16, 2)
        turno_festivo("liberazione", 3) turno_festivo("liberazione", 4)
        """
        schedule, fest_sched = parse_schedule(mock_output)
        self.assertEqual(schedule[16], [1, 2])
        self.assertEqual(fest_sched["liberazione"], [3, 4])

        fest_dict = {date(2025, 4, 25): "Liberazione"}  # Friday in 2025 (Week 16)
        fd, csv_path = tempfile.mkstemp(suffix=".csv", text=True)
        os.close(fd)

        try:
            generate_csv_report(schedule, csv_path, run_info={'solver': 'clingo'}, year=2025, festivo_schedule=fest_sched, festivities_dict=fest_dict)
            with open(csv_path, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))

            header = rows[0]
            self.assertEqual(header[:3], ["Settimana", "Data", "Festività"])
            
            # Find Liberazione row
            liberazione_rows = [r for r in rows if len(r) > 2 and r[2] == "Liberazione"]
            self.assertEqual(len(liberazione_rows), 1)
            c_row = liberazione_rows[0]
            self.assertEqual(c_row[0], "16")
            self.assertEqual(c_row[1], "2025-04-25")
            # F3 (index 5) and F4 (index 6) should be "1"
            self.assertEqual(c_row[5], "1")
            self.assertEqual(c_row[6], "1")
            self.assertEqual(c_row[3], "") # F1
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

if __name__ == '__main__':
    unittest.main()
