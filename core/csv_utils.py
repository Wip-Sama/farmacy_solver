import csv
import re
import os
import logging
from collections import defaultdict
from datetime import datetime, timedelta

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

def parse_pharmacy_mapping(map_arg):
    """
    Parses pharmacy mapping string or file into a dictionary {int_id: name_str}.
    Format: '1,MONTORO;2,BUCCARELLI' or '1:MONTORO,2:BUCCARELLI' or file path.
    """
    if not map_arg:
        return {}
    
    mapping = {}
    if isinstance(map_arg, dict):
        return {int(k): str(v) for k, v in map_arg.items()}

    content = str(map_arg)
    if os.path.exists(content):
        try:
            with open(content, mode='r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Failed to read pharmacy mapping file '{map_arg}': {e}")
            return {}

    tokens = re.findall(r'(\d+)[\s:=,\-]+([^\s:=,\-\d][^\s;,\n]*)', content)
    for f_id_str, name_str in tokens:
        mapping[int(f_id_str)] = name_str.strip()
    return mapping

def parse_metadata_line(line: str) -> dict:
    """Parses a '# Metadata: Key=Value | Key=Value' string into a dict."""
    metadata = {}
    if not line or not line.startswith('#'):
        return metadata
    
    body = line.lstrip('#').strip()
    if body.startswith('Metadata:'):
        body = body[len('Metadata:'):].strip()
    
    parts = body.split('|')
    for p in parts:
        if '=' in p:
            k, v = p.split('=', 1)
            metadata[k.strip().lower()] = v.strip()
    return metadata

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

def read_csv_schedule(csv_path: str):
    """
    Reads any generated CSV schedule file and parses:
    - schedule: dict week_int -> set of pharmacy IDs
    - metadata: dict of parsed metadata key-values
    - pharmacy_map: dict int_id -> name_str
    - past_festivities: set of tuples (festivity_name_lower, farmacia_id)
    - raw_rows: list of raw row lists
    """
    schedule = defaultdict(set)
    metadata = {}
    pharmacy_map = {}
    pharmacy_name_to_id = {}
    past_festivities = set()
    raw_rows = []

    if not os.path.exists(csv_path):
        logging.error(f"CSV file not found: {csv_path}")
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header_row = None
        for row in reader:
            if not row:
                continue
            raw_rows.append(row)
            if row[0].startswith('#'):
                meta_parsed = parse_metadata_line(row[0])
                metadata.update(meta_parsed)
                if 'mappings' in meta_parsed and meta_parsed['mappings'] != 'none':
                    m_dict = parse_pharmacy_mapping(meta_parsed['mappings'])
                    pharmacy_map.update(m_dict)
                    for k, v in m_dict.items():
                        pharmacy_name_to_id[v.lower()] = k
                continue
            
            if header_row is None or 'gennaio' in [h.strip().lower() for h in header_row]:
                header_row = row
                for h in header_row:
                    h_clean = h.strip().lower()
                    if h_clean not in ['settimana', 'data', 'data inizio', 'giorno', 'festività', 'festivita', 'farmacie di turno', 'lu-do']:
                        if h_clean.startswith('f') and h_clean[1:].isdigit():
                            pharmacy_map[int(h_clean[1:])] = h.strip()
                            pharmacy_name_to_id[h.strip().lower()] = int(h_clean[1:])
                if 'gennaio' in [h.strip().lower() for h in row]:
                    continue
                continue

            h_lower = [h.strip().lower() for h in header_row]
            fest_col_idx = None
            for fname in ['festività', 'festivita', 'festivities', 'festivity']:
                if fname in h_lower:
                    fest_col_idx = h_lower.index(fname)
                    break
            
            if 'giorno' in h_lower and 'farmacie di turno' in h_lower:
                num_blocks = len(row) // 4
                for b in range(num_blocks):
                    offset = b * 4
                    if offset + 3 < len(row):
                        giorno_str = row[offset].strip()
                        fest_str = row[offset+2].strip()
                        farm_str = row[offset+3].strip()
                        if giorno_str.isdigit() and farm_str:
                            f_ids = extract_pharmacy_ids(farm_str, pharmacy_name_to_id)
                            if fest_str and fest_str != "Festività":
                                for fest_item in fest_str.split('/'):
                                    f_clean = fest_item.strip().lower()
                                    if f_clean:
                                        for fid in f_ids:
                                            past_festivities.add((f_clean, fid))
                continue

            if not row[0].isdigit():
                continue
            
            week_num = int(row[0])
            fest_str = row[fest_col_idx].strip() if fest_col_idx is not None and fest_col_idx < len(row) else ""

            # Identifica dinamicamente tutte le colonne farmacia presenti nell'header
            pharmacy_cols = []
            for idx, col_name in enumerate(h_lower):
                if col_name.startswith('f') and col_name[1:].isdigit():
                    pharmacy_cols.append((int(col_name[1:]), idx))

            has_pharmacy_cols = False
            for f_id, idx in pharmacy_cols:
                if idx < len(row) and str(row[idx]).strip() == "1":
                    schedule[week_num].add(f_id)
                    has_pharmacy_cols = True
                    if fest_str:
                        past_festivities.add((fest_str.lower(), f_id))

            if not has_pharmacy_cols:
                turn_col_idx = None
                for tname in ['farmacie di turno', 'farmacie']:
                    if tname in h_lower:
                        turn_col_idx = h_lower.index(tname)
                        break
                if turn_col_idx is not None and turn_col_idx < len(row):
                    farm_str = row[turn_col_idx].strip()
                    f_ids = extract_pharmacy_ids(farm_str, pharmacy_name_to_id)
                    schedule[week_num].update(f_ids)
                    if fest_str:
                        for fid in f_ids:
                            past_festivities.add((fest_str.lower(), fid))

    return schedule, metadata, pharmacy_map, past_festivities, raw_rows

def generate_csv_report(
    schedule,
    filename,
    run_info=None,
    year=2025,
    festivo_schedule=None,
    festivities_dict=None,
    csv_mode="normal",
    csv_direction="column",
    csv_map_pharmacies=None,
    first_day_of_week=0
):
    """
    Generates a CSV report with customizable mode (normal/compact/tiny/extended),
    direction (column/row), pharmacy name mapping, and first day of week.
    First row contains metadata about run/generation/parsing.
    """
    pharmacy_map = parse_pharmacy_mapping(csv_map_pharmacies)
    fest_dict = festivities_dict or {}

    def get_pharmacy_name(f_id):
        return pharmacy_map.get(f_id, f"F{f_id}")

    # Raccoglie dinamicamente tutti gli ID farmacia assegnati nel calendario corrente
    active_pharmacy_ids = set()
    for f_set in schedule.values():
        active_pharmacy_ids.update(f_set)
    
    # Includiamo anche quelle del mapping (se fornite) nel caso qualcuna abbia 0 turni
    if pharmacy_map:
        active_pharmacy_ids.update(pharmacy_map.keys())
        
    sorted_f_ids = sorted(list(active_pharmacy_ids))
    if not sorted_f_ids:
        sorted_f_ids = list(range(1, 11)) # Fallback di sicurezza estrema

    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            solver_str = run_info.get('solver', 'N/A') if run_info else 'N/A'
            time_str = f"{run_info.get('time', 0):.2f}s" if run_info else 'N/A'
            map_str = ",".join(f"{k}:{v}" for k, v in sorted(pharmacy_map.items())) if pharmacy_map else "none"
            meta_str = f"# Metadata: Year={year} | Solver={solver_str} | Time={time_str} | Mode={csv_mode} | Direction={csv_direction} | FirstDayOfWeek={first_day_of_week} | Mappings={map_str}"
            writer.writerow([meta_str])

            if csv_direction == "row":
                month_names = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
                
                header_row1 = []
                for m_name in month_names:
                    header_row1.extend([m_name, "", "", ""])
                writer.writerow(header_row1)

                header_row2 = []
                for _ in range(12):
                    header_row2.extend(["Giorno", "Lu-Do", "Festività", "Farmacie di Turno"])
                writer.writerow(header_row2)

                month_days = defaultdict(dict)
                for week in sorted(schedule.keys()):
                    monday_str = get_week_date(week, year, first_day_of_week)
                    monday_date = datetime.strptime(monday_str, "%Y-%m-%d").date()
                    for day_idx in range(7):
                        day_date = monday_date + timedelta(days=day_idx)
                        if day_date.year == year:
                            m_idx = day_date.month
                            d_idx = day_date.day
                            dow_str = ["L", "M", "M", "G", "V", "S", "D"][day_date.weekday()]
                            fest_name = fest_dict.get(day_date, "")
                            f_ids = sorted(schedule[week])
                            f_names = "-".join(get_pharmacy_name(f) for f in f_ids)
                            month_days[m_idx][d_idx] = (dow_str, fest_name, f_names)

                for d in range(1, 32):
                    grid_row = []
                    for m in range(1, 13):
                        if d in month_days[m]:
                            dow, fest, f_str = month_days[m][d]
                            grid_row.extend([d, dow, fest, f_str])
                        else:
                            grid_row.extend(["", "", "", ""])
                    writer.writerow(grid_row)

            else:
                if csv_mode == "tiny":
                    header = ['Settimana', 'Data Inizio', 'Festività', 'Farmacie di Turno']
                    writer.writerow(header)
                    for week in sorted(schedule.keys()):
                        monday_str = get_week_date(week, year, first_day_of_week)
                        monday_date = datetime.strptime(monday_str, "%Y-%m-%d").date()
                        week_festivities = []
                        for day_idx in range(7):
                            day_date = monday_date + timedelta(days=day_idx)
                            fn = fest_dict.get(day_date, "")
                            if fn and fn not in week_festivities:
                                week_festivities.append(fn)
                        fest_label = " / ".join(week_festivities)
                        f_names = "-".join(get_pharmacy_name(f) for f in sorted(schedule[week]))
                        writer.writerow([week, monday_str, fest_label, f_names])

                elif csv_mode == "compact":
                    header = ['Settimana', 'Data Inizio', 'Festività'] + [get_pharmacy_name(i) for i in sorted_f_ids]
                    writer.writerow(header)
                    for week in sorted(schedule.keys()):
                        monday_str = get_week_date(week, year, first_day_of_week)
                        monday_date = datetime.strptime(monday_str, "%Y-%m-%d").date()
                        week_festivities = []
                        for day_idx in range(7):
                            day_date = monday_date + timedelta(days=day_idx)
                            fn = fest_dict.get(day_date, "")
                            if fn and fn not in week_festivities:
                                week_festivities.append(fn)
                        fest_label = " / ".join(week_festivities)
                        f_assigned = set(schedule[week])
                        row = [week, monday_str, fest_label]
                        for i in sorted_f_ids:
                            row.append(1 if i in f_assigned else "")
                        writer.writerow(row)

                elif csv_mode == "extended":
                    header = ['Settimana', 'Data', 'Giorno', 'Festività'] + [get_pharmacy_name(i) for i in sorted_f_ids]
                    writer.writerow(header)
                    for week in sorted(schedule.keys()):
                        monday_str = get_week_date(week, year, first_day_of_week)
                        monday_date = datetime.strptime(monday_str, "%Y-%m-%d").date()
                        for day_idx in range(7):
                            day_date = monday_date + timedelta(days=day_idx)
                            if day_date.year == year:
                                dow_str = ["L", "M", "M", "G", "V", "S", "D"][day_date.weekday()]
                                fest_name = fest_dict.get(day_date, "")
                                f_assigned = set(schedule[week])
                                row = [week, day_date.strftime("%Y-%m-%d"), dow_str, fest_name]
                                for i in sorted_f_ids:
                                    row.append(1 if i in f_assigned else "")
                                writer.writerow(row)

                else: # normal mode
                    header = ['Settimana', 'Data', 'Festività'] + [get_pharmacy_name(i) for i in sorted_f_ids]
                    writer.writerow(header)
                    for week in sorted(schedule.keys()):
                        monday_str = get_week_date(week, year, first_day_of_week)
                        monday_date = datetime.strptime(monday_str, "%Y-%m-%d").date()
                        days_details = []
                        for day_idx in range(7):
                            day_date = monday_date + timedelta(days=day_idx)
                            fest_name = fest_dict.get(day_date, "")
                            f_assigned = set(schedule[week])
                            days_details.append((day_date, fest_name, f_assigned))

                        current_group = [days_details[0]]
                        groups = []
                        for d_info in days_details[1:]:
                            prev = current_group[-1]
                            if d_info[1] == prev[1] and d_info[2] == prev[2]:
                                current_group.append(d_info)
                            else:
                                groups.append(current_group)
                                current_group = [d_info]
                        if current_group:
                            groups.append(current_group)

                        for group in groups:
                            start_date_str = group[0][0].strftime("%Y-%m-%d")
                            fest_label = group[0][1]
                            f_assigned = group[0][2]
                            row = [week, start_date_str, fest_label]
                            for i in sorted_f_ids:
                                row.append(1 if i in f_assigned else "")
                            writer.writerow(row)

        print(f"Report CSV generato con successo in: {filename}")
    except Exception as e:
        print(f"Errore durante la generazione del report CSV: {e}")

def get_week_date(week_number, year=2025, first_day_of_week=0):
    from core.runner_core import get_week_start_date
    d_obj = get_week_start_date(week_number, year, first_day_of_week)
    return d_obj.strftime("%Y-%m-%d")