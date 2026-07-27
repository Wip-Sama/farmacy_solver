# Manuale Utente - Interfaccia Web Turnazione Farmacie

Questo manuale descrive l'utilizzo dell'interfaccia grafica web (`frontend/`) per la gestione e generazione dei calendari di turnazione delle farmacie.

---

## 1. Struttura dell'Interfaccia

L'interfaccia grafica si compone di tre sezioni principali:

1. **Pannello Controlli Superiore (`TopControls`):**
   * **Anno (`Year`):** Seleziona l'anno di schedulazione (es. 2026).
   * **Usa anno precedente (`Use previous year`):** Interruttore (switch) per estrarre lo storico festività dall'anno precedente.
   * **Primo giorno della settimana (`First day of week`):** Menu a tendina per impostare l'inizio della settimana (Sunday / Monday).
   * **Festività automatiche (`Auto festivities`):** Interruttore per attivare o disattivare il calcolo automatico delle festività nazionali italiane (compresa la Pasquetta).
   * **Tempo limite (`Time Limit`):** Imposta il tempo massimo in secondi per il solver ASP Clingo (default: 60s).
   * **Rigenera da (`Regenerate from`):** Seleziona la data o settimana da cui effettuare il ricalcolo parziale.

2. **Tabelle Interattive di Configurazione:**
   * **Tabella Festività (`Festivities`):** Quando le festività automatiche sono disattivate (o per aggiungere date custom), permette l'inserimento manuale del Nome festività e della Data tramite selettore di calendario.
   * **Tabella Preferenze (`Preferences`):** Permette di impostare preferenze o chiusure per specifiche farmacie (F1, F2, F3...) in date selezionate.

3. **Pannello Calendario & Esportazione (`ScheduleView`):**
   * **Vista Compatta vs Estesa:** Selettore per passare dalla vista settimanale riassuntiva (1 riga per settimana) alla vista estesa giornaliera con colonne dettagliate per ogni farmacia.
   * **Evidenziazione Temporale:** Le settimane passate appaiono sfuocate/grigie, la settimana corrente è evidenziata con bordo verde brillante, e le prossime settimane con bordo ciano.
   * **Pulsanti di Esportazione:** Scarica il calendario in formato CSV o immagine PNG.

---

## 2. Generazione e Sincronizzazione in Tempo Reale

* **Nessun Polling:** L'interfaccia si connette tramite WebSocket al backend FastAPI. Eventuali modifiche effettuate su una scheda del browser vengono sincronizzate **all'istante** su tutte le altre schede aperte.
* **Blocco Concorrenza:** Quando si clicca su **Genera** o **Rigenera**, il backend blocca l'esecuzione simultanea di altri calcoli. I pulsanti vengono temporaneamente disabilitati su tutte le schede e viene mostrata una finestra di dialogo con i log in tempo reale del solver ASP (`Clingo`).
