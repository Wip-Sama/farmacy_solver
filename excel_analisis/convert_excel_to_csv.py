import os
import sys
import csv
import pandas as pd
import datetime
from collections import defaultdict

# 1. Pharmacy Mapping dictionary based on mapping_farmacie.jpg
MAPPING_TEXT = """1,MONTORO
2,BUCCARELLI
3,CENTRALE
4,DE PINO
5,DAVID
6,SAN MICHELE
7,MARCELLINI
8,PHARMADUO
9,IORFIDA
10,SAN LEONARDO"""

NAME_TO_ID = {
    'montoro': 1,
    'buccarelli': 2,
    'centrale': 3,
    'de pino': 4,
    'depino': 4,
    'david': 5,
    'san michele': 6,
    'sanmichele': 6,
    'marcellini': 7,
    'pharmaduo': 8,
    'iorfida': 9,
    'iofida': 9,
    'san leonardo': 10,
    'sanleonardo': 10,
    'farmacia a': 1,
    'farmacia b': 2,
    'farmacia c': 3,
    'farmacia d': 4,
    'farmacia e': 5,
    'farmacia f': 6,
    'farmacia g': 7,
    'farmacia h': 8,
    'farmacia i': 9,
    'farmacia j': 10,
}

ID_TO_NAME = {
    1: "MONTORO",
    2: "BUCCARELLI",
    3: "CENTRALE",
    4: "DE PINO",
    5: "DAVID",
    6: "SAN MICHELE",
    7: "MARCELLINI",
    8: "PHARMADUO",
    9: "IORFIDA",
    10: "SAN LEONARDO"
}

def parse_pharmacy_string(farm_str):
    ids = set()
    if not farm_str or pd.isna(farm_str):
        return ids
    
    # Split by '-', ',', '/'
    tokens = str(farm_str).replace('/', '-').replace(',', '-').split('-')
    for t in tokens:
        clean = t.strip().lower()
        if clean in NAME_TO_ID:
            ids.add(NAME_TO_ID[clean])
    return ids

def convert_2025_excel(excel_path, out_csv_path):
    df = pd.read_excel(excel_path)
    rows_out = []

    meta_row = ["# Metadata: Year=2025 | Solver=excel_import | Time=0.00s | Mode=normal | Direction=column | Mappings=1:MONTORO,2:BUCCARELLI,3:CENTRALE,4:DE PINO,5:DAVID,6:SAN MICHELE,7:MARCELLINI,8:PHARMADUO,9:IORFIDA,10:SAN LEONARDO"]
    rows_out.append(meta_row)

    header = ['Settimana', 'Data', 'Festività'] + [f"F{i}" for i in range(1, 11)]
    rows_out.append(header)

    for idx, row in df.iterrows():
        week_num = idx + 1
        date_str = str(row['Settimana Inizio']).split()[0] if pd.notna(row['Settimana Inizio']) else ""
        fest_name = str(row['Festività nella settimana']).strip() if pd.notna(row['Festività nella settimana']) else ""
        if fest_name.lower() == 'nan':
            fest_name = ""

        f1 = str(row['Farmacia di Turno 1']).strip() if pd.notna(row['Farmacia di Turno 1']) else ""
        f2 = str(row['Farmacia di Turno 2']).strip() if pd.notna(row['Farmacia di Turno 2']) else ""

        f_ids = set()
        f_ids.update(parse_pharmacy_string(f1))
        f_ids.update(parse_pharmacy_string(f2))

        row_data = [week_num, date_str, fest_name]
        for i in range(1, 11):
            row_data.append(1 if i in f_ids else "")
        rows_out.append(row_data)

    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)
    with open(out_csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows_out)
    print(f"Successfully created: {out_csv_path}")

