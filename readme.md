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
