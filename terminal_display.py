import sys
import argparse
import re
import csv
from collections import defaultdict

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
    """Estrae i turni dall'output ASP e li organizza in un dizionario per settimana."""
    pattern = r"turno\((\d+),\s*(\d+)\)"
    matches = re.findall(pattern, asp_output)

    schedule = defaultdict(list)
    for week_str, farmacia_str in matches:
        week = int(week_str)
        farmacia = int(farmacia_str)
        schedule[week].append(farmacia)
        
    return schedule


def get_zona(f_id):
    """Restituisce la zona in base all'ID della farmacia (1-6 Centro, 7-10 Marina)."""
    return "Centro" if 1 <= f_id <= 6 else "Marina"


def print_weekly_schedule(schedule):
    """Stampa la tabella del calendario settimanale."""
    print("-" * 50)
    print(f"\n{'Settimana':<10} | {'Farmacie di Turno'}")
    print("-" * 50)

    for week in sorted(schedule.keys()):
        farmacie = schedule[week]
        formatted_farmacie = [f"F{f} ({get_zona(f)})" for f in sorted(farmacie)]
        print(f"Wk {week:<7} | {', '.join(formatted_farmacie)}")
    print("-" * 50)

def generate_csv_report(schedule, filename, run_info=None):
    """Genera un report CSV della turnazione."""
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Intestazione: Settimana, F1, F2, ..., F10
            header = ['Settimana'] + [f"F{i}" for i in range(1, 11)]
            writer.writerow(header)
            
            for week in sorted(schedule.keys()):
                row = [week]
                farmacie_di_turno = set(schedule[week])
                for i in range(1, 11):
                    row.append(1 if i in farmacie_di_turno else "")
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
    print_weekly_schedule(schedule)
    print_shift_statistics(schedule)
    print_optimization_cost(asp_output)


if __name__ == "__main__":
    main()