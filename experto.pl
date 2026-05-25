% --- REGLAS DE RIESGO ALTO ---
riesgo_alto(true, _, _, true, _, _, true, _). % No estudia, no tareas, muchas faltas
riesgo_alto(true, _, true, _, _, true, _, _). % No estudia, duerme poco, no comprende

% --- REGLAS DE RIESGO MEDIO ---
% Basta con fallar en una de estas para caer en riesgo medio
riesgo_medio(_, true, _, _, _, _, _, _). % Estudia poco
riesgo_medio(_, _, true, _, _, _, _, _). % Duerme poco
riesgo_medio(_, _, _, _, true, _, _, _). % Comprende parcial
riesgo_medio(_, _, _, _, _, _, _, true). % Algunas faltas

% --- DIAGNOSTICAR RIESGO ---
diagnosticar(NoE, EstP, DuerP, NoEntT, CompP, NoComp, MuchF, AlgF, alto) :-
    riesgo_alto(NoE, EstP, DuerP, NoEntT, CompP, NoComp, MuchF, AlgF), !.

diagnosticar(NoE, EstP, DuerP, NoEntT, CompP, NoComp, MuchF, AlgF, medio) :-
    riesgo_medio(NoE, EstP, DuerP, NoEntT, CompP, NoComp, MuchF, AlgF), !.

diagnosticar(_, _, _, _, _, _, _, _, bajo).

% --- PERFILES ---
perfil(_, _, true, _, _, _, _, _, true, _, sobrecargado) :- !.
perfil(_, _, true, _, _, _, _, _, _, true, sobrecargado) :- !.
perfil(_, _, _, true, _, _, _, _, _, true, desconectado) :- !.
perfil(true, _, _, _, _, _, true, _, _, _, fantasma) :- !.
perfil(_, _, _, _, _, _, _, _, _, _, regular).

% --- EJECUCIÓN PRINCIPAL ---
diagnostico_completo(NoE, EstP, DuerP, NoEntT, CompP, NoComp, MuchF, AlgF, TrasL, MuchC, Riesgo, Perfil) :-
    diagnosticar(NoE, EstP, DuerP, NoEntT, CompP, NoComp, MuchF, AlgF, Riesgo),
    perfil(NoE, EstP, DuerP, NoEntT, CompP, NoComp, MuchF, AlgF, TrasL, MuchC, Perfil).