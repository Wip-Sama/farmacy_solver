import subprocess
import sys
import os
import time
import csv
import tempfile
from datetime import date
from enum import Enum
from typing import List, Optional, Annotated

# Force utf-8 encoding on Windows to support rich progress spinners (which use braille unicode chars)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from terminal_display import (
    parse_schedule, 
    get_zona,
    get_week_date,
    generate_csv_report
)

app = typer.Typer(help="Rich runner for ASP pharmacy scheduling.")
console = Console()

class SolverType(str, Enum):
    clingo = "clingo"
    dlv = "dlv"
    dlv2 = "dlv2"

def run_external_solver(executable, domain_file, guess_file, constraints_file, opt_file, dynamic_file=None, live=False, time_limit=None):
    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)
        
    console.print(f"[cyan]Running {executable.upper()} solver with files: {', '.join(files)}[/cyan]")
    if live:
        console.print(f"[yellow]Live printing is currently fully supported only with --clingo. {executable.upper()} will process normally.[/yellow]")
        
    try:
        process = subprocess.Popen(
            [executable] + files,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            progress.add_task(description=f"[cyan]Running {executable.upper()}...", total=None)
            stdout, stderr = process.communicate(timeout=time_limit)
            
        if process.returncode != 0 and process.returncode is not None:
            console.print(f"[red]{executable.upper()} execution failed: {stderr}[/red]")
            sys.exit(1)
        return stdout
    except subprocess.TimeoutExpired:
        console.print(f"[yellow]Time limit of {time_limit}s reached. Terminating {executable.upper()}...[/yellow]")
        process.terminate()
        stdout, _ = process.communicate()
        return stdout
    except KeyboardInterrupt:
        console.print(f"[yellow]Execution interrupted by user (Ctrl+C). Terminating {executable.upper()}...[/yellow]")
        process.terminate()
        stdout, _ = process.communicate()
        return stdout
    except FileNotFoundError:
        console.print(f"[red]{executable.upper()} executable not found. Please ensure it is installed and in your PATH.[/red]")
        sys.exit(1)

def run_clingo(domain_file, guess_file, constraints_file, opt_file, dynamic_file=None, live=False, time_limit=None):
    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)
        
    console.print(f"[cyan]Running Clingo solver via Python API with files: {', '.join(files)}[/cyan]")
    
    try:
        import clingo
    except ImportError:
        console.print("[red]The 'clingo' Python module is not installed. Please install it using 'pip install clingo'.[/red]")
        sys.exit(1)

    ctl = clingo.Control()
    for f in files:
        ctl.load(f)
        
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        progress.add_task(description="[green]Grounding...", total=None)
        ctl.ground([("base", [])])
    
    models = []
    costs = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        task_id = progress.add_task(description="[cyan]Solving...", total=None)

        def on_model(m):
            model_str = " ".join(str(sym) for sym in m.symbols(shown=True))
            models.append(model_str)
            if m.cost:
                costs.append(m.cost)
            
            cost_str = f" [magenta](Cost: {m.cost[0]})[/magenta]" if m.cost else ""
            progress.update(task_id, description=f"[cyan]Solving... [green]Found solution #{len(models)}{cost_str}[/green]")
                
            if live:
                progress.console.print("\n[bold yellow]" + "="*50 + "[/bold yellow]")
                progress.console.print("[bold yellow]LIVE SOLUTION UPDATE[/bold yellow]")
                progress.console.print("[bold yellow]" + "="*50 + "[/bold yellow]")
                # We can print a simple version here since it's just live update
                schedule = parse_schedule(model_str)
                for week in sorted(schedule.keys()):
                    progress.console.print(f"Wk {week}: {', '.join([f'F{f}' for f in sorted(schedule[week])])}")
                if m.cost:
                    progress.console.print(f"[bold magenta]Current Optimization Value: {m.cost[0]}[/bold magenta]")
                progress.console.print("[bold yellow]" + "="*50 + "\n[/bold yellow]")

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
                        console.print(f"[yellow]Time limit of {time_limit}s reached. Cancelling solver...[/yellow]")
                        handle.cancel()
                        handle.wait()
                else:
                    while not handle.wait(1.0):
                        pass
            except KeyboardInterrupt:
                console.print("[yellow]Execution interrupted by user (Ctrl+C). Cancelling solver...[/yellow]")
                handle.cancel()
                handle.wait()
    
    output = ""
    if models:
        output += models[-1] + "\n"
    if costs:
        final_cost = costs[-1]
        output += f"COST {final_cost[0]}@1\n"
        
    return output

