# Report e Note Tecnice

> **Mi hanno bloccato TEAMS... Contatti:**  
> - **Email:** sgro.orlando@gmail.com  
> - **Telegram:** [@smastermega](https://t.me/smastermega)  

---

## 📝 Stato del Lavoro
Il report è stato completato alle **2:30 di notte** se notate errori contattatemi il prima possivile dato il breve intervallo di tempo a disposizione.

---

## Note Tecniche e Osservazioni

### 1. Risultati dei Test
* **UCS:** Non completa l'esecuzione nel tempo stabilito (*non so bene come funziona...*).
* **`parallel4`:** Risulta marginalmente migliore rispetto al setting di default.
  * **Nota:** Eseguire nuovamente il test in modalità **sequenziale** (senza altre applicazioni in background) potrebbe accentuare MARGINNALMENTE meglio le differenze.

### 2. Tempistiche di Esecuzione
> ⚠️ **ATTENZIONE:** Eseguire l'intero dataset in modalità sequenziale (1 elemento alla volta) richiede **ALMENO 2 ore / 2 ore e mezza** (o poco più), parallelizzando i vari timing di scadenza. Senza paralllelizzarli il tempo diventa facilmente **4 ore**.
---

## Livelli di Parallelizzazione

L'infrastruttura supporta **2 livelli di parallelizzazione** (che possono essere **combinati**):

1. `--parallel`
   * Esegue tutti i tempi in simultanea per una specifica data (es. *base 5, 15, 30, 60* tutti insieme).
   * Se si usa ad esempio `--parallel 4`, vengono impiegati 4 core per evitare rallentamenti.
   * *Requisito hardware ideale:* Processore con almeno **16 thread**.
   * *Note hardware test:* Il PC utilizzato dispone di **32 thread**, quindi non ha subito rallentamenti significativi.

2. `--parallel-profiles n`
   * Esegue `n` profili differenti di **Clingo** in simultanea.

---

## Timeout e Finestre Temporali

* **15s, 30s, 60s:** Rappresentano i tempi di benchmark principali.
* **5s:** Test di controllo per valutare le prestazioni del solver in un lasso di tempo **estremamente limitato**.

---

## Menzioni onorevoli

- **Grafici:** Sarebbe interessante plottare il miglioramento delle performance in funzione del tempo.
- **Generatore Dati:** Attualmente non ne sono particolarmente fiero, ma dato il tempo limitato a disposizione è discreto.
