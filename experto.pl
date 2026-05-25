perfil(_NoEstudia, _EstudiaPoco, DuermePoco, _NoEntregaTareas, _ComprendeParcial, _NoComprende, _MuchasFaltas, _AlgunasFaltas, TrasladoLargo, MuchoCodigo, sobrecargado) :-
    DuermePoco == true,
    (TrasladoLargo == true ; MuchoCodigo == true).

perfil(_NoEstudia, _EstudiaPoco, _DuermePoco, NoEntregaTareas, _ComprendeParcial, _NoComprende, _MuchasFaltas, _AlgunasFaltas, _TrasladoLargo, MuchoCodigo, desconectado) :-
    MuchoCodigo == true, NoEntregaTareas == true.

perfil(NoEstudia, _EstudiaPoco, _DuermePoco, _NoEntregaTareas, _ComprendeParcial, _NoComprende, MuchasFaltas, _AlgunasFaltas, _TrasladoLargo, _MuchoCodigo, fantasma) :-
    MuchasFaltas == true, NoEstudia == true.

perfil(_NoEstudia, _EstudiaPoco, _DuermePoco, _NoEntregaTareas, _ComprendeParcial, _NoComprende, _MuchasFaltas, _AlgunasFaltas, _TrasladoLargo, _MuchoCodigo, regular).

diagnostico_completo(NoEstudia, EstudiaPoco, DuermePoco, NoEntregaTareas, ComprendeParcial, NoComprende, MuchasFaltas, AlgunasFaltas, TrasladoLargo, MuchoCodigo, Riesgo, Perfil) :-
    diagnosticar(NoEstudia, EstudiaPoco, DuermePoco, NoEntregaTareas, ComprendeParcial, NoComprende, MuchasFaltas, AlgunasFaltas, Riesgo),
    perfil(NoEstudia, EstudiaPoco, DuermePoco, NoEntregaTareas, ComprendeParcial, NoComprende, MuchasFaltas, AlgunasFaltas, TrasladoLargo, MuchoCodigo, Perfil),
    !.