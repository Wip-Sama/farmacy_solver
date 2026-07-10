% -----------------------------------------
% 1. DEFINIZIONE DEL DOMINIO E DEI FATTI
% -----------------------------------------
% Un anno è composto da 52 settimane
settimana(1..52).

% Le farmacie da far turnare sono 10, di cui 6 ubicate in zona centro e 4 in zona marina
farmacia(1..10).
zona(1..6, centro).
zona(7..10, marina).

% Definizione del periodo estivo (es. settimane dalla 24 alla 36, circa metà giugno - inizio settembre)
estate(24..36).
%estate(29..36).

max_farmacie_settimana(2).

% -----------------------------------------
% 2. GENERAZIONE DELLE SOLUZIONI (Guess)
% -----------------------------------------
% Per ogni settimana e ogni farmacia, questa è di turno o non lo è
turno(S, F) | no_turno(S, F) :- settimana(S), farmacia(F).

% -----------------------------------------
% 3. VINCOLI (Hard Constraints - Check)
% -----------------------------------------

% Criterio 1: ogni settimana devono turnare almeno 2 farmacie
:- settimana(S), #count { F : turno(S, F) } < 2.

% Criterio 2: nessuna farmacia deve espletare il turno per 2 settimane consecutive 
:- turno(S, F), turno(S+1, F), settimana(S).

% Criterio 3: durante il periodo estivo, deve essere aperta almeno una farmacia della marina 
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1.

% Criterio 4: non possono turnare contemporaneamente 2 farmacie della marina, ma devono alternarsi con quelle del centro 
% si potrebbe cambiare smeplicemente imponento che ci sia almeno una farmacia in centro
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2.

% -----------------------------------------
% 4. OTTIMIZZAZIONE (Weak Constraints)
% -----------------------------------------

% riduce lo spazio di ricerca
:- settimana(S), #count { F : turno(S, F) } > L, max_farmacie_settimana(L).

% -----------------------------------------
% 1. Costo Base: Ogni singolo turno costa 1.
% :~ turno(S, F). [1@1, S, F]

% 2. Costo Progressivo: Ogni volta che la stessa farmacia fa due turni diversi, aggiungiamo 1.
% La condizione S1 < S2 impedisce di contare la stessa coppia due volte o di incrociare lo stesso giorno.
%:~ turno(S1, F), turno(S2, F), S1 < S2. [1@1, S1, S2, F]

% -----------------------------------------
% 1. Calcoliamo quanti turni totali fa ogni farmacia (N)
%turni_totali(F, N) :- farmacia(F), N = #count { S : turno(S, F) }.

% 2. Penalizziamo la farmacia assegnando un costo pari al quadrato dei suoi turni (N * N)
%:~ turni_totali(F, N). [N*N@1, F]

% -----------------------------------------
% 1. Calcoliamo quanti turni totali fa ogni singola farmacia
turni_totali(F, N) :- farmacia(F), N = #count { S : turno(S, F) }.

% 2. Calcoliamo la differenza matematica tra ogni coppia possibile di farmacie (F1 e F2).
% Usiamo F1 < F2 per evitare di calcolare la stessa coppia due volte (es. 1-2 e 2-1).
% Caso A: la farmacia 1 ha fatto più turni (o uguali) della farmacia 2
differenza(F1, F2, Diff) :- turni_totali(F1, N1), turni_totali(F2, N2), F1 < F2, N1 >= N2, Diff = N1 - N2.

% Caso B: la farmacia 2 ha fatto più turni della farmacia 1
differenza(F1, F2, Diff) :- turni_totali(F1, N1), turni_totali(F2, N2), F1 < F2, N1 < N2, Diff = N2 - N1.

% 3. Weak Constraint: penalizziamo il solver in base a quanto è grande la differenza
:~ differenza(F1, F2, Diff). [Diff@1, F1, F2]

% -----------------------------------------
% 5. OUTPUT
% -----------------------------------------
#show turno/2.