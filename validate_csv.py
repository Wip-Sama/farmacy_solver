import sys
import os
import argparse
import tempfile
import logging
from collections import defaultdict
from csv_utils import read_csv_schedule, parse_first_day_of_week

from datetime import date

def get_summer_weeks(year: int = 2025, first_day_of_week: int | str = 0) -> tuple[int, int]:
    """Calculates summer period start and end week numbers for June 15 - Sept 15."""
    from runner_core import get_week_number_for_date
    w_start = get_week_number_for_date(date(year, 6, 15), year, first_day_of_week)
    w_end = get_week_number_for_date(date(year, 9, 15), year, first_day_of_week)
    return w_start, w_end

def validate_csv(csv_path: str, prev_year_csv: str = None) -> tuple[bool, list[str]]:
    """
    Validates a generated CSV schedule against ASP domain rules using Python inspection.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    
    if not os.path.exists(csv_path):
        return False, [f"File not found: {csv_path}"]

    schedule, metadata, pharmacy_map, past_festivities, raw_rows = read_csv_schedule(csv_path)

    if not schedule:
        errors.append("No weekly schedule assignments could be parsed from the CSV file.")
        return False, errors

    try:
        year = int(metadata.get('year', 2025))
    except (ValueError, TypeError):
        year = 2025

    first_day_of_week = metadata.get('firstdayofweek', 'monday')
    summer_start, summer_end = get_summer_weeks(year, first_day_of_week)

    # Criterio 1: At least 2 assigned pharmacies per week (standard is exactly 2)
    for week in sorted(schedule.keys()):
        pharmacies = schedule[week]
        if len(pharmacies) < 2:
            errors.append(f"Week {week}: Expected at least 2 assigned pharmacies, found {len(pharmacies)} ({sorted(pharmacies)})")

    # Criterio 2: No pharmacy serves on consecutive weeks (W and W+1)
    weeks = sorted(schedule.keys())
    for i in range(len(weeks) - 1):
        w1, w2 = weeks[i], weeks[i+1]
        if w2 == w1 + 1:
            overlap = schedule[w1].intersection(schedule[w2])
            if overlap:
                overlap_names = [pharmacy_map.get(f, f"F{f}") for f in sorted(overlap)]
                errors.append(f"Consecutive Week Violation between Week {w1} and Week {w2}: Pharmacy {', '.join(overlap_names)} assigned on both weeks.")

    # Criterio 3: Summer period (June 15 - Sept 15: weeks summer_start..summer_end) must have at least 1 Marina pharmacy (7..10)
    for week in sorted(schedule.keys()):
        if summer_start <= week <= summer_end:
            pharmacies = schedule[week]
            marina = [f for f in pharmacies if 7 <= f <= 10]
            if len(marina) < 1:
                errors.append(f"Week {week} (Summer period {summer_start}..{summer_end}): Expected at least 1 pharmacy in Marina (7..10), found 0")

    # Criterio 4: Cannot have 2 Marina pharmacies assigned in the same week
    for week in sorted(schedule.keys()):
        pharmacies = schedule[week]
        marina = [f for f in pharmacies if 7 <= f <= 10]
        if len(marina) > 1:
            marina_names = [pharmacy_map.get(f, f"F{f}") for f in sorted(marina)]
            errors.append(f"Week {week}: Cannot assign 2 Marina pharmacies in the same week (Criterio 4), found {len(marina)} ({', '.join(marina_names)})")

    # Criterio Festività: Midweek festivity historical uniqueness (if prev_year provided)
    if prev_year_csv and os.path.exists(prev_year_csv):
        _, _, _, prev_festivities, _ = read_csv_schedule(prev_year_csv)
        if past_festivities and prev_festivities:
            overlap_fest = past_festivities.intersection(prev_festivities)
            if overlap_fest:
                for fest_name, fid in sorted(overlap_fest):
                    fname = pharmacy_map.get(fid, f"F{fid}")
                    errors.append(f"Consecutive Year Festivity Violation: Pharmacy {fname} covered festivity '{fest_name.capitalize()}' in both years.")

    is_valid = len(errors) == 0
    return is_valid, errors

def validate_csv_asp(csv_path: str, prev_year_csv: str = None, year: int = None) -> tuple[bool, str, list[str]]:
    """
    Validates a CSV schedule by loading it as ASP facts into Clingo solver alongside domain.lp and constraints.lp.
    Returns (is_coherent, clingo_status_str, list_of_error_details).
    """
    if not os.path.exists(csv_path):
        return False, "File Not Found", [f"File not found: {csv_path}"]

    try:
        import clingo
    except ImportError:
        return False, "Clingo Not Available", ["The 'clingo' Python module is not installed. Please install it using 'pip install clingo'."]

    schedule, metadata, pharmacy_map, past_festivities, _ = read_csv_schedule(csv_path)

    if not schedule:
        return False, "Empty Schedule", ["No weekly schedule assignments could be parsed from the CSV file."]

    if year is None:
        try:
            year = int(metadata.get('year', 2025))
        except (ValueError, TypeError):
            year = 2025

    first_day_of_week = metadata.get('firstdayofweek', 'monday')
    summer_start, summer_end = get_summer_weeks(year, first_day_of_week)

    # Fact lines representing the CSV schedule
    fact_lines = ["% Facts extracted from CSV schedule for ASP validation\n"]
    max_week = max(schedule.keys()) if schedule else 52
    fact_lines.append(f"settimana(1..{max_week}).\n")
    fact_lines.append(f"estate({summer_start}..{summer_end}).\n")
    fact_lines.append("inverno(W) :- settimana(W), not estate(W).\n\n")

    for w in sorted(schedule.keys()):
        for f in sorted(schedule[w]):
            fact_lines.append(f"turno({w}, {f}).\n")

    # Historical festivities facts
    if prev_year_csv and os.path.exists(prev_year_csv):
        _, _, _, prev_festivities, _ = read_csv_schedule(prev_year_csv)
        for fest_name, fid in prev_festivities:
            fact_lines.append(f'past_festivita("{fest_name}", {fid}).\n')

    # National holidays facts
    try:
        from runner_core import get_italian_holidays, get_week_number_for_date
        holidays = get_italian_holidays(year)
        for fest_date, fest_name in holidays.items():
            if fest_date.weekday() < 5:  # Monday to Friday
                w_num = get_week_number_for_date(fest_date, year, first_day_of_week)
                fact_lines.append(f'festivita("{fest_name.lower()}", {w_num}).\n')
    except Exception as e:
        logging.warning(f"Could not calculate Italian holidays for ASP validation: {e}")

    # Write temporary facts LP file
    tmp_fd, tmp_facts_path = tempfile.mkstemp(suffix=".lp", text=True)
    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
        f.writelines(fact_lines)

    try:
        domain_file = os.path.join("asp", "domain.lp")
        constraints_file = os.path.join("asp", "constraints.lp")

        if not os.path.exists(domain_file) or not os.path.exists(constraints_file):
            return False, "ASP Files Missing", ["Required ASP files (domain.lp, constraints.lp) not found in asp/ directory."]

        ctl = clingo.Control()
        ctl.load(domain_file)
        ctl.load(constraints_file)
        ctl.load(tmp_facts_path)
        ctl.ground([("base", [])])

        res = ctl.solve()
        is_sat = res.satisfiable

        if is_sat:
            return True, "SATISFIABLE (Coherent)", []
        else:
            return False, "UNSATISFIABLE (Incoherent)", ["The CSV schedule violates one or more ASP constraints in asp/constraints.lp."]
    except Exception as e:
        return False, "Clingo Error", [f"Clingo solver error during ASP validation: {e}"]
    finally:
        if os.path.exists(tmp_facts_path):
            os.remove(tmp_facts_path)


def main():
    parser = argparse.ArgumentParser(
        description="Validator script to verify a generated CSV schedule against ASP rules."
    )
    parser.add_argument('csv_path', help="Path to the generated CSV schedule to validate.")
    parser.add_argument('--prev-year', help="Path to previous year CSV schedule for festivity history check.")
    parser.add_argument('--asp', action='store_true', help="Use Clingo ASP solver to validate coherence against asp/constraints.lp.")
    
    args = parser.parse_args()

    print("=" * 65)
    print(f" CSV Schedule Validation: {args.csv_path}")
    if args.asp:
        print(" Validation Mode: ASP Clingo Coherence Solver")
    else:
        print(" Validation Mode: Python Rules Inspection")
    print("=" * 65)

    if args.asp:
        is_valid, status, errors = validate_csv_asp(args.csv_path, args.prev_year)
        if is_valid:
            print(f" SUCCESS: CSV schedule is COHERENT! ({status})")
            print("  - Passed all hard constraints in asp/domain.lp & asp/constraints.lp")
            print("=" * 65)
            sys.exit(0)
        else:
            print(f" FAILURE: CSV schedule is INCOHERENT! ({status})")
            for err in errors:
                print(f"  [ERROR] {err}")
            print("=" * 65)
            sys.exit(1)
    else:
        is_valid, errors = validate_csv(args.csv_path, args.prev_year)
        if is_valid:
            print(" SUCCESS: CSV schedule adheres to all ASP rules!")
            print("  - At least 2 pharmacies per week")
            print("  - Summer Marina requirement satisfied (Criterio 3)")
            print("  - Max 1 Marina pharmacy per week (Criterio 4)")
            print("  - No consecutive-week assignments (Criterio 2)")
            print("  - Midweek festivity historical uniqueness verified")
            print("=" * 65)
            sys.exit(0)
        else:
            print(f" FAILURE: Found {len(errors)} validation errors:")
            for err in errors:
                print(f"  [ERROR] {err}")
            print("=" * 65)
            sys.exit(1)

if __name__ == '__main__':
    main()
