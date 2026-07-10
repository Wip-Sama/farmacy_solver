import argparse
import subprocess
import logging
import sys
import os
import time
from terminal_display import parse_schedule, print_weekly_schedule, print_shift_statistics, print_optimization_cost, generate_csv_report

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_external_solver(executable, base_file, opt_file, live=False, time_limit=None):
    logging.info(f"Running {executable.upper()} solver with files: {base_file}, {opt_file}")
    if live:
        logging.warning(f"Live printing is currently fully supported only with --clingo. {executable.upper()} will process normally.")
        
    try:
        process = subprocess.Popen(
            [executable, base_file, opt_file],
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

def run_clingo(base_file, opt_file, live=False, time_limit=None):
    logging.info(f"Running Clingo solver via Python API with files: {base_file}, {opt_file}")
    try:
        import clingo
    except ImportError:
        logging.error("The 'clingo' Python module is not installed. Please install it using 'pip install clingo'.")
        sys.exit(1)

    ctl = clingo.Control()
    ctl.load(base_file)
    ctl.load(opt_file)
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
                finished = handle.wait(time_limit)
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

def main():
    parser = argparse.ArgumentParser(description="Python runner for ASP pharmacy scheduling.")
    parser.add_argument('--base', choices=['choice', 'or'], default='choice',
                        help="The base encoding to use (default: choice).")
    parser.add_argument('--opt', choices=['differenza_turni', 'differenza_turni_con_penalita', 'penalita_esponenziale'],
                        default='penalita_esponenziale',
                        help="The optimization strategy to use (default: penalita_esponenziale).")
    
    parser.add_argument('--time-limit', type=int, default=None,
                        help="Time limit for the solver in seconds.")
    parser.add_argument('--live', action='store_true',
                        help="Print live the latest found solution as it is discovered.")
    parser.add_argument('--csv', type=str, metavar='FILENAME',
                        help="Generate a CSV report of the schedule to the specified file.")
    
    # Mutually exclusive group for solver selection
    solver_group = parser.add_mutually_exclusive_group()
    solver_group.add_argument('--dlv', action='store_true', help="Use DLV solver.")
    solver_group.add_argument('--dlv2', action='store_true', help="Use DLV2 solver.")
    solver_group.add_argument('--clingo', action='store_true', default=True, help="Use Clingo solver via Python API.")

    args = parser.parse_args()

    # Default to clingo if no solver is specified
    if not args.dlv and not args.dlv2 and not args.clingo:
        args.clingo = True

    base_file = f"base_{args.base}.asp"
    
    # Keep the logic for opt_file depending on clingo vs others if needed.
    if args.clingo:
        opt_file = os.path.join("optimizations_choice", f"{args.opt}.asp")
    else:
        opt_file = os.path.join("optimizations_or", f"{args.opt}.asp")

    if not os.path.exists(base_file):
        logging.error(f"Base file '{base_file}' not found.")
        sys.exit(1)
        
    if not os.path.exists(opt_file):
        logging.error(f"Optimization file '{opt_file}' not found.")
        sys.exit(1)

    # Run the selected solver
    start_time = time.time()
    if args.clingo:
        asp_output = run_clingo(base_file, opt_file, live=args.live, time_limit=args.time_limit)
    elif args.dlv2:
        asp_output = run_external_solver('dlv2', base_file, opt_file, live=args.live, time_limit=args.time_limit)
    else:
        asp_output = run_external_solver('dlv', base_file, opt_file, live=args.live, time_limit=args.time_limit)
    elapsed_time = time.time() - start_time

    if not asp_output or not asp_output.strip():
        logging.warning("Solver returned empty output. No schedule found.")
        sys.exit(0)

    # Parse and display using the existing terminal_display logic
    schedule = parse_schedule(asp_output)
    if not schedule:
        logging.error("No schedule could be parsed from the output.")
        sys.exit(1)

    print_weekly_schedule(schedule)
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
        generate_csv_report(schedule, args.csv, run_info)

if __name__ == "__main__":
    main()
