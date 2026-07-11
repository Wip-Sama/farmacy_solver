% -----------------------------------------
% 3. VINCOLI (Hard Constraints - Check)
% -----------------------------------------

% Criterio 1: ogni settimana deve avere almeno 2 farmacie
:- settimana(S), #count{F : turno(S, F)} < 2.

% Criterio 2: nessuna farmacia deve espletare il turno per 2 settimane consecutive
:- turno(S, F), turno(S+1, F), settimana(S).

% Criterio 3: durante il periodo estivo, deve essere aperta almeno una farmacia della marina
:- settimana(S), estate(S), #count { F : turno(S, F), zona(F, marina) } < 1.

% Criterio 3.1: durante il periodo invernale, deve essere aperta almeno una farmacia al centro
:- settimana(S), inverno(S), #count { F : turno(S, F), zona(F, centro) } < 1.

% Criterio 4: non possono turnare contemporaneamente 2 farmacie della marina, ma devono alternarsi con quelle del centro.
:- turno(S, F1), turno(S, F2), zona(F1, marina), zona(F2, marina), F1 != F2.
