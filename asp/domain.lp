% -----------------------------------------
% 1. DEFINIZIONE DEL DOMINIO E DEI FATTI
% -----------------------------------------

% Un anno è composto da 52 o 53 settimane (verrà generato dinamicamente)
% settimana(1..52).

% Le farmacie da far turnare sono 10, di cui 6 ubicate in zona centro e 4 in zona marina
farmacia(1..10).
zona(1..6, centro).
zona(7..10, marina).

% Definizione del periodo estivo (15 giugno - 15 settembre) e invernale (generati dinamicamente)
% estate(W_START..W_END).
% inverno(W) :- settimana(W), not estate(W).

% Fatti dinamici: numero minimo e massimo di farmacie che devono turnare ogni settimana
min_farmacie_settimana(1).
max_farmacie_settimana(4).