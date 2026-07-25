# Specifiche Tecniche & Generazione Dinamica di Codice ASP

Questo documento fornisce le specifiche tecniche dettagliate di come il runner Python pre-processa i requisiti di schedulazione, genera dinamicamente codice Answer Set Programming (ASP), invoca i solver ASP (Clingo, DLV, DLV2) e converte i risultati in calendari e report CSV.

---

## 1. Architettura Generale

Il sistema di turnazione delle farmacie utilizza un'architettura ibrida:
- **Livello di Gestione Python (`runner.py`, `rich_runner.py`, `runner_core.py`, `terminal_display.py`)**: Gestisce il parsing degli argomenti da riga di comando, l'aritmetica delle date, il calcolo delle festività, l'analisi dello storico CSV, la generazione dinamica di regole ASP, l'invocazione dei solver e la formattazione dei report.
- **Livello Logico ASP (`asp/domain.lp`, `asp/guess_*.lp`, `asp/constraints.lp`, `asp/optimizations/*.lp`)**: Responsabile della definizione dello spazio di ricerca, del soddisfacimento dei vincoli e dell'ottimizzazione.

```
+-------------------------------------------------------+
|                Livello Runner Python                  |
|  - Parse dei flag (--auto-festivities, --prev-year)   |
|  - Calcolo date e numeri di settimana                 |
|  - Lettura file CSV precedenti                        |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|     Generazione Dinamica Codice ASP (`runner_core.py`)|
|  - Scrittura file .lp temporaneo con fatti e regole   |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                   Livello Solver ASP                  |
|  - Caricamento file ASP statici + file .lp temporaneo |
|  - Grounding & Solving via Clingo / DLV / DLV2        |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|             Post-Processing & Esportazione CSV        |
|  - Parsing turno/2 e turno_festivo/2                  |
|  - Segmentazione settimane in righe con Festività     |
+-------------------------------------------------------+
```

---

## 2. Generazione Dinamica del Codice ASP

Quando viene eseguito `runner.py` o `rich_runner.py`, la funzione `generate_dynamic_constraints()` in `runner_core.py` crea un file ASP temporaneo (`.lp`) tramite `tempfile.mkstemp()`. Questo file viene caricato insieme ai file `.lp` statici e viene eliminato automaticamente nel blocco `finally` al termine dell'esecuzione del solver.

### 2.1 Limiti della Schedulazione (`settimana`)
Python calcola l'intervallo di settimane attive (`start_week` .. `end_week`):
```asp
settimana(1..52).
```
Se viene specificato `--start-week 20` senza rischedulazione, viene generato `settimana(20..52).`, limitando l'orizzonte del solver a tale intervallo.

---

### 2.2 Rischedulazione e Blocco dello Storico

Quando vengono forniti `--reschedule-csv <file>` e `--reschedule-from <SETTIMANA>`:
1. Python legge `<file>` ed estrae i turni delle settimane precedenti a `<SETTIMANA>`.
2. Genera i fatti `past_turno(Settimana, Farmacia).`.
3. Genera i vincoli di blocco:

```asp
reschedule_from(20).

% Blocco dei turni settimanali ordinari passati
past_turno(1, 1).
past_turno(1, 3).
% ...

:- past_turno(S, F), not turno(S, F).
:- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).
```

---

### 2.3 Vincoli di Indisponibilità

Quando vengono passati `--unavailable <F,W>` o `--unavailable-interval <F,W1,W2>`:
```asp
% Da --unavailable 1,22
:- turno(22, 1).

% Da --unavailable-interval 3,22,28
:- turno(S, 3), S >= 22, S <= 28.
```

---

### 2.4 Generazione delle Festività (`festivita`, `past_festivita`)

Quando viene abilitato `--auto-festivities` o `--festivities`:

1. **Mappatura Date-Settimana**:
   Python calcola le date esatte delle festività italiane dell'anno (es. Capodanno, Pasquetta, Liberazione, Natale, ecc.) o converte le date personalizzate fornite dall'utente.
