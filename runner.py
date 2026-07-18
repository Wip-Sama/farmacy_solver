import argparse
import subprocess
import logging
import sys
import os
import time
import csv
import tempfile
from datetime import date
from terminal_display import parse_schedule, print_weekly_schedule, print_shift_statistics, print_optimization_cost, generate_csv_report

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_external_solver(executable, domain_file, guess_file, constraints_file, opt_file, dynamic_file=None, live=False, time_limit=None):
    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)
    logging.info(f"Running {executable.upper()} solver with files: {', '.join(files)}")
    if live:
        logging.warning(f"Live printing is currently fully supported only with --clingo. {executable.upper()} will process normally.")
        
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
        return stdout
    except subprocess.TimeoutExpired:
        logging.warning(f"Time limit of {time_limit}s reached. Terminating {executable.upper()}...")
        process.terminate()
        stdout, _ = process.communicate()
        return stdout
    except KeyboardInterrupt:
        logging.warning(f"Execution interrupted by user (Ctrl+C). Terminating {executable.upper()}...")
        process.terminate()
        stdout, _ = process.communicate()
        return stdout
    except FileNotFoundError:
        logging.error(f"{executable.upper()} executable not found. Please ensure it is installed and in your PATH.")
        sys.exit(1)

def run_clingo(domain_file, guess_file, constraints_file, opt_file, dynamic_file=None, live=False, time_limit=None):
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
        logging.info("Found a new solution!")
        model_str = " ".join(str(sym) for sym in m.symbols(shown=True))
        models.append(model_str)
        if m.cost:
            costs.append(m.cost)
            
        if live:
            from terminal_display import parse_schedule, print_weekly_schedule
            print("\n" + "="*50)
            print("LIVE SOLUTION UPDATE")
            print("="*50)
            schedule = parse_schedule(model_str)
            print_weekly_schedule(schedule)
            if m.cost:
                print(f"Current Optimization Value: {m.cost[0]}")
            print("="*50 + "\n")

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
                # Use a short timeout in a loop to allow Python to catch KeyboardInterrupt
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
        # Format the cost in the way terminal_display.py expects (DLV format: COST N@1)
        output += f"COST {final_cost[0]}@1\n"
        
    return output

def generate_dynamic_constraints(reschedule_csv, reschedule_from, unavailables, unavailable_intervals, start_week, end_week):
    """
    Generates a temporary ASP file containing dynamic constraints for rescheduling.
    
    Example generated rules:
    ```asp
    % When reading from previous CSV with --reschedule-from 20
    reschedule_from(20).
    past_turno(1, 1).
    past_turno(1, 3).
    % ...
    % Lock past weeks
    :- past_turno(S, F), not turno(S, F).
    :- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).

    % From --unavailable 1,22
    :- turno(22, 1).

    % From --unavailable-interval 3,25,28
    :- turno(S, 3), S >= 25, S <= 28.
    ```
    🥲 non vanno ne markdown ne wmoji in vscode nei commenti in vscode... piango
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
                for row in reader:
                    if not row or len(row) < 12:
                        continue
                    try:
                        week = int(row[0])
                        if week < reschedule_from:
                            for i in range(1, 11):
                                if row[i+1] == "1":
                                    lines.append(f"past_turno({week}, {i}).\n")
                    except ValueError:
                        continue
                        
        except Exception as e:
            logging.error(f"Failed to read CSV file {reschedule_csv}: {e}")
            sys.exit(1)
            
        lines.append("% Lock past weeks\n")
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
                
    if not lines:
        # We always need the settimana fact!
        lines.append(f"settimana({actual_start_week}..{end_week}).\n")
        
    else:
        # Prepend the settimana fact to ensure it's loaded
        lines.insert(0, f"settimana({actual_start_week}..{end_week}).\n")
        
    fd, path = tempfile.mkstemp(suffix=".lp", text=True)
    with os.fdopen(fd, 'w') as f:
        f.writelines(lines)
    return path

def main():
    optimizations = opt_file = os.path.join("asp", "optimizations")
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
    
    parser.add_argument('--reschedule-csv', type=str, metavar='FILENAME',
                        help="Path to the CSV file of a previous run.")
    parser.add_argument('--reschedule-from', type=int, metavar='WEEK',
                        help="Week number from which to reschedule (past weeks will be fixed). Requires --reschedule-csv.")
    parser.add_argument('--unavailable', type=str, nargs='+', metavar='F,W',
                        help="List of unavailable pharmacies in specific weeks (e.g., 3,15 4,16).")
    parser.add_argument('--unavailable-interval', type=str, nargs='+', metavar='F,W1,W2',
                        help="List of intervals where pharmacies are unavailable (e.g., 3,15,18).")
    
    parser.add_argument('--year', type=int, default=2025,
                        help="L'anno per cui si vuole generare il calendario (default: 2025).")
    parser.add_argument('--start-week', type=int, default=1,
                        help="Settimana di inizio per la schedulazione (default: 1).")
    parser.add_argument('--end-week', type=int, default=None,
                        help="Settimana di fine per la schedulazione (default: ultima settimana dell'anno).")
    
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
    
    end_week = args.end_week if args.end_week is not None else total_weeks
    
    if args.start_week > total_weeks:
        logging.error(f"Error: --start-week {args.start_week} is greater than the total number of weeks in year {args.year} ({total_weeks}).")
        sys.exit(1)
        
    if args.start_week > end_week:
        logging.error(f"Error: --start-week {args.start_week} cannot be greater than --end-week {end_week}.")
        sys.exit(1)

    dynamic_file = None
    try:
        dynamic_file = generate_dynamic_constraints(
            args.reschedule_csv, args.reschedule_from, 
            args.unavailable, args.unavailable_interval,
            args.start_week, end_week
        )

        # Run the selected solver
        start_time = time.time()
        if args.clingo:
            asp_output = run_clingo(domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=args.live, time_limit=args.time_limit)
        elif args.dlv2:
            asp_output = run_external_solver('dlv2', domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=args.live, time_limit=args.time_limit)
        else:
            asp_output = run_external_solver('dlv', domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=args.live, time_limit=args.time_limit)
        elapsed_time = time.time() - start_time
    finally:
        if dynamic_file and os.path.exists(dynamic_file):
            os.remove(dynamic_file)

    if not asp_output or not asp_output.strip():
        logging.warning("Solver returned empty output. No schedule found.")
        sys.exit(0)

    # Parse and display using the existing terminal_display logic
    schedule = parse_schedule(asp_output)
    if not schedule:
        logging.error("No schedule could be parsed from the output.")
        sys.exit(1)

    print_weekly_schedule(schedule, args.year)
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
        generate_csv_report(schedule, args.csv, run_info, args.year)

if __name__ == "__main__":
    main()
