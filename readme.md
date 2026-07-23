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
| `--start-week`                        | Start scheduling from week                                              |
| `--end-week`                          | End scheduling at week                                                  |
| `--time-limit`                        | Time limit for solver in seconds                                        |
| `--live`                              | Print live latest found solutions as discovered                         |
| `--csv`                               | Generate a CSV report of the schedule                                   |
| `--auto-festivities`                  | Auto-generate national Italian festivities for the year                 |
| `--festivities`                       | Custom festivities (`NAME,START,FINISH` or `NAME,DATE`)                 |
| `--prev-year`                         | Path to previous year CSV to prevent consecutive-year festivity repeats |
| `--reschedule-csv`                    | CSV file of previous run for rescheduling                               |
| `--reschedule-from`                   | Week number from which to reschedule                                    |
| `--unavailable`                       | List of unavailable pharmacies (e.g. `1,22`)                            |
| `--unavailable-interval`              | Interval of unavailability (e.g. `3,22,28`)                             |

### Festivities Management

When `--auto-festivities` or `--festivities` is enabled:
- Mid-week festivities (Mon-Fri) switch out all assigned pharmacies for the holiday with a completely disjoint set.
- Festivities falling on weekends keep the normal shift while adding the festivity label.
- `--prev-year` prevents any pharmacy from covering the same holiday two years in a row.
- The CSV report splits weeks containing mid-week festivities and populates the `Festività` column.

```shell
# Run with automatic Italian holidays and save to CSV
python rich_runner.py --year 2025 --auto-festivities --csv schedule_2025.csv --time-limit 60

# Run for 2026 using 2025 schedule to prevent repeating holidays
python rich_runner.py --year 2026 --auto-festivities --prev-year schedule_2025.csv --csv schedule_2026.csv
```

### Technical Specification

For detailed documentation on how the Python runner dynamically generates ASP code, facts, rules, and interacts with the ASP solvers, see [specification.md](file:///c:/Users/sgroo/Desktop/tt/specification.md).
