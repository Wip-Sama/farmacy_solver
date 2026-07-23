import sys
import argparse
import re
import csv
from collections import defaultdict
from datetime import datetime, timedelta

def get_week_date(week_number, year=2025):
    d = datetime(year, 1, 1)
    if d.weekday() != 0:
        d += timedelta(days=(7 - d.weekday()))
    current_date = d + timedelta(weeks=week_number - 1)
    return current_date.strftime("%Y-%m-%d")

def parse_arguments():
    """Gestisce gli argomenti passati da riga di comando (argv)."""
    parser = argparse.ArgumentParser(
        description="Parser per l'output ASP della turnazione delle farmacie.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        'input_file', 
        nargs='?', 
        type=argparse.FileType('r', encoding='utf-8'), 
        default=sys.stdin,
        help="Il file di output generato da DLV/Clingo.\nSe omesso, lo script leggerà automaticamente da standard input (pipe)."
    )
    
    parser.add_argument(
        '--year', type=int, default=2025,
        help="L'anno per cui si vuole generare il calendario (default: 2025)."
    )
    
    return parser.parse_args()


def read_input(args):
    """Legge l'output di DLV/Clingo dal file passato come argomento o dalla pipe."""
    # Controllo di sicurezza: se stiamo aspettando l'input da stdin ma il terminale 
    # è interattivo (ovvero l'utente non ha usato la pipe), blocchiamo l'esecuzione.
    if args.input_file.name == '<stdin>' and sys.stdin.isatty():
        print("Errore: Nessun input ricevuto. Passa un file o usa la pipe.")
        print("Esegui 'python script.py --help' per maggiori informazioni.")
        sys.exit(1)

    # Legge il contenuto (sia che sia un file, sia che sia la pipe)
    asp_output = args.input_file.read()

    # Controllo se l'output è vuoto
    if not asp_output.strip():
        print("Errore: L'input ricevuto è vuoto. Verifica l'output del solver.")
        sys.exit(1)
        
    return asp_output


def parse_schedule(asp_output):
    """Estrae i turni e i turni festivi dall'output ASP."""
    pattern_turno = r"turno\((\d+),\s*(\d+)\)"
    matches_turno = re.findall(pattern_turno, asp_output)

    schedule = defaultdict(list)
    for week_str, farmacia_str in matches_turno:
        week = int(week_str)
        farmacia = int(farmacia_str)
        schedule[week].append(farmacia)

    pattern_festivo = r'turno_festivo\((?:"([^"]+)"|([a-zA-Z0-9_]+)),\s*(\d+)\)'
    matches_festivo = re.findall(pattern_festivo, asp_output)

    festivo_schedule = defaultdict(list)
    for m in matches_festivo:
        name = (m[0] or m[1]).lower()
        farmacia = int(m[2])
        festivo_schedule[name].append(farmacia)

    return schedule, festivo_schedule


def get_zona(f_id):
    """Restituisce la zona in base all'ID della farmacia (1-6 Centro, 7-10 Marina)."""
    return "Centro" if 1 <= f_id <= 6 else "Marina"


def print_weekly_schedule(schedule, year=2025, festivo_schedule=None, festivities_dict=None):
    """Stampa la tabella del calendario settimanale spezzando le righe sulle festività."""
    print("-" * 85)
    print(f"{'Settimana':<22} | {'Festività':<20} | {'Farmacie di Turno'}")
    print("-" * 85)

    festivo_sched = festivo_schedule or {}
    fest_dict = festivities_dict or {}

    for week in sorted(schedule.keys()):
        monday_str = get_week_date(week, year)
        monday_date = datetime.strptime(monday_str, "%Y-%m-%d").date()
        
        days_details = []
        for day_idx in range(7):
            day_date = monday_date + timedelta(days=day_idx)
            fest_name = fest_dict.get(day_date, "")
            
            if fest_name and day_idx < 5:  # mid-week festivity
                f_assigned = set(festivo_sched.get(fest_name.lower(), schedule[week]))
            else:
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
            
            formatted_farmacie = [f"F{f} ({get_zona(f)})" for f in sorted(f_assigned)]
            week_display = f"Wk {week:<2} ({start_date_str})"
            
            print(f"{week_display:<22} | {fest_label:<20} | {', '.join(formatted_farmacie)}")
    print("-" * 85)

def generate_csv_report(schedule, filename, run_info=None, year=2025, festivo_schedule=None, festivities_dict=None):
    """Genera un report CSV della turnazione con la colonna 'Festività' e spezzamento righe per festività."""
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Intestazione: Settimana, Data, Festività, F1, F2, ..., F10
            header = ['Settimana', 'Data', 'Festività'] + [f"F{i}" for i in range(1, 11)]
            writer.writerow(header)
            
            festivo_sched = festivo_schedule or {}
            fest_dict = festivities_dict or {}

            for week in sorted(schedule.keys()):
                monday_str = get_week_date(week, year)
                monday_date = datetime.strptime(monday_str, "%Y-%m-%d").date()
                
                # Construct 7 days details
                days_details = []
                for day_idx in range(7):
                    day_date = monday_date + timedelta(days=day_idx)
                    fest_name = fest_dict.get(day_date, "")
                    
                    if fest_name and day_idx < 5:  # mid-week festivity
                        f_assigned = set(festivo_sched.get(fest_name.lower(), schedule[week]))
                    else:
                        f_assigned = set(schedule[week])

                    days_details.append((day_date, fest_name, f_assigned))

                # Group consecutive days with identical (fest_name, f_assigned)
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
                    for i in range(1, 11):
                        row.append(1 if i in f_assigned else "")
                    writer.writerow(row)
                
            if run_info:
                writer.writerow([])
                writer.writerow(['--- Run Info ---'])
                writer.writerow(['Solver', run_info.get('solver', 'N/A')])
                writer.writerow(['Base', run_info.get('base', 'N/A')])
                writer.writerow(['Optimization', run_info.get('opt', 'N/A')])
                writer.writerow(['Computation Time (s)', f"{run_info.get('time', 0):.2f}"])
                
        print(f"Report CSV generato con successo in: {filename}")
    except Exception as e:
        print(f"Errore durante la generazione del report CSV: {e}")



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
    print("-" * 50)


def print_optimization_cost(asp_output):
    """Estrae il costo ASP (ora usato come penalità per il divario)."""
    cost_match = re.search(r"COST\s+(\d+)@\d+", asp_output, re.IGNORECASE)
    
    if cost_match:
        penalty = int(cost_match.group(1))
        print(f"Valore di Ottimizzazione (Penalità divario): {penalty}")
    else:
        print("Nessun dato di ottimizzazione (COST) trovato nell'output.")
    print("-" * 50 + "\n")


def main():
    args = parse_arguments()
    asp_output = read_input(args)
    schedule = parse_schedule(asp_output)
    
    if not schedule:
        print("Nessun turno trovato nell'output. Verifica che il solver abbia trovato una soluzione valida.")
        return

    # 4. Visualizzazione a schermo
    print_weekly_schedule(schedule, args.year)
    print_shift_statistics(schedule)
    print_optimization_cost(asp_output)


if __name__ == "__main__":
    main()