### Setup

```shell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> DLV / DLV2 needs to be on the system path with dlv.exe and dlv2.exe, clingo is included in the requirements.txt

### Use

```shell
python runner.py
```

> Strongly suggest adding a time limit with --time [seconds]

```shell
python runner.py --time 60
```

### Configurations

| Base Encoding      | Optimization Strategy             | Solver              |
| ------------------ | --------------------------------- | ------------------- |
| `choice` (default) | `penalita_esponenziale` (default) | DLV / DLV2 / Clingo |

**Available Configurations:**

| Option                                | Description                     |
| ------------------------------------- | ------------------------------- |
| `--base choice`                       | Choice encoding (default)       |
| `--base or`                           | OR encoding                     |
| `--opt penalita_esponenziale`         | Penalità esponenziale (default) |
| `--opt differenza_turni`              | Differenza turni                |
| `--opt differenza_turni_con_penalita` | Differenza turni con penalità   |
| `--dlv`                               | DLV solver                      |
| `--dlv2`                              | DLV2 solver                     |
| `--clingo`                            | Clingo solver                   |
| `--year`                              | Target year                     |
| `--start-week`                        | Start scheduling from week      |
| `--end-week`                          | End scheduling at week          |

### CSV Report

Generate a CSV report of the schedule to the specified file:

```shell
python runner.py --csv schedule.csv
```

### Live Mode

Print live the latest found solution as it is discovered:

```shell
python runner.py --live
```

### Rescheduling & Constraints

You can reschedule shifts while keeping historical assignments fixed, and specify custom constraints for pharmacies:

```shell
# Reschedule from week 20, keeping weeks 1-19 fixed exactly as they are in original.csv
python runner.py --reschedule-csv original.csv --reschedule-from 20

# Force Farmacia 1 to be unavailable in week 22
python runner.py --unavailable 1,22

# Force Farmacia 3 to be unavailable from week 22 to 28
python runner.py --unavailable-interval 3,22,28

# Combine all of them
python runner.py --reschedule-csv original.csv --reschedule-from 20 --unavailable 1,22 --unavailable-interval 3,22,28
```

### Partial Year & Year-specific Scheduling

You can target a specific year for accurate dates (and automatic 53-week handling) or schedule only a partial slice of the year by ignoring previous unrequested weeks entirely:

```shell
# Schedule only weeks 50 through 52 for the default year
python runner.py --start-week 50

# Schedule only weeks 20 to 30 for the year 2026
python runner.py --year 2026 --start-week 20 --end-week 30
```

### Examples

**Solve with default configuration:**

```shell
python runner.py --time 60
```

**Use difference_turni_con_penalita optimization:**

```shell
python runner.py --opt differenza_turni_con_penalita --time 60
```

**Use DLV2 solver:**

```shell
python runner.py --dlv2 --time 60
```

**Generate CSV report with clingo solver:**

```shell
python runner.py --clingo --csv report.csv
```

**Combine multiple options:**

```shell
python runner.py --base or --opt differenza_turni --dlv2 --time 120 --csv full_report.csv
```
