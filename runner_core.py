import os
import sys
import re
import csv
import time
import tempfile
import logging
import subprocess
from datetime import date, datetime, timedelta
from collections import defaultdict

def get_easter_date(year: int) -> date:
    """Calculates Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def get_italian_holidays(year: int) -> dict:
    """Returns a dict mapping date -> holiday name for national Italian holidays in the given year."""
    holidays = {
        date(year, 1, 1): "Capodanno",
        date(year, 1, 6): "Epifania",
        date(year, 4, 25): "Liberazione",
        date(year, 5, 1): "Festa del Lavoro",
        date(year, 6, 2): "Festa della Repubblica",
        date(year, 8, 15): "Ferragosto",
        date(year, 11, 1): "Ognissanti",
        date(year, 12, 8): "Immacolata",
        date(year, 12, 25): "Natale",
        date(year, 12, 26): "Santo Stefano",
    }
    easter = get_easter_date(year)
    pasquetta = easter + timedelta(days=1)
    holidays[pasquetta] = "Pasquetta"
    return holidays

def parse_festivities(festivities_args: list | None, auto_festivities: bool, year: int) -> dict:
    """
    Parses --festivities and --auto-festivities.
    Returns a dict mapping date -> holiday_name.
    """
    festivities_dict = {}
    if auto_festivities:
        festivities_dict.update(get_italian_holidays(year))

    if festivities_args:
        for item in festivities_args:
            parts = [p.strip() for p in item.split(',')]
            if len(parts) == 2:
                name, start_str = parts
                finish_str = start_str
            elif len(parts) == 3:
                name, start_str, finish_str = parts
            else:
                logging.error(f"Invalid format for --festivities: '{item}'. Expected 'name,start_date,finish_date' or 'name,date'")
                sys.exit(1)
            
            try:
                start_d = datetime.strptime(start_str, "%Y-%m-%d").date()
                finish_d = datetime.strptime(finish_str, "%Y-%m-%d").date()
            except ValueError as e:
                logging.error(f"Invalid date format in --festivities '{item}': {e}. Expected YYYY-MM-DD")
                sys.exit(1)

            curr = start_d
            while curr <= finish_d:
                festivities_dict[curr] = name
                curr += timedelta(days=1)

    return festivities_dict

def get_week_monday(week_number: int, year: int = 2025) -> date:
    """Calculates the Monday date for a given week number in a year."""
    d = date(year, 1, 1)
    if d.weekday() != 0:
        d += timedelta(days=(7 - d.weekday()))
    return d + timedelta(weeks=week_number - 1)

def get_week_number_for_date(d: date, year: int = 2025) -> int:
    """Finds which schedule week number a date belongs to."""
    first_monday = get_week_monday(1, year)
    delta_days = (d - first_monday).days
    if delta_days < 0:
        return 1
    return (delta_days // 7) + 1

def parse_prev_year_csv(csv_path: str) -> set:
    """
    Parses a previous year CSV to extract past festivity assignments.
    Returns a set of tuples: (festivity_name_lower, farmacia_id)
    """
    past_festivities = set()
    if not csv_path or not os.path.exists(csv_path):
        return past_festivities

    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return past_festivities
            
            headers_lower = [h.strip().lower() for h in headers]
            fest_col_idx = None
            for name in ['festività', 'festivita', 'festivities', 'festivity']:
                if name in headers_lower:
                    fest_col_idx = headers_lower.index(name)
                    break
            
            if fest_col_idx is None:
                return past_festivities

            farmacia_cols = {}
            for idx, h in enumerate(headers_lower):
                if h.startswith('f') and h[1:].isdigit():
                    farmacia_cols[int(h[1:])] = idx

            for row in reader:
                if not row or len(row) <= fest_col_idx:
                    continue
                fest_name = row[fest_col_idx].strip()
                if fest_name:
                    fest_name_clean = fest_name.lower()
                    for f_id, col_idx in farmacia_cols.items():
                        if col_idx < len(row) and row[col_idx].strip() == "1":
                            past_festivities.add((fest_name_clean, f_id))
    except Exception as e:
        logging.warning(f"Could not parse previous year CSV '{csv_path}': {e}")

    return past_festivities

def generate_dynamic_constraints(
    reschedule_csv: str | None,
    reschedule_from: int | None,
    unavailables: list | None,
    unavailable_intervals: list | None,
    start_week: int,
    end_week: int,
    festivities_dict: dict | None = None,
    prev_year_csv: str | None = None
) -> str:
    """
    Generates dynamic ASP rules in a temporary file for week limits, rescheduling, unavailabilities, and festivities.
    """
    lines = []
    actual_start_week = start_week

    if reschedule_csv and reschedule_from:
        actual_start_week = 1
        lines.append(f"reschedule_from({reschedule_from}).\n")
        try:
            with open(reschedule_csv, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader, None)
                headers_lower = [h.strip().lower() for h in headers] if headers else []
                fest_col_idx = None
                for name in ['festività', 'festivita', 'festivities', 'festivity']:
                    if name in headers_lower:
                        fest_col_idx = headers_lower.index(name)
                        break

                for row in reader:
                    if not row or len(row) < 12:
                        continue
                    try:
                        week = int(row[0])
                        if week < reschedule_from:
                            is_festivity_row = fest_col_idx is not None and len(row) > fest_col_idx and bool(row[fest_col_idx].strip())
                            fest_name = row[fest_col_idx].strip().lower() if is_festivity_row else None
                            
                            for i in range(1, 11):
                                col_idx = i + 1 if fest_col_idx is None else (i + 2 if fest_col_idx == 2 else i + 1)
                                if col_idx < len(row) and row[col_idx].strip() == "1":
                                    if is_festivity_row and fest_name:
                                        lines.append(f'past_turno_festivo("{fest_name}", {i}).\n')
                                    else:
                                        lines.append(f"past_turno({week}, {i}).\n")
                    except ValueError:
                        continue
        except Exception as e:
            logging.error(f"Failed to read CSV file {reschedule_csv}: {e}")
            sys.exit(1)

        lines.append("% Lock past weeks\n")
        lines.append(":- past_turno(S, F), not turno(S, F).\n")
        lines.append(":- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).\n")
        lines.append(":- past_turno_festivo(N, F), not turno_festivo(N, F).\n")

    if unavailables:
        for u in unavailables:
            try:
                f, w = u.split(',')
                lines.append(f":- turno({w}, {f}).\n")
            except ValueError:
                logging.error(f"Invalid format for --unavailable: {u}. Expected F,W")
                sys.exit(1)

    if unavailable_intervals:
        for u in unavailable_intervals:
            try:
                f, w1, w2 = u.split(',')
                lines.append(f":- turno(S, {f}), S >= {w1}, S <= {w2}.\n")
            except ValueError:
                logging.error(f"Invalid format for --unavailable-interval: {u}. Expected F,W1,W2")
                sys.exit(1)

    # Festivities facts & choice rule
    if festivities_dict:
        midweek_festivities = []
        for fest_date, fest_name in festivities_dict.items():
            if fest_date.weekday() < 5:  # Monday to Friday
                w_num = get_week_number_for_date(fest_date, fest_date.year)
                midweek_festivities.append((fest_name.lower(), w_num))

        if midweek_festivities:
            lines.append("\n% Mid-week Festivities facts and choice rules\n")
            for name, w in midweek_festivities:
                lines.append(f'festivita("{name}", {w}).\n')

            lines.append('{ turno_festivo(N, F) : farmacia(F) } :- festivita(N, S).\n')

        # Previous year festivity history
        if prev_year_csv:
            past_fest_set = parse_prev_year_csv(prev_year_csv)
            if past_fest_set:
                lines.append("\n% Previous year festivity history\n")
                for name, f_id in past_fest_set:
                    lines.append(f'past_festivita("{name}", {f_id}).\n')

    lines.insert(0, f"settimana({actual_start_week}..{end_week}).\n")

    fd, path = tempfile.mkstemp(suffix=".lp", text=True)
    with os.fdopen(fd, 'w') as f:
        f.writelines(lines)
    return path

def run_external_solver(executable, domain_file, guess_file, constraints_file, opt_file, dynamic_file=None, live=False, time_limit=None):
    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)
    logging.info(f"Running {executable.upper()} solver with files: {', '.join(files)}")
    try:
        process = subprocess.Popen(
            [executable] + files,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=time_limit)
        if process.returncode != 0 and process.returncode is not None:
            logging.error(f"{executable.upper()} execution failed: {stderr}")
            sys.exit(1)
        return stdout, None
    except subprocess.TimeoutExpired:
        logging.warning(f"Time limit of {time_limit}s reached. Terminating {executable.upper()}...")
        process.terminate()
        stdout, _ = process.communicate()
        return stdout, None
    except KeyboardInterrupt:
        logging.warning(f"Execution interrupted by user (Ctrl+C). Terminating {executable.upper()}...")
        process.terminate()
        stdout, _ = process.communicate()
        return stdout, None
    except FileNotFoundError:
        logging.error(f"{executable.upper()} executable not found. Please ensure it is installed and in your PATH.")
        sys.exit(1)

def run_clingo(domain_file, guess_file, constraints_file, opt_file, dynamic_file=None, live=False, time_limit=None, year=2025, on_model_cb=None):
    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)
    logging.info(f"Running Clingo solver via Python API with files: {', '.join(files)}")
    try:
        import clingo
    except ImportError:
        logging.error("The 'clingo' Python module is not installed. Please install it using 'pip install clingo'.")
        sys.exit(1)

    ctl = clingo.Control()
    for f in files:
        ctl.load(f)
    logging.info("Grounding...")
    ctl.ground([("base", [])])

    models = []
    costs = []

    def on_model(m):
        model_str = " ".join(str(sym) for sym in m.symbols(shown=True))
        models.append(model_str)
        if m.cost:
            costs.append(m.cost)

        if on_model_cb:
            on_model_cb(m, model_str, len(models))

    logging.info("Solving...")
    with ctl.solve(on_model=on_model, async_=True) as handle:
        try:
            if time_limit is not None:
                end_time = time.time() + time_limit
                finished = False
                while time.time() < end_time:
                    if handle.wait(1.0):
                        finished = True
                        break
                if not finished:
                    logging.warning(f"Time limit of {time_limit}s reached. Cancelling solver...")
                    handle.cancel()
                    handle.wait()
            else:
                while not handle.wait(1.0):
                    pass
        except KeyboardInterrupt:
            logging.warning("Execution interrupted by user (Ctrl+C). Cancelling solver...")
            handle.cancel()
            handle.wait()

    output = ""
    if models:
        output += models[-1] + "\n"
    if costs:
        final_cost = costs[-1]
        output += f"COST {final_cost[0]}@1\n"

    return output, len(models)