def generate_dynamic_constraints(reschedule_csv: Optional[str], reschedule_from: Optional[int], 
                                 unavailables: Optional[List[str]], unavailable_intervals: Optional[List[str]], 
                                 start_week: int, end_week: int):
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
            console.print(f"[red]Failed to read CSV file {reschedule_csv}: {e}[/red]")
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
                console.print(f"[red]Invalid format for --unavailable: {u}. Expected F,W[/red]")
                sys.exit(1)
                
    if unavailable_intervals:
        for u in unavailable_intervals:
            try:
                f, w1, w2 = u.split(',')
                lines.append(f":- turno(S, {f}), S >= {w1}, S <= {w2}.\n")
            except ValueError:
                console.print(f"[red]Invalid format for --unavailable-interval: {u}. Expected F,W1,W2[/red]")
                sys.exit(1)
                
    if not lines:
        lines.append(f"settimana({actual_start_week}..{end_week}).\n")
    else:
        lines.insert(0, f"settimana({actual_start_week}..{end_week}).\n")
        
    fd, path = tempfile.mkstemp(suffix=".lp", text=True)
    with os.fdopen(fd, 'w') as f:
        f.writelines(lines)
    return path

@app.command()
def main(
    base: Annotated[str, typer.Option(help="The base encoding to use")] = "choice",
    opt: Annotated[str, typer.Option(help="The optimization strategy to use")] = "penalita_esponenziale",
    time_limit: Annotated[Optional[int], typer.Option(help="Time limit for the solver in seconds")] = None,
    live: Annotated[bool, typer.Option(help="Print live the latest found solution as it is discovered")] = False,
    csv_file: Annotated[Optional[str], typer.Option("--csv", help="Generate a CSV report to the specified file")] = None,
    reschedule_csv: Annotated[Optional[str], typer.Option(help="Path to the CSV file of a previous run")] = None,
    reschedule_from: Annotated[Optional[int], typer.Option(help="Week number from which to reschedule")] = None,
    unavailable: Annotated[Optional[List[str]], typer.Option(help="List of unavailable pharmacies (e.g., 3,15 4,16)")] = None,
    unavailable_interval: Annotated[Optional[List[str]], typer.Option(help="List of unavailable intervals (e.g., 3,15,18)")] = None,
    year: Annotated[int, typer.Option(help="L'anno per cui si vuole generare il calendario")] = 2025,
    start_week: Annotated[int, typer.Option(help="Settimana di inizio per la schedulazione")] = 1,
    end_week: Annotated[Optional[int], typer.Option(help="Settimana di fine per la schedulazione")] = None,
    solver: Annotated[SolverType, typer.Option(help="Solver to use")] = SolverType.clingo
):
    optimizations = os.path.join("asp", "optimizations")
    if not os.path.exists(optimizations):
        console.print(f"[red]Optimizations directory '{optimizations}' not found.[/red]")
        sys.exit(1)
    
    # Automatically route CSV files to a dedicated 'schedules' folder if no path is specified
    csv_dir = "schedules"
    if csv_file and not os.path.dirname(csv_file):
        csv_file = os.path.join(csv_dir, csv_file)
    if reschedule_csv and not os.path.dirname(reschedule_csv):
        reschedule_csv = os.path.join(csv_dir, reschedule_csv)

    domain_file = os.path.join("asp", "domain.lp")
    guess_file = os.path.join("asp", f"guess_{base}.lp")
    constraints_file = os.path.join("asp", "constraints.lp")
    opt_file = os.path.join("asp", "optimizations", f"{opt}.lp")

    for f in [domain_file, guess_file, constraints_file, opt_file]:
        if not os.path.exists(f):
            console.print(f"[red]File '{f}' not found.[/red]")
            sys.exit(1)

    if reschedule_from and not reschedule_csv:
        console.print("[red]--reschedule-from requires --reschedule-csv[/red]")
        raise typer.Exit(code=1)

    total_weeks = date(year, 12, 28).isocalendar()[1]
    final_end_week = end_week if end_week is not None else total_weeks
    
    if start_week > total_weeks:
        console.print(f"[red]Error: --start-week {start_week} is greater than the total number of weeks in year {year} ({total_weeks}).[/red]")
        raise typer.Exit(code=1)
        
    if start_week > final_end_week:
        console.print(f"[red]Error: --start-week {start_week} cannot be greater than --end-week {final_end_week}.[/red]")
        raise typer.Exit(code=1)

    dynamic_file = None
    try:
        dynamic_file = generate_dynamic_constraints(
            reschedule_csv, reschedule_from, 
            unavailable, unavailable_interval,
            start_week, final_end_week
        )

        start_time = time.time()
        if solver == SolverType.clingo:
            asp_output = run_clingo(domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=live, time_limit=time_limit)
        elif solver == SolverType.dlv2:
            asp_output = run_external_solver("dlv2", domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=live, time_limit=time_limit)
        elif solver == SolverType.dlv:
            asp_output = run_external_solver("dlv", domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=live, time_limit=time_limit)

        elapsed_time = time.time() - start_time

        schedule = parse_schedule(asp_output)
        
        if not schedule:
            console.print("[red]No schedule could be parsed from the output.[/red]")
            raise typer.Exit(code=1)

        # 1. Print Weekly Schedule Table
        table = Table(title=f"Calendario Settimanale ({year})", show_header=True, header_style="bold blue")
        table.add_column("Settimana", style="dim", width=22)
        table.add_column("Farmacie di Turno", style="bold green")

        for week in sorted(schedule.keys()):
            farmacie = schedule[week]
            formatted_farmacie = [f"F{f} ({get_zona(f)})" for f in sorted(farmacie)]
            date_str = get_week_date(week, year)
            week_display = f"Wk {week:<2} ({date_str})"
            table.add_row(week_display, ", ".join(formatted_farmacie))
            
        console.print(table)

        # 2. Print Shift Statistics Table
        stat_table = Table(title="Statistiche Turni", show_header=True, header_style="bold magenta")
        stat_table.add_column("Farmacia", justify="center")
        stat_table.add_column("Turni Assegnati", justify="right")

        total_shifts_counted = 0
        for farmacia in range(1, 11): 
            count = sum(farmacia in farmacie for farmacie in schedule.values())
            total_shifts_counted += count
            stat_table.add_row(f"F{farmacia}", str(count))
            
        console.print(stat_table)
        
        console.print(f"[bold cyan]Totale complessivo turni assegnati:[/bold cyan] {total_shifts_counted}")
        if len(schedule) > 0:
            media = total_shifts_counted / len(schedule.keys())
            console.print(f"[bold cyan]Media farmacie per settimana:[/bold cyan] {media:.1f}")

        # 3. Print Optimization Cost
        import re
        cost_match = re.search(r"COST\s+(\d+)@\d+", asp_output, re.IGNORECASE)
        if cost_match:
            penalty = int(cost_match.group(1))
            console.print(f"\n[bold magenta]Valore di Ottimizzazione (Penalità divario):[/bold magenta] {penalty}")
        else:
            console.print("\n[yellow]Nessun dato di ottimizzazione (COST) trovato nell'output.[/yellow]")

        console.print(f"\n[bold green]Computation time: {elapsed_time:.2f} seconds[/bold green]")

        if csv_file:
            run_info = {
                'solver': solver.value,
                'base': base,
                'opt': opt,
                'time': elapsed_time
            }
            if os.path.dirname(csv_file):
                os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            generate_csv_report(schedule, csv_file, run_info, year)

    finally:
        if dynamic_file and os.path.exists(dynamic_file):
            os.remove(dynamic_file)

if __name__ == "__main__":
    app()
