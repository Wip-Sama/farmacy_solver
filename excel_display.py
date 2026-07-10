import sys
import os
import argparse
import pandas as pd
import re
from collections import defaultdict

def parse_arguments():
    """Gestisce gli argomenti passati da riga di comando (argv). Funziona SOLO con file."""
    parser = argparse.ArgumentParser(
        description="Analizzatore di file Excel/CSV per la turnazione delle farmacie.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        'input_file', 
        type=str,
        help="Il percorso del file Excel (.xlsx) o CSV (.csv) da analizzare."
    )
    
    return parser.parse_args()


def load_and_parse_excel(file_path):
    """Legge il file Excel/CSV e crea il dizionario della turnazione."""
    if not os.path.exists(file_path):
        print(f"Errore: Il file '{file_path}' non esiste.")
        sys.exit(1)

    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Errore durante l'apertura del file: {e}")
        sys.exit(1)

    schedule = defaultdict(list)
    week_labels = {}
    
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    week_col = next((col for col in df.columns if 'settimana' in col or 'week' in col), None)
    
    if not week_col:
        print("Errore: Non riesco a trovare una colonna chiamata 'Settimana' nel file Excel.")
        print("Colonne trovate:", list(df.columns))
        sys.exit(1)

    letter_to_id = {chr(65+i): i+1 for i in range(10)} # A=1, B=2, ..., J=10
    week_counter = 1

    for index, row in df.iterrows():
        try:
            week_val = str(row[week_col]).strip()
            if week_val.lower() == 'nan' or not week_val:
                continue
            
            week_label = None
            # Check for date formats like "2025-01-06"
            if re.match(r'\d{4}-\d{2}-\d{2}', week_val):
                week = week_counter
                week_label = week_val.split()[0]
            else:
                week_match = re.search(r'\d+', week_val)
                if week_match:
                    parsed_num = int(week_match.group())
                    if parsed_num > 1000:
                        week = week_counter
                        week_label = week_val.split()[0]
                    else:
                        week = parsed_num
                else:
                    week = week_counter
            
            found_any = False
            for col in df.columns:
                if col != week_col:
                    cell_val = str(row[col])
                    
                    # Cerchiamo "Farmacia X"
                    letter_match = re.findall(r'Farmacia\s+([A-J])', cell_val, re.IGNORECASE)
                    if letter_match:
                        for letter in letter_match:
                            f_id = letter_to_id[letter.upper()]
                            if f_id not in schedule[week]:
                                schedule[week].append(f_id)
                                found_any = True
                    else:
                        # Fallback: cerchiamo numeri 1-10
                        farmacie_trovate = re.findall(r'\b([1-9]|10)\b', cell_val)
                        for f in farmacie_trovate:
                            f_id = int(f)
                            if f_id not in schedule[week]:
                                schedule[week].append(f_id)
                                found_any = True
                                
            if found_any:
                if week_label:
                    week_labels[week] = week_label
                week_counter += 1
                
        except Exception as e:
            continue

    return schedule, week_labels


def get_zona(f_id):
    """Restituisce la zona in base all'ID della farmacia (1-6 Centro, 7-10 Marina)."""
    return "Centro" if 1 <= f_id <= 6 else "Marina"


def print_weekly_schedule(schedule, week_labels=None):
    if week_labels is None:
        week_labels = {}
    """Stampa la tabella del calendario settimanale."""
    print("-" * 75)
    print(f"\n{'Settimana':<22} | {'Farmacie di Turno'}")
    print("-" * 75)

    for week in sorted(schedule.keys()):
        farmacie = schedule[week]
        formatted_farmacie = [f"F{f} ({get_zona(f)})" for f in sorted(farmacie)]
        
        if week in week_labels:
            week_display = f"Wk {week:<2} ({week_labels[week]})"
        else:
            week_display = f"Wk {week:<2}"
            
        print(f"{week_display:<22} | {', '.join(formatted_farmacie)}")
    print("-" * 75)


def print_shift_statistics(schedule):
    """Calcola e stampa il totale dei turni assegnati per ogni farmacia."""
    print(f"{'Farmacia':<10} | {'Turni Assegnati'}")
    print("-" * 50)
    
    total_shifts_counted = 0
    
    for farmacia in range(1, 11): 
        count = sum(farmacia in farmacie for farmacie in schedule.values())
        total_shifts_counted += count
        print(f"F{farmacia:<9} | {count}")

    print("-" * 50)
    print(f"Totale complessivo turni assegnati: {total_shifts_counted}")
    
    if len(schedule) > 0:
        media = total_shifts_counted / len(schedule.keys())
        print(f"Media farmacie per settimana: {media:.1f}")
    print("-" * 50 + "\n")


def main():
    args = parse_arguments()
    
    schedule, week_labels = load_and_parse_excel(args.input_file)
    
    if not schedule:
        print("Non ho trovato nessun turno valido nel file Excel.")
        print("Assicurati di avere una colonna 'Settimana' e i numeri delle farmacie (1-10) o i nomi (es. Farmacia A) nelle righe corrispondenti.")
        return

    print_weekly_schedule(schedule, week_labels)
    print_shift_statistics(schedule)


if __name__ == "__main__":
    main()