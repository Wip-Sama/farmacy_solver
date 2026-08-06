% -----------------------------------------
% 4. OTTIMIZZAZIONE (Weak Constraints - Penalità sulle differenze)
% -----------------------------------------

turni_totali(F, N) :- farmacia(F), N = #count { S : turno(S, F) }.

differenza(F1, F2, Diff) :- turni_totali(F1, N1), turni_totali(F2, N2), F1 < F2, N1 >= N2, Diff = N1 - N2.
differenza(F1, F2, Diff) :- turni_totali(F1, N1), turni_totali(F2, N2), F1 < F2, N1 < N2, Diff = N2 - N1.

% Penalizziamo le differenze a Livello 1, scalando il peso per renderlo significativo
:~ differenza(F1, F2, Diff). [Diff*100@1, F1, F2]