### Installazione e Configurazione

```shell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> DLV / DLV2 devono essere presenti nel PATH di sistema con `dlv.exe` e `dlv2.exe`. `clingo` è incluso in `requirements.txt`.

### Utilizzo

Runner standard:
```shell
python runner.py --time-limit 60
```

Runner con interfaccia Rich (indicatori di progresso interattivi e tabelle formattate):
```shell
python rich_runner.py --time-limit 60
```

### Configurazioni & Opzioni

| Opzione                               | Descrizione                                                                            |
| ------------------------------------- | -------------------------------------------------------------------------------------- |
| `--base choice`                       | Codifica Choice (predefinita)                                                          |
| `--base or`                           | Codifica OR                                                                            |
| `--opt penalita_esponenziale`         | Penalità esponenziale (predefinita)                                                    |
| `--opt differenza_turni`              | Differenza turni                                                                       |
| `--opt differenza_turni_con_penalita` | Differenza turni con penalità                                                          |
| `--dlv`                               | Solver DLV                                                                             |
| `--dlv2`                              | Solver DLV2                                                                            |
| `--clingo`                            | Solver Clingo (predefinito)                                                            |
| `--year`                              | Anno di destinazione (predefinito: 2025)                                               |
| `--start-week`                        | Settimana di inizio per la schedulazione                                               |
| `--end-week`                          | Settimana di fine per la schedulazione                                                 |
| `--time-limit`                        | Limite di tempo per il solver in secondi                                               |
| `--live`                              | Stampa in tempo reale le soluzioni man mano che vengono trovate                        |
| `--csv`                               | Genera un report CSV del calendario                                                    |
| `--auto-festivities`                  | Genera automaticamente le festività nazionali italiane per l'anno                      |
| `--festivities`                       | Festività personalizzate (`NOME,INIZIO,FINE` oppure `NOME,DATA`)                       |
| `--prev-year`                         | Percorso del CSV dell'anno precedente per evitare ripetizioni di festività consecutive |
| `--reschedule-csv`                    | File CSV di una schedulazione precedente per la rischedulazione                        |
| `--reschedule-from`                   | Numero di settimana da cui iniziare la rischedulazione                                 |
| `--unavailable`                       | Elenco delle farmacie indisponibili (es. `1,22`)                                       |
| `--unavailable-interval`              | Intervallo di indisponibilità (es. `3,22,28`)                                          |

### Gestione delle Festività

Quando viene abilitato `--auto-festivities` o `--festivities`:
- Le festività infrasettimanali (Lun-Ven) sostituiscono tutte le farmacie assegnate per quel giorno con un insieme completamente disgiunto di farmacie.
- Le festività che cadono nei fine settimana mantengono il turno normale aggiungendo l'etichetta della festività.
- `--prev-year` impedisce a qualsiasi farmacia di coprire la stessa festività per due anni consecutivi.
- Il report CSV spezza le settimane che contengono festività infrasettimanali e popola la colonna `Festività`.

```shell
# Esecuzione con festività italiane automatiche e salvataggio in CSV
python rich_runner.py --year 2025 --auto-festivities --csv schedule_2025.csv --time-limit 60

# Esecuzione per il 2026 utilizzando la schedulazione 2025 per evitare festività ripetute
python rich_runner.py --year 2026 --auto-festivities --prev-year schedule_2025.csv --csv schedule_2026.csv
```

### Specifiche Tecniche

Per la documentazione dettagliata su come il runner Python genera dinamicamente codice ASP, fatti, regole e interagisce con i solver ASP, consulta [specification-it.md](file:///c:/Users/sgroo/Desktop/tt/specification-it.md).
