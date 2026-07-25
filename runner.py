import argparse
import logging
import sys
import os
import time
from datetime import date
from runner_core import (
    parse_festivities,
    generate_dynamic_constraints,
    run_clingo,
    run_external_solver
)
from terminal_display import (
    parse_schedule,
    print_weekly_schedule,
    print_shift_statistics,
    print_optimization_cost,
    generate_csv_report
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    optimizations = os.path.join("asp", "optimizations")
    if not os.path.exists(optimizations):
        logging.error(f"Optimizations directory '{optimizations}' not found.")
        sys.exit(1)
    else:
        optimizations_list = [f[:-4] for f in os.listdir(optimizations) if f.endswith('.lp')]
    
    parser = argparse.ArgumentParser(description="Python runner for ASP pharmacy scheduling.")
    parser.add_argument('--base', choices=['choice', 'or'], default='choice',
                        help="The base encoding to use (default: choice).")
    parser.add_argument('--opt', choices=optimizations_list,
                        default='penalita_esponenziale',
                        help="The optimization strategy to use (default: penalita_esponenziale).")
    
    parser.add_argument('--time-limit', type=int, default=None,
                        help="Time limit for the solver in seconds.")
    parser.add_argument('--live', action='store_true',
                        help="Print live the latest found solution as it is discovered.")
    parser.add_argument('--csv', type=str, metavar='FILENAME',
                        help="Generate a CSV report of the schedule to the specified file.")
    parser.add_argument('--csv-mode', choices=['compact', 'normal', 'tiny', 'extended'], default='normal',
                        help="CSV mode: compact (1 row/week, full cols), normal (break week on festivity), tiny (1 row/week, condensed col), extended (daily view).")
    parser.add_argument('--csv-direction', choices=['column', 'row'], default='column',
                        help="CSV direction: column (vertical top-to-bottom), row (12-month horizontal grid).")
    parser.add_argument('--csv-map-pharmacies', type=str, metavar='MAPPING',
                        help="Pharmacy name mapping (e.g. '1,BUCCARELLI;2,SANMICHELE' or path to file).")
    parser.add_argument('--first-day-of-the-week', '--fdotw', dest='first_day_of_week', default='monday',
                        help="First day of the week for scheduling (e.g. monday, saturday, sunday, 0..6).")
    
    parser.add_argument('--reschedule-csv', type=str, metavar='FILENAME',
                        help="Path to the CSV file of a previous run.")
    parser.add_argument('--reschedule-from', type=str, metavar='WEEK',
                        help="Week number from which to reschedule (number or 'now'). Requires --reschedule-csv.")
    parser.add_argument('--unavailable', type=str, nargs='+', metavar='F,W',
                        help="List of unavailable pharmacies in specific weeks (e.g., 3,15 4,16).")
    parser.add_argument('--unavailable-interval', type=str, nargs='+', metavar='F,W1,W2',
                        help="List of intervals where pharmacies are unavailable (e.g., 3,15,18).")
    
    parser.add_argument('--year', type=int, default=2025,
                        help="L'anno per cui si vuole generare il calendario (default: 2025).")
    parser.add_argument('--start-week', type=str, default='1',
                        help="Settimana di inizio per la schedulazione (numero o 'now').")
    parser.add_argument('--end-week', type=str, default=None,
                        help="Settimana di fine per la schedulazione (numero o 'now').")
    
    # Festivities & history flags
    parser.add_argument('--festivities', type=str, action='append', metavar='NAME,START,FINISH',
                        help="Custom festivities in format 'name,start_date,finish_date' or 'name,date'.")
    parser.add_argument('--auto-festivities', action='store_true',
                        help="Automatically generate Italian national festivities for the year.")
    parser.add_argument('--prev-year', type=str, metavar='FILENAME',
                        help="Path to previous year's CSV schedule to extract past festivity assignments.")

    # Mutually exclusive group for solver selection
    solver_group = parser.add_mutually_exclusive_group()
    solver_group.add_argument('--dlv', action='store_true', help="Use DLV solver.")
    solver_group.add_argument('--dlv2', action='store_true', help="Use DLV2 solver.")
    solver_group.add_argument('--clingo', action='store_true', help="Use Clingo solver via Python API.")

    args = parser.parse_args()

    # Automatically route CSV files to a dedicated 'schedules' folder if no path is specified
    csv_dir = "schedules"
    if args.csv and not os.path.dirname(args.csv):
        args.csv = os.path.join(csv_dir, args.csv)
    if args.reschedule_csv and not os.path.dirname(args.reschedule_csv):
        args.reschedule_csv = os.path.join(csv_dir, args.reschedule_csv)
    if args.prev_year and not os.path.dirname(args.prev_year):
        args.prev_year = os.path.join(csv_dir, args.prev_year)

    # Default to clingo if no solver is specified
    if not args.dlv and not args.dlv2 and not args.clingo:
        args.clingo = True

    domain_file = os.path.join("asp", "domain.lp")
    guess_file = os.path.join("asp", f"guess_{args.base}.lp")
    constraints_file = os.path.join("asp", "constraints.lp")
    opt_file = os.path.join("asp", "optimizations", f"{args.opt}.lp")

    for f in [domain_file, guess_file, constraints_file, opt_file]:
        if not os.path.exists(f):
            logging.error(f"File '{f}' not found.")
            sys.exit(1)

    if args.reschedule_from and not args.reschedule_csv:
        parser.error("--reschedule-from requires --reschedule-csv")

    total_weeks = date(args.year, 12, 28).isocalendar()[1]

    from runner_core import parse_week_param
    start_week = parse_week_param(args.start_week, args.year, args.first_day_of_week) or 1
    end_week = parse_week_param(args.end_week, args.year, args.first_day_of_week) or total_weeks
    reschedule_from = parse_week_param(args.reschedule_from, args.year, args.first_day_of_week)

    if args.reschedule_csv:
        if reschedule_from is None:
            if start_week > 1:
                reschedule_from = start_week
            else:
                reschedule_from = 1
    
    if start_week > total_weeks:
        logging.error(f"Error: --start-week {start_week} is greater than the total number of weeks in year {args.year} ({total_weeks}).")
        sys.exit(1)
        
    if start_week > end_week:
        logging.error(f"Error: --start-week {start_week} cannot be greater than --end-week {end_week}.")
        sys.exit(1)

    festivities_dict = parse_festivities(args.festivities, args.auto_festivities, args.year)

    dynamic_file = None
    try:
        dynamic_file = generate_dynamic_constraints(
            args.reschedule_csv, reschedule_from, 
            args.unavailable, args.unavailable_interval,
            start_week, end_week,
            festivities_dict=festivities_dict,
            prev_year_csv=args.prev_year,
            first_day_of_week=args.first_day_of_week,
            year=args.year
        )

        def on_model_cb(m, model_str, count):
            if args.live:
                print("\n" + "="*50)
                print(f"LIVE SOLUTION UPDATE #{count}")
                print("="*50)
                schedule, fest_sched = parse_schedule(model_str)
                print_weekly_schedule(schedule, args.year, fest_sched, festivities_dict, first_day_of_week=args.first_day_of_week)
                if m.cost:
                    print(f"Current Optimization Value: {m.cost[0]}")
                print("="*50 + "\n")

        # Run the selected solver
        start_time = time.time()
        if args.clingo:
            asp_output, _ = run_clingo(domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=args.live, time_limit=args.time_limit, year=args.year, on_model_cb=on_model_cb)
        elif args.dlv2:
            asp_output, _ = run_external_solver('dlv2', domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=args.live, time_limit=args.time_limit)
        else:
            asp_output, _ = run_external_solver('dlv', domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=args.live, time_limit=args.time_limit)
        elapsed_time = time.time() - start_time
    finally:
        if dynamic_file and os.path.exists(dynamic_file):
            os.remove(dynamic_file)

    if not asp_output or not asp_output.strip():
        logging.warning("Solver returned empty output. No schedule found.")
        sys.exit(0)

    # Parse and display using the existing terminal_display logic
    schedule, festivo_schedule = parse_schedule(asp_output)
    if not schedule:
        logging.error("No schedule could be parsed from the output.")
        sys.exit(1)

    print_weekly_schedule(schedule, args.year, festivo_schedule, festivities_dict, first_day_of_week=args.first_day_of_week)
    print_shift_statistics(schedule)
    print_optimization_cost(asp_output)
    print(f"\nComputation time: {elapsed_time:.2f} seconds")

    if args.csv:
        run_info = {
            'solver': 'clingo' if args.clingo else ('dlv2' if args.dlv2 else 'dlv'),
            'base': args.base,
            'opt': args.opt,
            'time': elapsed_time
        }
        if os.path.dirname(args.csv):
            os.makedirs(os.path.dirname(args.csv), exist_ok=True)
        generate_csv_report(
            schedule, args.csv, run_info, args.year, festivo_schedule, festivities_dict,
            csv_mode=args.csv_mode, csv_direction=args.csv_direction, csv_map_pharmacies=args.csv_map_pharmacies,
            first_day_of_week=args.first_day_of_week
        )

if __name__ == "__main__":
    main()
