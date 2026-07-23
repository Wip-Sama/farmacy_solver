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
3. Se esistono turni festivi passati, genera i fatti `past_turno_festivo(NomeFestivita, Farmacia).`.
4. Genera i vincoli di blocco:

```asp
reschedule_from(20).

% Blocco dei turni settimanali ordinari passati
past_turno(1, 1).
past_turno(1, 3).
% ...

:- past_turno(S, F), not turno(S, F).
:- turno(S, F), S < START_WEEK, not past_turno(S, F), reschedule_from(START_WEEK).

% Blocco dei turni festivi passati
:- past_turno_festivo(N, F), not turno_festivo(N, F).
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

### 2.4 Generazione delle Festività (`festivita`, `turno_festivo`, `past_festivita`)

Quando viene abilitato `--auto-festivities` o `--festivities`:

1. **Mappatura Date-Settimana**:
   Python calcola le date esatte delle festività italiane dell'anno (es. Capodanno, Pasquetta, Liberazione, Natale, ecc.) o converte le date personalizzate fornite dall'utente.
2. **Esclusione dei Fine Settimana**:
   - Le festività che cadono di sabato o domenica **non** attivano lo swap delle farmacie (sono coperte dal normale turno del weekend). Python ne registra il nome ai soli fini dell'etichettatura nel CSV.
   - Le festività che cadono dal lunedì al venerdì attivano un turno festivo dedicato in ASP.
3. **Fatti Dinamici e Regole di Guess ASP**:
   Per ogni festività infrasettimanale, Python genera:
   ```asp
   festivita("natale", 52).

   % Regola di scelta: genera l'assegnazione per le festività infrasettimanali attive
   { turno_festivo(N, F) : farmacia(F) } :- festivita(N, S).
   ```
4. **Continuità Storica (`--prev-year`)**:
   Quando viene specificato `--prev-year <file_csv>`, Python analizza i turni festivi dell'anno precedente e genera i fatti storici:
   ```asp
   past_festivita("natale", 3). % La farmacia 3 ha fatto Natale l'anno scorso
   ```
   Il vincolo in `asp/constraints.lp` impedisce la ripetizione:
   ```asp
   :- turno_festivo(N, F), past_festivita(N, F).
   ```

---

## 3. Interazione con i Solver ASP e Direttive

### 3.1 Direttive di Output
I file di guess (`asp/guess_choice.lp` e `asp/guess_or.lp`) contengono le direttive di output per garantire che Clingo/DLV restituiscano i simboli desiderati:
```asp
#show turno/2.
#show turno_festivo/2.
```

### 3.2 Regole di Vincolo ASP (`asp/constraints.lp`)
Il file dei vincoli statici applica le regole sia ai turni settimanali ordinari sia ai turni festivi:

```asp
% Vincoli dei turni settimanali ordinari
:- settimana(S), #count{F : turno(S, F)} < 2.
:- turno(S, F), turno(S+1, F), settimana(S).
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1.
:- settimana(S), inverno(S), #count { F : turno(S, F), zona(F, centro) } < 1.
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2.

% Vincoli dei turni festivi
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

## 4. Post-Processing ed Esportazione CSV

Dopo che il solver restituisce un answer set:

1. **Parsing dei Simboli (`parse_schedule`)**:
   - `turno(Settimana, Farmacia)` -> salvato in `schedule[Settimana]`
   - `turno_festivo(NomeFestivita, Farmacia)` -> salvato in `festivo_schedule[NomeFestivita]`
2. **Segmentazione Date ed Esportazione CSV (`generate_csv_report`)**:
   - Per ogni settimana, Python valuta i 7 giorni (da Lunedì a Domenica).
   - Se un giorno è una festività infrasettimanale, le farmacie vengono recuperate da `festivo_schedule`.
   - Se un giorno è ordinario o una festività del weekend, le farmacie vengono recuperate da `schedule[Settimana]`.
   - I giorni consecutivi con identiche assegnazioni e festività vengono raggruppati in una singola riga del CSV.
   - La colonna `Festività` viene popolata con il nome della festività.
