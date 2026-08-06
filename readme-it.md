### Installazione e Configurazione

```shell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> DLV / DLV2 devono essere presenti nel PATH di sistema con `dlv.exe` e `dlv2.exe`. `clingo` è incluso in `requirements.txt`.

### Installazione tramite Docker e GitHub Container Registry (GHCR)

È possibile eseguire l'applicazione direttamente all'interno di un container scaricando l'immagine preconfigurata dal **GitHub Container Registry (GHCR)** oppure utilizzando Docker Compose.

#### Opzione 1: Scaricare ed eseguire l'immagine ufficiale da GitHub (Consigliato)

Tramite Docker Compose utilizzando il file di configurazione preconfigurato GHCR:

```shell
# Avvia l'applicazione con l'immagine precompilata da GitHub Container Registry
docker compose -f docker-compose.ghcr.yml up -d
```

Oppure direttamente via CLI Docker:

```shell
# Scarica l'ultima versione dell'immagine da GitHub Container Registry
docker pull ghcr.io/wip-sama/farmacy_solver:latest

# Avvia il container (espone l'interfaccia Web e le API REST sulla porta 8001)
docker run -d \
  --name pharmacy_solver_app \
  -p 8001:8001 \
  -v pharmacy_data:/app/data \
  ghcr.io/wip-sama/farmacy_solver:latest
```

Una volta avviato, l'interfaccia grafica Web sarà accessibile all'indirizzo `http://localhost:8001` e la documentazione API REST a `http://localhost:8001/docs`.

#### Opzione 2: Compilazione ed esecuzione locale con Docker Compose

```shell
# Compila ed avvia il container in locale con Docker Compose
docker compose up -d --build
```

In alternativa, puoi utilizzare gli script automatici dalla radice del progetto:
- **Windows (PowerShell):** `.\scripts\docker-run.ps1`
- **Linux / macOS (Bash):** `./scripts/docker-run.sh`

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
| `--pharmacies`                        | Elenco personalizzato farmacie con zone (es. `1,centro;2,marina`)                     |
| `--live`                              | Stampa in tempo reale le soluzioni man mano che vengono trovate                        |
| `--auto-festivities`                  | Genera automaticamente le festività nazionali italiane per l'anno                      |
| `--festivities`                       | Festività personalizzate (`NOME,INIZIO,FINE` oppure `NOME,DATA`)                       |
| `--prev-year`                         | Percorso del CSV dell'anno precedente per evitare ripetizioni di festività consecutive |
| `--csv`                               | Genera un report CSV del calendario                                                    |
| `--csv-mode`                          | Modalità CSV: `compact` (1 riga/settimana, colonne complete), `normal` (spezzato), `tiny` (1 riga/settimana, colonna sintetica), `extended` (giornaliero)|
| `--csv-direction`                     | Orientamento CSV: `column` (verticale dall'alto in basso), `row` (griglia 12 mesi orizzontale)|
| `--csv-map-pharmacies`                | Mappatura ID farmacie con nomi (es. `1,BUCCARELLI;2,SANMICHELE` oppure file)           |
| `--first-day-of-the-week` / `--fdotw`  | Giorno di inizio della settimana (`monday`, `saturday`, `sunday`, oppure `0..6`)       |
| `--year`                              | L'anno per cui si vuole generare il calendario (default: 2025)                         |
| `--start-week`                        | Settimana di inizio per la schedulazione (numero o `now`)                               |
| `--end-week`                          | Settimana di fine per la schedulazione (numero o `now`)                                 |
| `--reschedule-csv`                    | File CSV di una schedulazione precedente per la rischedulazione                         |
| `--reschedule-from`                   | Numero di settimana da cui iniziare la rischedulazione (numero o `now`)                  |
| `--force-open`                        | Forza una farmacia ad essere aperta in una data settimana (es. `1,22`)                |
| `--force-closed`                      | Forza una farmacia ad essere chiusa in una data settimana (es. `1,22`)                |
| `--pref-open`                         | Preferisce una farmacia aperta in una data settimana (es. `1,22`)                     |
| `--pref-closed`                       | Preferisce una farmacia chiusa in una data settimana (es. `1,22`)                     |

### Gestione delle Festività e Report CSV

Quando viene abilitato `--auto-festivities` o `--festivities`:
- Le festività infrasettimanali (Lun-Ven) mantengono il normale turno settimanale senza spezzare la settimana né scambiare le farmacie.
- Le festività che cadono nei fine settimana mantengono il turno normale aggiungendo l'etichetta della festività.
- `--prev-year` impedisce a qualsiasi farmacia di coprire una festività infrasettimanale se ha coperto la stessa festività l'anno precedente.
- L'esportazione CSV e il giorno di inizio del turno possono essere personalizzati con:
  - `--first-day-of-the-week` (`--fdotw`): Specifica il giorno di inizio del turno settimanale (es. `saturday` per turni che vanno da sabato a venerdì).
  - `--csv-mode compact`: 1 riga per settimana (senza spezzare le festività) con colonne farmacia complete (`F1`..`F10`).
  - `--csv-mode tiny`: 1 riga per settimana con colonna sintetica (`Farmacie di Turno`).
  - `--csv-mode normal`: Blocchi settimanali suddivisi nei giorni festivi.
  - `--csv-mode extended`: 365/366 righe giornaliere con giorni della settimana e festività.
  - `--csv-direction row`: Griglia orizzontale a 12 mesi (4 colonne per mese: `Giorno`, `Lu-Do`, `Festività`, `Farmacie di Turno`).
  - `--csv-map-pharmacies`: Sostituisce gli ID (es. `F1`) con i nomi personalizzati (es. `BUCCARELLI`).

### Script di Utilità

- **`validate_csv.py`**: Valida un calendario CSV generato rispetto a tutte le regole ASP (ispezione Python o verifica di coerenza Clingo `--asp`):
  ```shell
  # Valida utilizzando le regole di ispezione Python
  python validate_csv.py schedules/schedule_2026.csv --prev-year schedules/schedule_2025.csv

  # Valida utilizzando il solver ASP Clingo per verificare la coerenza
  python validate_csv.py schedules/schedule_2026.csv --asp --prev-year schedules/schedule_2025.csv
  ```
- **`compare_csv.py`**: Confronta affiancati due file di calendario CSV (differenze di metadati, turni settimanali, carico di lavoro):
  ```shell
  python compare_csv.py schedules/schedule_2025.csv schedules/schedule_2026.csv
  ```

```shell
# Esecuzione con festività italiane automatiche, griglia orizzontale 12 mesi e nomi farmacie personalizzati
python rich_runner.py --year 2025 --auto-festivities --csv schedule_2025.csv --csv-direction row --csv-map-pharmacies "1,BUCCARELLI;2,SANMICHELE"

# Esecuzione per il 2026 utilizzando la schedulazione 2025 per evitare festività ripetute
python rich_runner.py --year 2026 --auto-festivities --prev-year schedule_2025.csv --csv schedule_2026.csv
```

### Specifiche Tecniche

Per la documentazione dettagliata su come il runner Python genera dinamicamente codice ASP, fatti, regole e interagisce con i solver ASP, consulta [specification-it.md](file:///c:/Users/sgroo/Desktop/tt/specification-it.md).
