% -----------------------------------------
% 2. GENERAZIONE DELLE SOLUZIONI (Guess tramite OR / Disgiunzione)
% -----------------------------------------
% Per ogni settimana e ogni farmacia, questa è di turno (OR) non è di turno.
turno(S, F) | no_turno(S, F) :- settimana(S), farmacia(F).

% Criterio 0: Tagliamo via tutti gli scenari in cui le farmacie di turno non rispettano i limiti
:- settimana(S), min_farmacie_settimana(M), #count { F : turno(S, F) } < M.
:- settimana(S), max_farmacie_settimana(L), #count { F : turno(S, F) } > L.

% -----------------------------------------
% 5. OUTPUT
% -----------------------------------------
#show turno/2.
