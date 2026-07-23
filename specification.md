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
3. If past festivity shifts exist, emits `past_turno_festivo(FestivityName, Farmacia).` facts.
4. Generates locking constraints:

```asp
reschedule_from(20).

% Lock past regular weekly shifts
past_turno(1, 1).
past_turno(1, 3).
% ...

:- past_turno(S, F), not turno(S, F).
:- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).

% Lock past festivity shifts
:- past_turno_festivo(N, F), not turno_festivo(N, F).
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

### 2.4 Festivities Generation (`festivita`, `turno_festivo`, `past_festivita`)

When `--auto-festivities` or `--festivities` is enabled:

1. **Date-to-Week Mapping**:
   Python calculates exact holiday dates for the year (e.g. Capodanno, Pasquetta, Liberazione, Natale, etc.) or parses user-provided custom dates.
2. **Weekend Exclusion**:
   - Holidays falling on Saturday or Sunday do **not** trigger mid-week pharmacy swaps (they are covered by normal weekend duty). Python records their name for CSV labeling only.
   - Holidays falling on Monday through Friday trigger a mid-week festivity assignment in ASP.
3. **Dynamic ASP Facts & Choice Rules**:
   For each mid-week festivity, Python emits:
   ```asp
   festivita("natale", 52).

   % Choice rule: guess festivity assignments for active mid-week festivities
   { turno_festivo(N, F) : farmacia(F) } :- festivita(N, S).
   ```
4. **Historical Continuity (`--prev-year`)**:
   When `--prev-year <csv_file>` is supplied, Python parses previous year festivity assignments and emits historical facts:
   ```asp
   past_festivita("natale", 3). % Pharmacy 3 worked Natale last year
   ```
   ASP constraint in `asp/constraints.lp` then prevents repetition:
   ```asp
   :- turno_festivo(N, F), past_festivita(N, F).
   ```

---

## 3. ASP Solver Interaction & Directives

### 3.1 Directives
The guess files (`asp/guess_choice.lp` and `asp/guess_or.lp`) contain output directives to ensure Clingo/DLV emit the required symbols:
```asp
#show turno/2.
#show turno_festivo/2.
```

### 3.2 ASP Constraint Rules (`asp/constraints.lp`)
The static constraint file enforces all domain rules for both regular weekly shifts and festivity shifts:

```asp
% Regular Weekly Shifts Constraints
:- settimana(S), #count{F : turno(S, F)} < 2.
:- turno(S, F), turno(S+1, F), settimana(S).
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1.
:- settimana(S), inverno(S), #count { F : turno(S, F), zona(F, centro) } < 1.
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2.

% Festivity Shifts Constraints
:- festivita(N, S), #count { F : turno(S, F) } = K, #count { F : turno_festivo(N, F) } != K.
:- festivita(N, S), turno_festivo(N, F), turno(S, F).
:- festivita(N, S), turno_festivo(N, F), turno(S-1, F), settimana(S-1).
:- festivita(N, S), turno_festivo(N, F), turno(S+1, F), settimana(S+1).
:- turno_festivo(N, F), past_festivita(N, F).
:- festivita(N, S), estate(S), #count { F : turno_festivo(N, F), zona(F, marina) } < 1.
:- festivita(N, S), inverno(S), #count { F : turno_festivo(N, F), zona(F, centro) } < 1.
:- festivita(N, S), turno_festivo(N, F1), turno_festivo(N, F2), zona(F1, marina), zona(F2, marina), F1 != F2.
```

---

## 4. Post-Processing & CSV Report Generation

After the solver returns a answer set:

1. **Symbol Parsing (`parse_schedule`)**:
   - `turno(Week, Farmacia)` -> stored in `schedule[Week]`
   - `turno_festivo(FestivityName, Farmacia)` -> stored in `festivo_schedule[FestivityName]`
2. **Date Segmentation & CSV Output (`generate_csv_report`)**:
   - For each week, Python evaluates each of the 7 days (Monday to Sunday).
   - If a day is a mid-week festivity, its pharmacies are retrieved from `festivo_schedule`.
   - If a day is a normal day or weekend festivity, its pharmacies are retrieved from `schedule[Week]`.
   - Contiguous days with identical pharmacy assignments and festivity labels are grouped into a single CSV row.
   - The `Festività` column is populated with the holiday name whenever applicable.
