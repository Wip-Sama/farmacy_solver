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
from core.csv_utils import read_csv_schedule

def parse_week_param(val: int | str | None, year: int = 2025, first_day_of_week: int | str = 0) -> int | None:
    """
    Parses a week parameter that can be an integer, numeric string, or 'now'.
    Returns an integer week number or None.
    """
    if val is None:
        return None
    
    val_str = str(val).strip().lower()
    if not val_str:
        return None

    if val_str == 'now':
        today = date.today()
        if today.year == year:
            target_date = today
        else:
            try:
                target_date = date(year, today.month, today.day)
            except ValueError:
                target_date = date(year, today.month, 28)
        
        week_num = get_week_number_for_date(target_date, year, first_day_of_week)
        logging.info(f"Resolved 'now' ({target_date.isoformat()}) for year {year} to week {week_num}.")
        return week_num

    try:
        return int(val_str)
    except ValueError:
        raise ValueError(f"Invalid week specification '{val}'. Expected an integer or 'now'.")

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

def parse_first_day_of_week(val) -> int:
    """Normalizes day name or int into 0..6 (0=Monday, 5=Saturday, 6=Sunday)."""
    if val is None:
        return 0
    if isinstance(val, int) and 0 <= val <= 6:
        return val
    s = str(val).strip().lower()
    mapping = {
        'monday': 0, 'mon': 0, 'lunedi': 0, 'lunedì': 0, '0': 0,
        'tuesday': 1, 'tue': 1, 'martedi': 1, 'martedì': 1, '1': 1,
        'wednesday': 2, 'wed': 2, 'mercoledi': 2, 'mercoledì': 2, '2': 2,
        'thursday': 3, 'thu': 3, 'giovedi': 3, 'giovedì': 3, '3': 3,
        'friday': 4, 'fri': 4, 'venerdi': 4, 'veneredì': 4, '4': 4,
        'saturday': 5, 'sat': 5, 'sabato': 5, '5': 5,
        'sunday': 6, 'sun': 6, 'domenica': 6, '6': 6,
    }
    return mapping.get(s, 0)

def get_week_start_date(week_number: int, year: int = 2025, first_day_of_week: int | str = 0) -> date:
    """Calculates the start date for a given week number in a year given first_day_of_week."""
    start_dow = parse_first_day_of_week(first_day_of_week)
    jan1 = date(year, 1, 1)
    if start_dow == 0:
        if jan1.weekday() != 0:
            jan1 += timedelta(days=(7 - jan1.weekday()))
        return jan1 + timedelta(weeks=week_number - 1)
    
    if jan1.weekday() == start_dow:
        return jan1 + timedelta(weeks=week_number - 1)
    else:
        diff = (start_dow - jan1.weekday()) % 7
        first_full_start = jan1 + timedelta(days=diff)
        if week_number == 1:
            return jan1
        else:
            return first_full_start + timedelta(weeks=week_number - 2)

def get_week_monday(week_number: int, year: int = 2025) -> date:
    """Calculates the Monday date for a given week number in a year."""
    return get_week_start_date(week_number, year, 0)

