% -----------------------------------------
% 3. VINCOLI (Strong Constraints - Check)
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

% -----------------------------------------
% 3.1. VINCOLI FESTIVITA'
% -----------------------------------------

% Criterio Festività 1: Il numero di farmacie assegnate alla festività deve essere identico al numero di farmacie previste per il turno settimanale di quella settimana
:- festivita(N, S), #count { F : turno(S, F) } = K, #count { F : turno_festivo(N, F) } != K.

% Criterio Festività 2: Durante la festività infrasettimanale si effettua lo swap completo delle farmacie: nessuna farmacia di turno nella settimana S può coprire il turno festivo della stessa settimana
:- festivita(N, S), turno_festivo(N, F), turno(S, F).

% Criterio Festività 3: Nessuna farmacia può coprire una festività nella settimana S se è già di turno nella settimana immediatamente precedente (S-1) o successiva (S+1)
:- festivita(N, S), turno_festivo(N, F), turno(S-1, F), settimana(S-1).
:- festivita(N, S), turno_festivo(N, F), turno(S+1, F), settimana(S+1).

% Criterio Festività 4 (Continuità storica): Una farmacia non può svolgere la stessa festività per due anni consecutivi (dati provenienti da --prev-year)
:- turno_festivo(N, F), past_festivita(N, F).

% Criterio Festività 5.1 (Copertura Zona Estiva): Durante il periodo estivo, per ogni festività deve essere aperta almeno una farmacia situata nella zona marina
:- festivita(N, S), estate(S), #count { F : turno_festivo(N, F), zona(F, marina) } < 1.

% Criterio Festività 5.2 (Copertura Zona Invernale): Durante il periodo invernale, per ogni festività deve essere aperta almeno una farmacia situata nella zona centro
:- festivita(N, S), inverno(S), #count { F : turno_festivo(N, F), zona(F, centro) } < 1.

% Criterio Festività 5.3 (Bilanciamento Zona): Durante una festività non possono essere contemporaneamente aperte due farmacie della zona marina (devono alternarsi con quelle del centro)
:- festivita(N, S), turno_festivo(N, F1), turno_festivo(N, F2), zona(F1, marina), zona(F2, marina), F1 != F2.

