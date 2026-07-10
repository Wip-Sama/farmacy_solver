% -----------------------------------------
% 4. OTTIMIZZAZIONE (Weak Constraints - Penalità sulle differenze)
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
