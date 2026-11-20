% -----------------------------------------
% 3. VINCOLI (Strong Constraints - Check)
% -----------------------------------------

% Criterio 1: ogni settimana deve avere almeno 2 farmacie
:- settimana(S), #count{F : turno(S, F)} < 2, not past_week(S).

% Criterio 2: nessuna farmacia lavorare 2 settimane consecutive
:- turno(S, F), turno(S+1, F), settimana(S), not past_week(S).

% Criterio 3: durante il periodo estivo, deve essere aperta almeno una farmacia della marina
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1, not past_week(S).

% Criterio 3.1: durante il periodo invernale, deve essere aperta almeno una farmacia al centro
% :- settimana(S), inverno(S), #count { F : turno(S, F), zona(F, centro) } < 1.

% Criterio 4: non possono turnare contemporaneamente 2 farmacie della marina, devono alternarsi.
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2, not past_week(S).

% -----------------------------------------
% 3.1. VINCOLI FESTIVITA'
% -----------------------------------------

% Criterio Festività (Continuità storica): Una farmacia non può svolgere la stessa festività 2 anni di fila
:- festivita(N, S), turno(S, F), past_festivita(N, F), not past_week(S).

