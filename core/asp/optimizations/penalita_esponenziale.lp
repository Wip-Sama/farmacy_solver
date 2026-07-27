% -----------------------------------------
% 4. OTTIMIZZAZIONE (Weak Constraints - Penalità esponenziale)
% -----------------------------------------

% 1. Calcoliamo quanti turni totali fa ogni farmacia (N)
turni_totali(F, N) :- farmacia(F), N = #count { S : turno(S, F) }.

% 2. Penalizziamo la farmacia assegnando un costo pari al cubo dei suoi turni (N * N)
:~ turni_totali(F, N). [N*N*N@1, F]