def get_week_number_for_date(d: date, year: int = 2025, first_day_of_week: int | str = 0) -> int:
    """Finds which schedule week number a date belongs to."""
    start_dow = parse_first_day_of_week(first_day_of_week)
    jan1 = date(year, 1, 1)
    if start_dow == 0:
        first_monday = get_week_start_date(1, year, 0)
        delta_days = (d - first_monday).days
        if delta_days < 0:
            return 1
        return (delta_days // 7) + 1

    if jan1.weekday() == start_dow:
        delta_days = (d - jan1).days
        if delta_days < 0:
            return 1
        return (delta_days // 7) + 1
    else:
        diff = (start_dow - jan1.weekday()) % 7
        first_full_start = jan1 + timedelta(days=diff)
        if d < first_full_start:
            return 1
        else:
            return 2 + ((d - first_full_start).days // 7)

def extract_pharmacy_ids(farmacie_str, pharmacy_name_to_id=None):
    """Extracts integer pharmacy IDs from strings like '1-2', 'F1-F2', or 'BUCCARELLI-SANMICHELE'."""
    ids = set()
    if not farmacie_str:
        return ids
    tokens = re.split(r'[-/,\s]+', farmacie_str.strip())
    for t in tokens:
        if not t:
            continue
        if t.isdigit():
            ids.add(int(t))
        elif t.lower().startswith('f') and t[1:].isdigit():
            ids.add(int(t[1:]))
        elif pharmacy_name_to_id and t.lower() in pharmacy_name_to_id:
            ids.add(pharmacy_name_to_id[t.lower()])
    return ids

def parse_prev_year_csv(csv_path: str) -> set[tuple[str, int]]:
    """
    Parses a previous year CSV to extract past festivity assignments.
    Returns a set of tuples: (festivity_name_lower, farmacia_id).
    Supports metadata rows, vertical (normal/compact/tiny/extended) and horizontal (row direction) CSVs.
    """
    _, _, _, past_festivities, _ = read_csv_schedule(csv_path)
    return past_festivities

def get_summer_weeks(year: int, first_day_of_week: int | str = 0) -> tuple[int, int]:
    """Calculates the dynamic summer week range (start_week, end_week) for June 15 - Sept 15."""
    sum_start_date = date(year, 6, 15)
    sum_end_date = date(year, 9, 15)
    sum_start_w = get_week_number_for_date(sum_start_date, year, first_day_of_week)
    sum_end_w = get_week_number_for_date(sum_end_date, year, first_day_of_week)
    return sum_start_w, sum_end_w

def parse_fw_constraints(fw_list: list | None) -> list[tuple[int, int]]:
    """Helper function to parse lists of Farmacia,Settimana constraints, supporting inline strings and text files."""
    parsed = []
    if fw_list:
        for item in fw_list:
            if os.path.isfile(item) or item.endswith('.txt') or item.endswith('.csv'):
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        item = f.read().strip()
                except Exception as e:
                    logging.warning(f"Could not read file {item}: {e}")
            
            for element in item.split(';'):
                element = element.strip()
                if element:
                    parts = element.split(',')
                    if len(parts) >= 2:
                        try:
                            parsed.append((int(parts[0].strip()), int(parts[1].strip())))
                        except ValueError:
                            logging.error(f"Valori non validi nel vincolo '{element}'. Devono essere ID numerici.")
                            sys.exit(1)
                    else:
                        logging.error(f"Formato incompleto nel vincolo '{element}'. Atteso formato 'ID,Settimana'.")
                        sys.exit(1)
    return parsed

def generate_dynamic_constraints(
    reschedule_csv: str | None,
    reschedule_from: int | None,
    unavailables: list | None,
    unavailable_intervals: list | None,
    start_week: int,
    end_week: int,
    festivities_dict: dict | None = None,
    prev_year_csv: str | None = None,
    first_day_of_week: int | str = 0,
    year: int = 2025,
    pharmacies: str | None = None,
    force_open: list | None = None,
    force_closed: list | None = None,
    pref_open: list | None = None,
    pref_closed: list | None = None
) -> str:
    """
    Generates dynamic ASP rules in a temporary file for week limits, rescheduling, unavailabilities, festivities, and dynamic summer period.
    Directly handles custom pharmacies injection and strong/weak constraints.
    """
    lines = []
    actual_start_week = start_week

    # DEBUG
    logging.info(f"DEBUG RICEVUTO - pharmacies grezze: {repr(pharmacies)}")
    #pharmacies="" # IMPORTANTE! DA TOGLIERE, PROVA MOMENTANEA

    # Apply 10 default pharmacies if none provided
    if not pharmacies:
        pharmacies = ";".join([
            f"{i},{'centro' if i <= 6 else 'marina'}" 
            for i in range(1, 11)
        ])

    if pharmacies and (os.path.isfile(pharmacies) or pharmacies.endswith(".txt") or pharmacies.endswith(".csv")):
        try:
            with open(pharmacies, "r", encoding="utf-8") as f:
                pharmacies = f.read().strip()
        except Exception as e:
            logging.error(f"Failed to read pharmacies file: {e}")
            sys.exit(1)

    parsed_pharmacies = []
    if pharmacies:
        for p in pharmacies.split(';'):
            p = p.strip()
            if p:
                parts = [x.strip() for x in p.split(',')]
                if len(parts) >= 2:
                    try:
                        p_id = int(parts[0])
                        p_zona = parts[1].lower() if parts[1].lower() in ['centro', 'marina'] else 'centro'
                        parsed_pharmacies.append((p_id, p_zona))
                    except ValueError:
                        logging.error(f"ID farmacia non valido: '{parts[0]}'. Deve essere un numero intero.")
                        sys.exit(1)
                elif len(parts) == 1:
                    try:
                        p_id = int(parts[0])
                        parsed_pharmacies.append((p_id, "centro"))
                    except ValueError:
                        logging.error(f"ID farmacia non valido: '{parts[0]}'. Deve essere un numero intero.")
                        sys.exit(1)
                else:
                    logging.error(f"Formato farmacia non riconosciuto in '{p}'.")
                    sys.exit(1)

    # Scrittura dei fatti ASP nel file temporaneo per farmacie e zone
    if parsed_pharmacies:
        lines.append("% Fatti generati dinamicamente (Farmacie e Zone)\n")
        for p_id, p_zona in parsed_pharmacies:
            lines.append(f"farmacia({p_id}).\n")
            lines.append(f"zona({p_id},{p_zona}).\n")
        lines.append("\n")

    # Inserimento dei vincoli logici utente per forzature e preferenze
    lines.append("% Vincoli logici personalizzati (Strong/Weak Constraints)\n")
    for f, w in parse_fw_constraints(force_open):
        lines.append(f":- not turno({w}, {f}).\n")
    for f, w in parse_fw_constraints(force_closed):
        lines.append(f":- turno({w}, {f}).\n")
    for f, w in parse_fw_constraints(pref_open):
        lines.append(f":~ not turno({w}, {f}). [10@0, {f}, {w}]\n")
    for f, w in parse_fw_constraints(pref_closed):
        lines.append(f":~ turno({w}, {f}). [10@0, {f}, {w}]\n")
    lines.append("\n")


    # Dynamic summer facts for June 15 - Sept 15
    sum_start_w, sum_end_w = get_summer_weeks(year, first_day_of_week)
    lines.append(f"% Dynamic summer period facts for {year} (June 15 - Sept 15)\n")
    lines.append(f"estate({sum_start_w}..{sum_end_w}).\n")
    lines.append("inverno(W) :- settimana(W), not estate(W).\n\n")

    if reschedule_csv and reschedule_from:
        actual_start_week = 1
        lines.append(f"reschedule_from({reschedule_from}).\n")
        lines.append("past_week(S) :- reschedule_from(START), settimana(S), S < START.\n\n")
        try:
            res_sched, _, _, _, _ = read_csv_schedule(reschedule_csv)
            for week, f_set in res_sched.items():
                if week < reschedule_from:
                    for f_id in f_set:
                        lines.append(f"past_turno({week}, {f_id}).\n")
        except Exception as e:
            logging.error(f"Failed to read CSV file {reschedule_csv}: {e}")
            sys.exit(1)

        lines.append("\n% Lock past weeks\n")
        lines.append(":- past_turno(S, F), not turno(S, F).\n")
        lines.append(":- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).\n")

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
                w_num = get_week_number_for_date(fest_date, fest_date.year, first_day_of_week)
                midweek_festivities.append((fest_name.lower(), w_num))

        if midweek_festivities:
            lines.append("\n% Mid-week Festivities facts\n")
            for name, w in midweek_festivities:
                lines.append(f'festivita("{name}", {w}).\n')

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
    
    # DEBUG ------------------------------------
    with open(path, 'r', encoding='utf-8') as dbg:
        logging.info(f"--- CONTENUTO FILE DINAMICO ({path}) ---\n" + dbg.read())

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

    ctl = clingo.Control(
        arguments=["--parallel-mode=4", "--opt-strat=usc"]
    )
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