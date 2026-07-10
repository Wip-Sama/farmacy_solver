% -----------------------------------------
% 1. DEFINIZIONE DEL DOMINIO E DEI FATTI
% -----------------------------------------
% Un anno è composto da 52 settimane
settimana(1..52).

% Le farmacie da far turnare sono 10, di cui 6 ubicate in zona centro e 4 in zona marina
farmacia(1..10).
zona(1..6, centro).
zona(7..10, marina).

% Definizione del periodo estivo (es. settimane dalla 24 alla 36)
estate(24..36).

% Fatti dinamici: numero minimo e massimo di farmacie che devono turnare ogni settimana
min_farmacie_settimana(2).
max_farmacie_settimana(4).

% -----------------------------------------
% 2. GENERAZIONE DELLE SOLUZIONI (Guess tramite OR / Disgiunzione)
% -----------------------------------------
% Per ogni settimana e ogni farmacia, questa è di turno (OR) non è di turno.
turno(S, F) | no_turno(S, F) :- settimana(S), farmacia(F).

% -----------------------------------------
% 3. VINCOLI (Hard Constraints - Check)
% -----------------------------------------

% Criterio 1: Tagliamo via tutti gli scenari in cui le farmacie di turno non rispettano i limiti
:- settimana(S), min_farmacie_settimana(M), #count { F : turno(S, F) } < M.
:- settimana(S), max_farmacie_settimana(L), #count { F : turno(S, F) } > L.

% Criterio 2: nessuna farmacia deve espletare il turno per 2 settimane consecutive 
:- turno(S, F), S1 = S + 1, turno(S1, F), settimana(S).

% Criterio 3: durante il periodo estivo, deve essere aperta almeno una farmacia della marina 
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1.

% Criterio 4: non possono turnare contemporaneamente 2 farmacie della marina, ma devono alternarsi con quelle del centro.
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2.

% -----------------------------------------
% 5. OUTPUT
% -----------------------------------------
#show turno/2.