def convert_2026_excel(excel_path, out_csv_path):
    df = pd.read_excel(excel_path)
    
    months_col = [
        ('Gennaio', 1, 1, 2),
        ('Febbraio', 2, 3, 4),
        ('Marzo', 3, 5, 6),
        ('Aprile', 4, 7, 8),
        ('Maggio', 5, 9, 10),
        ('Giugno', 6, 11, 12),
        ('Luglio', 7, 15, 16),
        ('Agosto', 8, 17, 18),
        ('Settembre', 9, 19, 20),
        ('Ottobre', 10, 21, 22),
        ('Novembre', 11, 23, 24),
        ('Dicembre', 12, 25, 26),
    ]

    # Map Italian national holidays in 2026
    italian_holidays_2026 = {
        datetime.date(2026, 1, 1): "Capodanno",
        datetime.date(2026, 1, 6): "Epifania",
        datetime.date(2026, 4, 5): "Pasqua",
        datetime.date(2026, 4, 6): "Pasquetta",
        datetime.date(2026, 4, 25): "Liberazione",
        datetime.date(2026, 5, 1): "Festa del Lavoro",
        datetime.date(2026, 6, 2): "Festa della Repubblica",
        datetime.date(2026, 8, 15): "Ferragosto",
        datetime.date(2026, 11, 1): "Ognissanti",
        datetime.date(2026, 12, 8): "Immacolata",
        datetime.date(2026, 12, 25): "Natale",
        datetime.date(2026, 12, 26): "Santo Stefano",
    }

    # Aggregate weekly assignments using Saturday week start (first Saturday of 2026 is Jan 3)
    first_sat = datetime.date(2026, 1, 3)
    week_shifts = defaultdict(set)
    daily_shifts = {}

    for m_name, m_num, dow_col, farm_col in months_col:
        for day in range(1, 32):
            try:
                d = datetime.date(2026, m_num, day)
                row_idx = day
                if row_idx < len(df):
                    val = df.iloc[row_idx, farm_col]
                    if pd.notna(val):
                        f_ids = parse_pharmacy_string(val)
                        if f_ids:
                            daily_shifts[d] = f_ids
                            if d < first_sat:
                                w_num = 1
                            else:
                                w_num = 2 + ((d - first_sat).days // 7)
                            week_shifts[w_num].update(f_ids)
            except ValueError:
                pass

    rows_out = []
    meta_row = ["# Metadata: Year=2026 | Solver=excel_import | Time=0.00s | Mode=normal | Direction=column | FirstDayOfWeek=saturday | Mappings=1:MONTORO,2:BUCCARELLI,3:CENTRALE,4:DE PINO,5:DAVID,6:SAN MICHELE,7:MARCELLINI,8:PHARMADUO,9:IORFIDA,10:SAN LEONARDO"]
    rows_out.append(meta_row)

    header = ['Settimana', 'Data', 'Festività'] + [f"F{i}" for i in range(1, 11)]
    rows_out.append(header)

    # Output weekly schedule
    sorted_weeks = sorted(list(week_shifts.keys()))
    for w in sorted_weeks:
        if w == 1:
            week_start_date = datetime.date(2026, 1, 1)
        else:
            week_start_date = first_sat + datetime.timedelta(weeks=w-2)
        
        # Check if week contains holidays
        week_fest = []
        for d_offset in range(7):
            d_curr = week_start_date + datetime.timedelta(days=d_offset)
            if d_curr in italian_holidays_2026:
                week_fest.append(italian_holidays_2026[d_curr])
        
        fest_str = " / ".join(week_fest)
        f_assigned = week_shifts[w]

        row_data = [w, week_start_date.strftime("%Y-%m-%d"), fest_str]
        for i in range(1, 11):
            row_data.append(1 if i in f_assigned else "")
        rows_out.append(row_data)

    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)
    with open(out_csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows_out)
    print(f"Successfully created: {out_csv_path}")

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # 1. Write mapping.txt
    mapping_path1 = os.path.join(root_dir, 'mapping.txt')
    mapping_path2 = os.path.join(root_dir, 'excel_analisis', 'mapping.txt')
    with open(mapping_path1, 'w', encoding='utf-8') as f:
        f.write(MAPPING_TEXT + '\n')
    with open(mapping_path2, 'w', encoding='utf-8') as f:
        f.write(MAPPING_TEXT + '\n')
    print(f"Successfully created: {mapping_path1} and {mapping_path2}")

    # 2. Convert 2025.xlsx
    excel_2025 = os.path.join(root_dir, 'excel_analisis', '2025.xlsx')
    csv_2025_root = os.path.join(root_dir, 'schedule_2025.csv')
    csv_2025_schedules = os.path.join(root_dir, 'schedules', 'schedule_2025.csv')
    csv_2025_excel = os.path.join(root_dir, 'excel_analisis', 'schedule_2025.csv')
    
    convert_2025_excel(excel_2025, csv_2025_root)
    convert_2025_excel(excel_2025, csv_2025_schedules)
    convert_2025_excel(excel_2025, csv_2025_excel)

    # 3. Convert 2026.xlsx
    excel_2026 = os.path.join(root_dir, 'excel_analisis', '2026.xlsx')
    csv_2026_root = os.path.join(root_dir, 'schedule_2026.csv')
    csv_2026_schedules = os.path.join(root_dir, 'schedules', 'schedule_2026.csv')
    csv_2026_excel = os.path.join(root_dir, 'excel_analisis', 'schedule_2026.csv')

    convert_2026_excel(excel_2026, csv_2026_root)
    convert_2026_excel(excel_2026, csv_2026_schedules)
    convert_2026_excel(excel_2026, csv_2026_excel)

if __name__ == "__main__":
    main()
