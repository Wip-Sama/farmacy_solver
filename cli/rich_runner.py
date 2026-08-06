import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional, Annotated

# Force utf-8 encoding on Windows to support rich progress spinners (which use braille unicode chars)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import typer
from rich.console import Console, Group
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live

from core.config import ASP_DIR, SCHEDULES_DIR
from core.runner_core import (
    parse_festivities,
    generate_dynamic_constraints,
    run_external_solver
)
from core.terminal_display import (
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

def generate_output_tables(schedule, year, cost_value=None, elapsed_time=None, is_live=False, festivo_schedule=None, festivities_dict=None, pharmacies_list=None):
    renderables = []

    ### Weekly Schedule Table
    title = f"[bold yellow]LIVE: Calendario Settimanale ({year})[/bold yellow]" if is_live else f"Calendario Settimanale ({year})"
    table = Table(title=title, show_header=True, header_style="bold blue")
    table.add_column("Settimana", style="dim", width=22)
    table.add_column("Festività", style="bold blue", width=20)
    table.add_column("Farmacie di Turno", style="bold green")

    festivo_sched = festivo_schedule or {}
    fest_dict = festivities_dict or {}

    for week in sorted(schedule.keys()):
        monday_str = get_week_date(week, year)
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
            
            formatted_farmacie = [f"F{f} ({get_zona(f)})" for f in sorted(f_assigned)]
            week_display = f"Wk {week:<2} ({start_date_str})"
            
            fest_display = f"[bold cyan]{fest_label}[/bold cyan]" if fest_label else ""
            table.add_row(week_display, fest_display, ", ".join(formatted_farmacie))
        
    renderables.append(table)

    ### Shift Statistics Table
    stat_table = Table(title="Statistiche Turni", show_header=True, header_style="bold magenta")
    stat_table.add_column("Farmacia", justify="center")
    stat_table.add_column("Turni Assegnati", justify="right")

    total_shifts_counted = 0
    pharma_ids = pharmacies_list if pharmacies_list is not None else range(1, 11)
    for farmacia in pharma_ids: 
        count = sum(farmacia in farmacie for farmacie in schedule.values())
        total_shifts_counted += count
        stat_table.add_row(f"F{farmacia}", str(count))
        
    renderables.append(stat_table)
    
    stats_text = f"[bold cyan]Totale complessivo turni assegnati:[/bold cyan] {total_shifts_counted}"
    if len(schedule) > 0:
        media = total_shifts_counted / len(schedule.keys())
        stats_text += f"\n[bold cyan]Media farmacie per settimana:[/bold cyan] {media:.1f}"
    
    renderables.append(Text.from_markup(stats_text))

    ### Optimization Cost
    if cost_value is not None:
        renderables.append(Text.from_markup(f"\n[bold magenta]Valore di Ottimizzazione (Penalità divario):[/bold magenta] {cost_value}"))
    else:
        renderables.append(Text.from_markup("\n[yellow]Nessun dato di ottimizzazione (COST) trovato nell'output.[/yellow]"))

    if elapsed_time is not None:
        renderables.append(Text.from_markup(f"\n[bold green]Computation time: {elapsed_time:.2f} seconds[/bold green]"))

    return renderables

def run_rich_clingo(domain_file, guess_file, constraints_file, opt_file, dynamic_file=None, live=False, time_limit=None, year=2025, festivities_dict=None, pharmacies_list=None):
    files = [domain_file, guess_file, constraints_file, opt_file]
    if dynamic_file:
        files.append(dynamic_file)

    console.print(f"[cyan]Running Clingo solver via Python API with files: {', '.join(files)}[/cyan]")
    
    try:
        import clingo
    except ImportError:
        console.print("[red]The 'clingo' Python module is not installed. Please install it using 'pip install clingo'.[/red]")
        sys.exit(1)

    ctl = clingo.Control(
        arguments=[]
        # arguments=["--opt-strat=usc"],
        # arguments=["--parallel-mode=4"],
        # arguments=["--parallel-mode=4", "--opt-strat=usc"],
    )
    for f in files:
        ctl.load(f)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="[green]Grounding...", total=None)
        ctl.ground([("base", [])])

    models = []
    costs = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    )
    task_id = progress.add_task(description="[cyan]Solving...", total=None)

    def on_model(m):
        model_str = " ".join(str(sym) for sym in m.symbols(shown=True))
        models.append(model_str)
        if m.cost:
            costs.append(m.cost)

        cost_str = f" [magenta](Cost: {m.cost[0]})[/magenta]" if m.cost else ""
        progress.update(task_id, description=f"[cyan]Solving... [green]Found solution #{len(models)}{cost_str}[/green]")

        if live and hasattr(on_model, 'live_ctx'):
            schedule, fest_sched = parse_schedule(model_str)
            cost_val = m.cost[0] if m.cost else None
            renderables = generate_output_tables(schedule, year, cost_value=cost_val, is_live=True, festivo_schedule=fest_sched, festivities_dict=festivities_dict, pharmacies_list=pharmacies_list)
            on_model.live_ctx.update(Group(*renderables, progress))

    with Live(Group(progress), console=console, refresh_per_second=10, transient=True) as live_ctx:
        on_model.live_ctx = live_ctx
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

    return output, len(models)

