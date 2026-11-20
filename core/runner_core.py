import logging
import os
import subprocess
import tempfile
import threading
import time
from datetime import date, datetime, timedelta

try:
    import clingo
except ImportError:
    clingo = None

from core.csv_utils import extract_pharmacy_ids, read_csv_schedule
from core.date_utils import (
    get_easter_date,
    get_italian_holidays,
    get_summer_weeks,
    get_week_monday,
    get_week_number_for_date,
    get_week_start_date,
    parse_first_day_of_week,
)

__all__ = [
    "extract_pharmacy_ids",
    "generate_dynamic_constraints",
    "get_easter_date",
    "get_italian_holidays",
    "get_summer_weeks",
    "get_week_monday",
    "get_week_number_for_date",
    "get_week_start_date",
    "parse_festivities",
    "parse_first_day_of_week",
    "parse_fw_constraints",
    "parse_prev_year_csv",
    "parse_week_param",
    "run_clingo",
    "run_external_solver",
]


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

    if val_str == "now":
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
    except ValueError as exc:
        raise ValueError(f"Invalid week specification '{val}'. Expected an integer or 'now'.") from exc


def parse_festivities(festivities_args: list | None, auto_festivities: bool, year: int) -> dict[date, str]:
    """
    Parses --festivities and --auto-festivities.
    Returns a dict mapping date -> holiday_name.
    """
    festivities_dict: dict[date, str] = {}
    if auto_festivities:
        festivities_dict.update(get_italian_holidays(year))

    if festivities_args:
        for item in festivities_args:
            parts = [p.strip() for p in item.split(",")]
            if len(parts) == 2:
                name, start_str = parts
                finish_str = start_str
            elif len(parts) == 3:
                name, start_str, finish_str = parts
            else:
                raise ValueError(
                    f"Invalid format for --festivities: '{item}'. Expected 'name,start_date,finish_date' or 'name,date'"
                )

            try:
                start_d = datetime.strptime(start_str, "%Y-%m-%d").date()
                finish_d = datetime.strptime(finish_str, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError(f"Invalid date format in --festivities '{item}': {exc}. Expected YYYY-MM-DD") from exc

            curr = start_d
            while curr <= finish_d:
                festivities_dict[curr] = name
                curr += timedelta(days=1)

    return festivities_dict


def parse_prev_year_csv(csv_path: str) -> set[tuple[str, int]]:
    """
    Parses a previous year CSV to extract past festivity assignments.
    Returns a set of tuples: (festivity_name_lower, farmacia_id).
    """
    _, _, _, past_festivities, _ = read_csv_schedule(csv_path)
    return past_festivities


def parse_fw_constraints(fw_list: list | None) -> list[tuple[int, int]]:
    """Parses lists of Farmacia,Settimana constraints, supporting inline strings and text files."""
    parsed: list[tuple[int, int]] = []
    if not fw_list:
        return parsed

    for item in fw_list:
        if os.path.isfile(item) or item.endswith((".txt", ".csv")):
            try:
                with open(item, "r", encoding="utf-8") as f:
                    item = f.read().strip()
            except Exception as e:
                logging.warning(f"Could not read file {item}: {e}")

        for element in item.split(";"):
            element = element.strip()
            if not element:
                continue
            parts = element.split(",")
            if len(parts) >= 2:
                try:
                    parsed.append((int(parts[0].strip()), int(parts[1].strip())))
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid values in constraint '{element}'. Numeric IDs expected."
                    ) from exc
            else:
                raise ValueError(
                    f"Incomplete format in constraint '{element}'. Expected 'ID,Week'."
                )
    return parsed


def _parse_pharmacies_spec(pharmacies: str | None) -> list[tuple[int, str]]:
    """Parses pharmacy ID and zone tuples from inline spec or file."""
    spec = pharmacies
    if not spec:
        spec = ";".join(
            f"{i},{'centro' if i <= 6 else 'marina'}"
            for i in range(1, 11)
        )
    elif os.path.isfile(spec) or spec.endswith((".txt", ".csv")):
        try:
            with open(spec, "r", encoding="utf-8") as f:
                spec = f.read().strip()
        except Exception as exc:
            raise RuntimeError(f"Failed to read pharmacies file '{spec}': {exc}") from exc

    parsed_pharmacies: list[tuple[int, str]] = []
    for p in spec.split(";"):
        p = p.strip()
        if not p:
            continue
        parts = [x.strip() for x in p.split(",")]
        try:
            p_id = int(parts[0])
        except ValueError as exc:
            raise ValueError(f"Invalid pharmacy ID '{parts[0]}'. Expected an integer.") from exc

        p_zona = "centro"
        if len(parts) >= 2 and parts[1].lower() in ["centro", "marina"]:
            p_zona = parts[1].lower()
        parsed_pharmacies.append((p_id, p_zona))
    return parsed_pharmacies