2. **Esclusione dei Fine Settimana**:
   - Le festività che cadono di sabato o domenica **non** attivano i fatti festività in ASP (sono coperte dal normale turno del weekend senza controlli sullo storico dell'anno precedente). Python ne registra il nome ai soli fini dell'etichettatura nel CSV.
   - Le festività che cadono dal lunedì al venerdì attivano un fatto festività in ASP senza spezzare la settimana né scambiare le farmacie.
3. **Fatti Dinamici ASP**:
   Per ogni festività infrasettimanale, Python genera:
   ```asp
   festivita("natale", 52).
   ```
4. **Continuità Storica (`--prev-year`)**:
   Quando viene specificato `--prev-year <file_csv>`, Python analizza i turni festivi dell'anno precedente e genera i fatti storici:
   ```asp
   past_festivita("natale", 3). % La farmacia 3 ha fatto Natale l'anno scorso
   ```
   Il vincolo in `asp/constraints.lp` impedisce alla stessa farmacia di essere assegnata al turno settimanale di quella festività:
   ```asp
   :- festivita(N, S), turno(S, F), past_festivita(N, F).
   ```

---

## 3. Interazione con i Solver ASP e Direttive

### 3.1 Direttive di Output
I file di guess (`asp/guess_choice.lp` e `asp/guess_or.lp`) contengono le direttive di output per garantire che Clingo/DLV restituiscano i simboli desiderati:
```asp
#show turno/2.
```

### 3.2 Regole di Vincolo ASP (`asp/constraints.lp`)
Il file dei vincoli statici applica le regole per i turni settimanali e il controllo storico delle festività:

```asp
% Vincoli dei turni settimanali ordinari
:- settimana(S), #count{F : turno(S, F)} < 2.
:- turno(S, F), turno(S+1, F), settimana(S).
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1.
:- settimana(S), inverno(S), #count { F : turno(S, F), zona(F, centro) } < 1.
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2.

% Vincolo di Continuità Storica per le Festività
:- festivita(N, S), turno(S, F), past_festivita(N, F).
```

---

## 4. Post-Processing ed Esportazione CSV

Dopo che il solver restituisce un answer set:

1. **Parsing dei Simboli (`parse_schedule`)**:
   - `turno(Settimana, Farmacia)` -> salvato in `schedule[Settimana]`
2. **Prima Riga con Intestazione Metadati**:
   - Scrive `# Metadata: Year=... | Solver=... | Time=... | Mode=... | Direction=... | Mappings=...` sulla prima riga del file CSV.
3. **Generazione Report CSV Flessibile (`csv_utils.generate_csv_report`)**:
   - Supporta `--csv-mode`:
     - `compact`: 1 riga per settimana (senza spezzare le festività) con colonne farmacia complete (`F1`..`F10` o nomi mappati).
     - `tiny`: 1 riga per settimana con colonna sintetica (`Farmacie di Turno`).
     - `normal`: Giorni consecutivi raggruppati, spezzando le righe nei giorni festivi.
     - `extended`: 365/366 righe giornaliere con giorno della settimana (L..D) e festività.
   - Supporta `--csv-direction`:
     - `column`: Layout verticale (righe dall'alto verso il basso).
     - `row`: Griglia orizzontale a 12 mesi affiancati con 4 colonne per mese (`Giorno`, `Lu-Do`, `Festività`, `Farmacie di Turno`).
   - Supporta `--first-day-of-the-week` (`--fdotw`): Configura il giorno di inizio del turno settimanale (`monday`, `saturday`, `sunday`, oppure `0..6`).
   - Supporta `--csv-map-pharmacies`: Mappa gli ID numerici delle farmacie con nomi personalizzati (es. `1` -> `BUCCARELLI`).
4. **Strumenti di Validazione e Confronto**:
   - `validate_csv.py`: Valida i calendari CSV rispetto a tutte le regole ASP.
   - `compare_csv.py`: Confronta affiancati due file di calendario CSV.
