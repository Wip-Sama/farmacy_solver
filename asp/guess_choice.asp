% -----------------------------------------
% 2. GENERAZIONE DELLE SOLUZIONI (Choice Rule)
% -----------------------------------------
% Per ogni settimana, scegliamo ESATTAMENTE 'L' farmacie (potatura alla radice dello spazio di ricerca).
% Questo sostituisce "turno | no_turno" e rende inutili i vincoli sul conteggio totale settimanale.
M { turno(S, F) : farmacia(F) } L :- settimana(S), min_farmacie_settimana(M), max_farmacie_settimana(L).

% -----------------------------------------
% 5. OUTPUT
% -----------------------------------------
#show turno/2.