@app.command()
def main(
    base: Annotated[str, typer.Option(help="The base encoding to use")] = "choice",
    opt: Annotated[str, typer.Option(help="The optimization strategy to use")] = "penalita_esponenziale",
    time_limit: Annotated[Optional[int], typer.Option(help="Time limit for the solver in seconds")] = None,
    live: Annotated[bool, typer.Option(help="Print live the latest found solution as it is discovered")] = False,
    csv_file: Annotated[Optional[str], typer.Option("--csv", help="Generate a CSV report to the specified file")] = None,
    csv_mode: Annotated[str, typer.Option(help="CSV mode: compact (full cols), normal, tiny (condensed col), extended")] = "normal",
    csv_direction: Annotated[str, typer.Option(help="CSV direction: column, row")] = "column",
    csv_map_pharmacies: Annotated[Optional[str], typer.Option(help="Pharmacy name mapping (e.g. '1,BUCCARELLI;2,SANMICHELE')")] = None,
    first_day_of_week: Annotated[str, typer.Option("--first-day-of-the-week", "--fdotw", help="First day of the week (monday, saturday, sunday, 0..6)")] = "monday",
    reschedule_csv: Annotated[Optional[str], typer.Option(help="Path to the CSV file of a previous run")] = None,
    reschedule_from: Annotated[Optional[str], typer.Option(help="Week number from which to reschedule (number or 'now')")] = None,
    festivities: Annotated[Optional[List[str]], typer.Option(help="Custom festivities in format 'name,start_date,finish_date' or 'name,date'")] = None,
    auto_festivities: Annotated[bool, typer.Option(help="Automatically generate Italian national festivities for the year")] = False,
    prev_year: Annotated[Optional[str], typer.Option(help="Path to previous year's CSV schedule")] = None,
    year: Annotated[int, typer.Option(help="L'anno per cui si vuole generare il calendario")] = 2025,
    start_week: Annotated[str, typer.Option(help="Settimana di inizio per la schedulazione (numero o 'now')")] = "1",
    end_week: Annotated[Optional[str], typer.Option(help="Settimana di fine per la schedulazione (numero o 'now')")] = None,
    pharmacies: Annotated[Optional[str], typer.Option(help="Elenco farmacie 'id,zona;...' o file .txt. Es: '1,centro; 2,marina'")] = None,
    force_open: Annotated[Optional[List[str]], typer.Option(help="Forza l'apertura (Strong constraint). Singola, lista con ';' (es. '1,15; 2,16') o file")] = None,
    force_closed: Annotated[Optional[List[str]], typer.Option(help="Forza la chiusura (Strong constraint). Singola, lista con ';' (es. '1,15') o file")] = None,
    pref_open: Annotated[Optional[List[str]], typer.Option(help="Preferisce l'apertura (Weak constraint). Singola, lista con ';' (es. '1,15') o file")] = None,
    pref_closed: Annotated[Optional[List[str]], typer.Option(help="Preferisce la chiusura (Weak constraint). Singola, lista con ';' (es. '1,15') o file")] = None,
    solver: Annotated[SolverType, typer.Option(help="Solver to use")] = SolverType.clingo
):
    optimizations = ASP_DIR / "optimizations"
    if not optimizations.exists():
        console.print(f"[red]Optimizations directory '{optimizations}' not found.[/red]")
        sys.exit(1)
    
    csv_dir = SCHEDULES_DIR
    if csv_file and not os.path.dirname(csv_file):
        csv_file = str(csv_dir / csv_file)
    if reschedule_csv and not os.path.dirname(reschedule_csv):
        reschedule_csv = str(csv_dir / reschedule_csv)
    if prev_year and not os.path.dirname(prev_year):
        prev_year = str(csv_dir / prev_year)

    domain_file = str(ASP_DIR / "domain.lp")
    guess_file = str(ASP_DIR / f"guess_{base}.lp")
    constraints_file = str(ASP_DIR / "constraints.lp")
    opt_file = str(ASP_DIR / "optimizations" / f"{opt}.lp")

    for f in [domain_file, guess_file, constraints_file, opt_file]:
        if not os.path.exists(f):
            console.print(f"[red]File '{f}' not found.[/red]")
            sys.exit(1)

    if reschedule_from and not reschedule_csv:
        console.print("[red]--reschedule-from requires --reschedule-csv[/red]")
        raise typer.Exit(code=1)

    total_weeks = date(year, 12, 28).isocalendar()[1]

    from core.runner_core import parse_week_param
    start_week_num = parse_week_param(start_week, year, first_day_of_week) or 1
    final_end_week = parse_week_param(end_week, year, first_day_of_week) or total_weeks
    reschedule_from_num = parse_week_param(reschedule_from, year, first_day_of_week)

    if reschedule_csv:
        if reschedule_from_num is None:
            if start_week_num > 1:
                reschedule_from_num = start_week_num
            else:
                reschedule_from_num = 1
    
    if start_week_num > total_weeks:
        console.print(f"[red]Error: --start-week {start_week_num} is greater than the total number of weeks in year {year} ({total_weeks}).[/red]")
        raise typer.Exit(code=1)
        
    if start_week_num > final_end_week:
        console.print(f"[red]Error: --start-week {start_week_num} cannot be greater than --end-week {final_end_week}.[/red]")
        raise typer.Exit(code=1)

    # Estrapoliamo gli ID delle farmacie esclusivamente per la visualizzazione nelle statistiche (UI)
    pharmacies_str = pharmacies
    if not pharmacies_str:
        pharmacies_str = ";".join([f"{i},{'marina' if i%2==0 else 'centro'}" for i in range(1, 11)])

    if pharmacies_str and (os.path.isfile(pharmacies_str) or pharmacies_str.endswith(".txt") or pharmacies_str.endswith(".csv")):
        try:
            with open(pharmacies_str, "r", encoding="utf-8") as f:
                pharmacies_str = f.read().strip()
        except Exception:
            pass # Ignoriamo eventuali errori. Se ne occuperà log/gestione nel core.

    pharmacies_list = None
    if pharmacies_str:
        try:
            parsed_ids = []
            for p in pharmacies_str.split(';'):
                p = p.strip()
                if p:
                    parts = p.split(',')
                    parsed_ids.append(int(parts[0].strip()))
            pharmacies_list = sorted(list(set(parsed_ids)))
        except Exception:
            pass # In caso di errori strani lascerà None, il fallback farà range(1, 11)

    festivities_dict = parse_festivities(festivities, auto_festivities, year)

    dynamic_file = None
    try:
        # Chiamata pulita e diretta al core passando i parametri in chiaro
        dynamic_file = generate_dynamic_constraints(
            reschedule_csv=reschedule_csv,
            reschedule_from=reschedule_from_num,
            start_week=start_week_num,
            end_week=final_end_week,
            festivities_dict=festivities_dict,
            prev_year_csv=prev_year,
            first_day_of_week=first_day_of_week,
            year=year,
            pharmacies=pharmacies,
            force_open=force_open,
            force_closed=force_closed,
            pref_open=pref_open,
            pref_closed=pref_closed
        )

        start_time = time.time()
        if solver == SolverType.clingo:
            asp_output, num_solutions = run_rich_clingo(
                domain_file, guess_file, constraints_file, opt_file,
                dynamic_file=dynamic_file, live=live, time_limit=time_limit, year=year,
                festivities_dict=festivities_dict, pharmacies_list=pharmacies_list
            )
        elif solver == SolverType.dlv2:
            asp_output, num_solutions = run_external_solver("dlv2", domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=live, time_limit=time_limit)
        elif solver == SolverType.dlv:
            asp_output, num_solutions = run_external_solver("dlv", domain_file, guess_file, constraints_file, opt_file, dynamic_file=dynamic_file, live=live, time_limit=time_limit)

        elapsed_time = time.time() - start_time

        schedule, festivo_schedule = parse_schedule(asp_output)
        
        if not schedule:
            console.print("[red]No schedule could be parsed from the output.[/red]")
            raise typer.Exit(code=1)

        import re
        cost_match = re.search(r"COST\s+(\d+)@\d+", asp_output, re.IGNORECASE)
        cost_value = int(cost_match.group(1)) if cost_match else None

        renderables = generate_output_tables(schedule, year, cost_value=cost_value, elapsed_time=elapsed_time, festivo_schedule=festivo_schedule, festivities_dict=festivities_dict, pharmacies_list=pharmacies_list)
        
        if num_solutions is not None:
            renderables.append(Text.from_markup(f"\n[cyan]✓ Solved![/cyan] [green]Found {num_solutions} solutions.[/green]"))
            
        for r in renderables:
            console.print(r)

        if csv_file:
            run_info = {
                'solver': solver.value,
                'base': base,
                'opt': opt,
                'time': elapsed_time
            }
            if os.path.dirname(csv_file):
                os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            generate_csv_report(
                schedule, csv_file, run_info, year, festivo_schedule=festivo_schedule, festivities_dict=festivities_dict,
                csv_mode=csv_mode, csv_direction=csv_direction, csv_map_pharmacies=csv_map_pharmacies,
                first_day_of_week=first_day_of_week
            )

    finally:
        if dynamic_file and os.path.exists(dynamic_file):
            os.remove(dynamic_file)

if __name__ == "__main__":
    app()