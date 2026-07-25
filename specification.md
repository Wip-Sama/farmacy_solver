# Dynamic ASP Code Generation & Architecture Specification

This document provides a technical specification of how the Python runner pre-processes scheduling requirements, generates dynamic Answer Set Programming (ASP) code, invokes ASP solvers (Clingo, DLV, DLV2), and parses results into schedules and CSV reports.

---

## 1. Overview & Architecture

The pharmacy scheduling system uses a hybrid architecture:
- **Python Management Layer (`runner.py`, `rich_runner.py`, `runner_core.py`, `terminal_display.py`)**: Responsible for command-line argument parsing, date arithmetic, holiday calculations, CSV history processing, dynamic ASP rule generation, solver invocation, and report formatting.
- **ASP Logic Layer (`asp/domain.lp`, `asp/guess_*.lp`, `asp/constraints.lp`, `asp/optimizations/*.lp`)**: Responsible for declarative search space definition, constraint satisfaction, and optimization.

```
+-------------------------------------------------------+
|                 Python Runner Layer                   |
|  - Parse flags (--auto-festivities, --prev-year, etc) |
|  - Calculate dates & week numbers                     |
|  - Read previous CSV files                            |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|        Dynamic ASP Code Generation (`runner_core.py`) |
|  - Write temporary .lp file containing facts & rules  |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                   ASP Solver Layer                    |
|  - Load static ASP files + dynamic temporary .lp file |
|  - Ground & Solve via Clingo / DLV / DLV2             |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|             Post-Processing & CSV Export              |
|  - Parse turno/2 & turno_festivo/2                    |
|  - Segment weeks into date rows with Festività column |
+-------------------------------------------------------+
```

---

## 2. Dynamic ASP Code Generation

When `runner.py` or `rich_runner.py` is executed, `generate_dynamic_constraints()` in `runner_core.py` generates a temporary ASP file (`.lp`) using `tempfile.mkstemp()`. This temporary file is loaded alongside the static `.lp` files and is automatically deleted in a `finally` block when solver execution finishes.

### 2.1 Scheduling Bounds (`settimana`)
Python calculates the active scheduling week range (`start_week` to `end_week`):
```asp
settimana(1..52).
```
If `--start-week 20` is specified without rescheduling, `settimana(20..52).` is emitted, restricting the solver horizon to that range.

---

### 2.2 Rescheduling & Historical Lock Facts

When `--reschedule-csv <file>` and `--reschedule-from <WEEK>` are provided:
1. Python reads `<file>` and extracts past week assignments for weeks `< WEEK`.
2. Emits `past_turno(Week, Farmacia).` facts.
3. Generates locking constraints:

```asp
reschedule_from(20).

% Lock past regular weekly shifts
past_turno(1, 1).
past_turno(1, 3).
% ...

:- past_turno(S, F), not turno(S, F).
:- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).
```

---

### 2.3 Unavailability Constraints

When `--unavailable <F,W>` or `--unavailable-interval <F,W1,W2>` are passed:
```asp
% From --unavailable 1,22
:- turno(22, 1).

% From --unavailable-interval 3,22,28
:- turno(S, 3), S >= 22, S <= 28.
```

---

### 2.4 Festivities Generation (`festivita`, `past_festivita`)

When `--auto-festivities` or `--festivities` is enabled:

1. **Date-to-Week Mapping**:
   Python calculates exact holiday dates for the year (e.g. Capodanno, Pasquetta, Liberazione, Natale, etc.) or parses user-provided custom dates.
2. **Weekend Exclusion**:
   - Holidays falling on Saturday or Sunday do **not** trigger mid-week festivity facts (they are covered by normal weekend duty without previous year checks). Python records their name for CSV labeling only.
   - Holidays falling on Monday through Friday trigger a mid-week festivity fact in ASP without splitting the week or swapping pharmacies.
3. **Dynamic ASP Facts**:
   For each mid-week festivity, Python emits:
   ```asp
   festivita("natale", 52).
   ```
4. **Historical Continuity (`--prev-year`)**:
   When `--prev-year <csv_file>` is supplied, Python parses previous year festivity assignments and emits historical facts:
   ```asp
   past_festivita("natale", 3). % Pharmacy 3 worked Natale last year
   ```
   ASP constraint in `asp/constraints.lp` then prevents the same pharmacy from being assigned to the weekly shift of that festivity:
   ```asp
   :- festivita(N, S), turno(S, F), past_festivita(N, F).
   ```

---

## 3. ASP Solver Interaction & Directives

### 3.1 Directives
The guess files (`asp/guess_choice.lp` and `asp/guess_or.lp`) contain output directives to ensure Clingo/DLV emit the required symbols:
```asp
#show turno/2.
```

### 3.2 ASP Constraint Rules (`asp/constraints.lp`)
The static constraint file enforces all domain rules for regular weekly shifts and historical festivity checks:

```asp
% Regular Weekly Shifts Constraints
:- settimana(S), #count{F : turno(S, F)} < 2.
:- turno(S, F), turno(S+1, F), settimana(S).
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1.
:- settimana(S), inverno(S), #count { F : turno(S, F), zona(F, centro) } < 1.
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2.

% Festivity Continuity Constraint
:- festivita(N, S), turno(S, F), past_festivita(N, F).
```

---

## 4. Post-Processing & CSV Report Generation

After the solver returns an answer set:

1. **Symbol Parsing (`parse_schedule`)**:
   - `turno(Week, Farmacia)` -> stored in `schedule[Week]`
2. **Metadata Header First Row**:
   - Writes `# Metadata: Year=... | Solver=... | Time=... | Mode=... | Direction=... | Mappings=...` on the first row of the CSV file.
3. **Flexible CSV Output (`csv_utils.generate_csv_report`)**:
   - Supports `--csv-mode`:
     - `compact`: 1 row per week (no breaks on festivities) with full pharmacy columns (`F1`..`F10` or mapped names).
     - `tiny`: 1 row per week with a single condensed pharmacy column (`Farmacie di Turno`).
     - `normal`: Grouped consecutive days with identical assignments, breaking rows on festivity days.
     - `extended`: 365/366 daily rows with day of week (L..D) and holiday annotations.
   - Supports `--csv-direction`:
     - `column`: Vertical layout (rows top-to-bottom).
     - `row`: 12-month horizontal calendar grid (side-by-side) with 4 full columns per month (`Giorno`, `Lu-Do`, `Festività`, `Farmacie di Turno`).
   - Supports `--first-day-of-the-week` (`--fdotw`): Configures the weekly shift start day (`monday`, `saturday`, `sunday`, or `0..6`).
   - Supports `--csv-map-pharmacies`: Maps numeric pharmacy IDs to custom names (e.g. `1` -> `BUCCARELLI`).
4. **Validation & Comparison Tools**:
   - `validate_csv.py`: Validates CSV schedules against all ASP domain rules.
   - `compare_csv.py`: Compares two CSV schedule files side-by-side.
