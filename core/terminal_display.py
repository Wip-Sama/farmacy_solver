import sys
import argparse
import re
import csv
import os
import logging
from collections import defaultdict
from datetime import datetime, timedelta

def get_week_date(week_number, year=2025, first_day_of_week=0):
    from core.runner_core import get_week_start_date
    d_obj = get_week_start_date(week_number, year, first_day_of_week)
    return d_obj.strftime("%Y-%m-%d")

def parse_arguments():
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
    # Controllo di sicurezza su stdin senza pipe
    if args.input_file.name == '<stdin>' and sys.stdin.isatty():
        print("Errore: Nessun input ricevuto. Passa un file o usa la pipe.")
        print("Esegui 'python script.py --help' per maggiori informazioni.")
        sys.exit(1)

    asp_output = args.input_file.read()

    if not asp_output.strip():
        print("Errore: L'input ricevuto è vuoto. Verifica l'output del solver.")
        sys.exit(1)
        
    return asp_output


def parse_schedule(asp_output):
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
    # Qui non so bene che cosa devo fare di preciso:
    # Per ora ho rimosso l'hardcoding 1-6 / 7-10. 
    # Mantengo la firma giusto per compatibilità con il runner, ma la logica andrà passata dinamicamente.
    return "Assegnata"


def print_weekly_schedule(schedule, year=2025, festivo_schedule=None, festivities_dict=None, first_day_of_week=0):
    print("-" * 85)
    print(f"{'Settimana':<22} | {'Festività':<20} | {'Farmacie di Turno'}")
    print("-" * 85)

    festivo_sched = festivo_schedule or {}
    fest_dict = festivities_dict or {}

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
            
            # Formattazione neutra senza zone fisse
            formatted_farmacie = [f"F{f}" for f in sorted(f_assigned)]
            week_display = f"Wk {week:<2} ({start_date_str})"
            
            print(f"{week_display:<22} | {fest_label:<20} | {', '.join(formatted_farmacie)}")
    print("-" * 85)

from core.csv_utils import parse_pharmacy_mapping, generate_csv_report


def print_shift_statistics(schedule):
    print(f"{'Farmacia':<10} | {'Turni Assegnati'}")
    print("-" * 50)
    
    # Estrazione dinamica delle farmacie attive
    active_pharmacies = set()
    for f_list in schedule.values():
        active_pharmacies.update(f_list)
    
    total_shifts_counted = 0
    for farmacia in sorted(active_pharmacies): 
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
    schedule, fest_schedule = parse_schedule(asp_output)
    
    if not schedule:
        print("Nessun turno trovato nell'output. Verifica che il solver abbia trovato una soluzione valida.")
        return

    print_weekly_schedule(schedule, args.year)
    print_shift_statistics(schedule)
    print_optimization_cost(asp_output)


if __name__ == "__main__":
    main()