def generate_dynamic_constraints(
    reschedule_csv: str | None = None,
    reschedule_from: int | None = None,
    unavailables: list | None = None,
    unavailable_intervals: list | None = None,
    start_week: int = 1,
    end_week: int = 52,
    festivities_dict: dict | None = None,
    prev_year_csv: str | None = None,
    first_day_of_week: int | str = 0,
    year: int = 2025,
    pharmacies: str | None = None,
    force_open: list | None = None,
    force_closed: list | None = None,
    pref_open: list | None = None,
    pref_closed: list | None = None,
) -> str:
    """
    Generates dynamic ASP rules in a temporary file for week limits, rescheduling,
    unavailabilities, festivities, and dynamic summer period.
    """
    lines: list[str] = []
    actual_start_week = start_week

    parsed_pharmacies = _parse_pharmacies_spec(pharmacies)
    if parsed_pharmacies:
        lines.append("% Dynamic pharmacy and zone facts\n")
        for p_id, p_zona in parsed_pharmacies:
            lines.append(f"farmacia({p_id}).\n")
            lines.append(f"zona({p_id},{p_zona}).\n")
        lines.append("\n")

    lines.append("% Custom logical constraints (Strong/Weak Constraints)\n")
    for f_id, w_num in parse_fw_constraints(force_open):
        lines.append(f":- not turno({w_num}, {f_id}).\n")

    combined_closed = list(force_closed or []) + list(unavailables or [])
    for f_id, w_num in parse_fw_constraints(combined_closed):
        lines.append(f":- turno({w_num}, {f_id}).\n")

    if unavailable_intervals:
        for interval in unavailable_intervals:
            parts = [p.strip() for p in str(interval).split(",")]
            if len(parts) == 3:
                f_id, w_start, w_end = int(parts[0]), int(parts[1]), int(parts[2])
                for w_num in range(w_start, w_end + 1):
                    lines.append(f":- turno({w_num}, {f_id}).\n")

    # High-priority level (@2) for user preferences so they override shift balance
    for f_id, w_num in parse_fw_constraints(pref_open):
        lines.append(f":~ not turno({w_num}, {f_id}). [10@2, {f_id}, {w_num}]\n")
    for f_id, w_num in parse_fw_constraints(pref_closed):
        lines.append(f":~ turno({w_num}, {f_id}). [10@2, {f_id}, {w_num}]\n")
    lines.append("\n")

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
        except Exception as exc:
            raise RuntimeError(f"Failed to read CSV file '{reschedule_csv}': {exc}") from exc

        lines.append("\n% Lock past weeks\n")
        lines.append(":- past_turno(S, F), not turno(S, F).\n")
        lines.append(":- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).\n")

    if festivities_dict:
        midweek_festivities = []
        for fest_date, fest_name in festivities_dict.items():
            if fest_date.weekday() < 5:
                w_num = get_week_number_for_date(fest_date, fest_date.year, first_day_of_week)
                midweek_festivities.append((fest_name.lower(), w_num))

        if midweek_festivities:
            lines.append("\n% Mid-week Festivities facts\n")
            for name, w_num in midweek_festivities:
                lines.append(f'festivita("{name}", {w_num}).\n')

    if prev_year_csv:
        past_fest_set = parse_prev_year_csv(prev_year_csv)
        if past_fest_set:
            lines.append("\n% Previous year festivity history\n")
            for name, f_id in past_fest_set:
                lines.append(f'past_festivita("{name}", {f_id}).\n')

    lines.insert(0, f"settimana({actual_start_week}..{end_week}).\n")

    fd, path = tempfile.mkstemp(suffix=".lp", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.writelines(lines)

    logging.debug(f"Generated dynamic ASP constraints file at {path}")
    return path


def run_external_solver(
    executable,
    domain_file,
    guess_file,
    constraints_file,
    opt_file,
    dynamic_file=None,
    live=False,
    time_limit=None,
):
    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)
    logging.info(f"Running {executable.upper()} solver with files: {', '.join(files)}")
    try:
        process = subprocess.Popen(
            [executable] + files,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=time_limit)
        if process.returncode != 0 and process.returncode is not None:
            raise RuntimeError(f"{executable.upper()} execution failed: {stderr}")
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
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"{executable.upper()} executable not found. Please ensure it is installed and in your PATH."
        ) from exc


def run_clingo(
    domain_file,
    guess_file,
    constraints_file,
    opt_file,
    dynamic_file=None,
    live=False,
    time_limit=None,
    year=2025,
    on_model_cb=None,
    cancel_event: threading.Event | None = None,
):
    if clingo is None:
        raise RuntimeError("The 'clingo' Python module is not installed. Please install it using 'pip install clingo'.")

    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)
    logging.info(f"Running Clingo solver via Python API with files: {', '.join(files)}")

    ctl = clingo.Control(arguments=["--parallel-mode=4", "--opt-strat=usc"])
    for f in files:
        ctl.load(f)
    logging.info("Grounding...")
    ctl.ground([("base", [])])

    models: list[str] = []
    costs: list[list[int]] = []

    def on_model(m):
        model_str = " ".join(str(sym) for sym in m.symbols(shown=True))
        models.append(model_str)
        if m.cost:
            costs.append(m.cost)

        if on_model_cb:
            on_model_cb(m, model_str, len(models))

    logging.info("Solving...")
    cancelled = False
    with ctl.solve(on_model=on_model, async_=True) as handle:
        try:
            end_time = (time.time() + time_limit) if time_limit is not None else None
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    logging.info("Cancellation requested; stopping Clingo solver...")
                    cancelled = True
                    handle.cancel()
                    handle.wait()
                    break
                if end_time is not None and time.time() >= end_time:
                    logging.warning(f"Time limit of {time_limit}s reached. Cancelling solver...")
                    handle.cancel()
                    handle.wait()
                    break
                if handle.wait(0.25):
                    break
        except KeyboardInterrupt:
            logging.warning("Execution interrupted by user (Ctrl+C). Cancelling solver...")
            handle.cancel()
            handle.wait()

    if cancelled:
        return "", 0

    output = ""
    if models:
        output += models[-1] + "\n"
    if costs:
        final_cost = costs[-1]
        output += f"COST {final_cost[0]}@1\n"

    return output, len(models)
