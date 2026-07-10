% -----------------------------------------
% 4. OTTIMIZZAZIONE (Weak Constraints - Penalità esponenziale) DLV Variant
% -----------------------------------------

numero_turni(N) :- #int(N), N >= 0, N <= 52.

% 1. Calcoliamo quanti turni totali fa ogni farmacia (N)
turni_totali(F, N) :- farmacia(F), numero_turni(N), N = #count { S : turno(S, F) }.

% 2. Penalizziamo la farmacia assegnando un costo pari al quadrato dei suoi turni (N * N)
:~ turni_totali(F, N). [N*N:1]
