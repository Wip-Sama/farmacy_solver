### Setup

```shell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> DLV / DLV2 needs to be on the system path with dlv.exe and dlv2.exe, clingo is included in the requirements.txt

### Usage

Standard runner:
```shell
python runner.py --time-limit 60
```

Rich UI runner (with interactive progress indicators and formatted tables):
```shell
python rich_runner.py --time-limit 60
```

### Configurations & Options

| Option                                | Description                                                             |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `--base choice`                       | Choice encoding (default)                                               |
| `--base or`                           | OR encoding                                                             |
| `--opt penalita_esponenziale`         | Penalità esponenziale (default)                                         |
| `--opt differenza_turni`              | Differenza turni                                                        |
| `--opt differenza_turni_con_penalita` | Differenza turni con penalità                                           |
| `--dlv`                               | DLV solver                                                              |
| `--dlv2`                              | DLV2 solver                                                             |
| `--clingo`                            | Clingo solver (default)                                                 |
| `--year`                              | Target year (default: 2025)                                             |
| `--start-week`                        | Start scheduling from week (int or `now`)                               |
| `--end-week`                          | End scheduling at week (int or `now`)                                 |
| `--time-limit`                        | Time limit for solver in seconds                                        |
| `--pharmacies`                        | Custom pharmacy list with zones (e.g. `1,centro;2,marina`)              |
| `--live`                              | Print live latest found solutions as discovered                         |
| `--csv`                               | Generate a CSV report of the schedule                                   |
| `--csv-mode`                          | CSV mode: `compact` (1 row/week, full cols), `normal` (segmented), `tiny` (1 row/week, condensed col), `extended` (daily) |
| `--csv-direction`                     | CSV direction: `column` (top-to-bottom), `row` (12-month horizontal grid)|
| `--csv-map-pharmacies`                | Map pharmacy IDs to custom names (e.g. `1,BUCCARELLI;2,SANMICHELE` or file)|
| `--first-day-of-the-week` / `--fdotw`  | Set first day of the week (`monday`, `saturday`, `sunday`, or `0..6`)    |
| `--auto-festivities`                  | Auto-generate national Italian festivities for the year                 |
| `--festivities`                       | Custom festivities (`NAME,START,FINISH` or `NAME,DATE`)                 |
| `--prev-year`                         | Path to previous year CSV to prevent consecutive-year festivity repeats |
| `--reschedule-csv`                    | CSV file of previous run for rescheduling                               |
| `--reschedule-from`                   | Week number from which to reschedule                                    |
| `--force-open`                        | Force a pharmacy to be open in a given week (e.g. `1,22`)               |
| `--force-closed`                      | Force a pharmacy to be closed in a given week (e.g. `1,22`)             |
| `--pref-open`                         | Prefer a pharmacy to be open in a given week (e.g. `1,22`)              |
| `--pref-closed`                       | Prefer a pharmacy to be closed in a given week (e.g. `1,22`)            |

### Festivities & CSV Report Management

When `--auto-festivities` or `--festivities` is enabled:
- Mid-week festivities (Mon-Fri) retain the regular weekly shift without splitting the week or swapping pharmacies.
- Festivities falling on weekends keep the normal shift while adding the festivity label.
- `--prev-year` prevents any pharmacy from covering a mid-week festivity if they covered the same festivity the previous year.
- CSV output and week boundaries can be customized using:
  - `--first-day-of-the-week` (`--fdotw`): Specify start day of weekly shift (e.g. `saturday` for Saturday-Friday shift cycles).
  - `--csv-mode compact`: 1 row per week (no line breaks on festivities) with full pharmacy columns (`F1`..`F10` or mapped names).
  - `--csv-mode tiny`: 1 row per week with a single condensed pharmacy column (`Farmacie di Turno`).
  - `--csv-mode normal`: Weekly shift blocks broken on festivity days.
  - `--csv-mode extended`: 365/366 daily rows with full weekday and holiday annotations.
  - `--csv-direction row`: 12-month side-by-side calendar grid (4 columns per month: `Giorno`, `Lu-Do`, `Festività`, `Farmacie di Turno`).
  - `--csv-map-pharmacies`: Replaces numeric IDs (e.g. `F1`) with mapped names (e.g. `BUCCARELLI`).

### Utility Scripts

- **`validate_csv.py`**: Validates a generated CSV schedule against all core ASP business rules (Python inspection or Clingo `--asp` coherence solver):
  ```shell
  # Validate using Python rules inspection
  python validate_csv.py schedules/schedule_2026.csv --prev-year schedules/schedule_2025.csv

  # Validate using Clingo ASP solver coherence check
  python validate_csv.py schedules/schedule_2026.csv --asp --prev-year schedules/schedule_2025.csv
  ```
- **`compare_csv.py`**: Compares two CSV schedule files side-by-side (metadata diffs, weekly assignment diffs, pharmacy workload deltas):
  ```shell
  python compare_csv.py schedules/schedule_2025.csv schedules/schedule_2026.csv
  ```

```shell
# Run with automatic Italian holidays, horizontal 12-month grid layout, and mapped pharmacy names
python rich_runner.py --year 2025 --auto-festivities --csv schedule_2025.csv --csv-direction row --csv-map-pharmacies "1,BUCCARELLI;2,SANMICHELE"

# Run for 2026 using 2025 schedule to prevent repeating holidays
python rich_runner.py --year 2026 --auto-festivities --prev-year schedule_2025.csv --csv schedule_2026.csv
```

### Technical Specification

For detailed documentation on how the Python runner dynamically generates ASP code, facts, rules, and interacts with the ASP solvers, see [specification.md](file:///c:/Users/sgroo/Desktop/tt/specification.md).
