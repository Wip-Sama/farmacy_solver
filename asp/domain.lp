% -----------------------------------------
% 1. DEFINIZIONE DEL DOMINIO E DEI FATTI
% -----------------------------------------

% Un anno è composto da 52 o 53 settimane (verrà generato dinamicamente)
% settimana(1..52).

% Le farmacie da far turnare sono 10, di cui 6 ubicate in zona centro e 4 in zona marina
farmacia(1..10).
zona(1..6, centro).
zona(7..10, marina).

% Definizione del periodo estivo e festivi
estate(25..37).
inverno(38..52).
inverno(1..25).
festivo(1).
festivo(15).
festivo(16).
festivo(17).
festivo(22).
festivo(32).
festivo(43).
festivo(49).
festivo(51).

% Fatti dinamici: numero minimo e massimo di farmacie che devono turnare ogni settimana
min_farmacie_settimana(1).
max_farmacie_settimana(4).