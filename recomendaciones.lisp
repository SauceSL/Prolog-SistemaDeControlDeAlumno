(defun consejo-riesgo (riesgo)
  (cond
    ((string= riesgo "alto") '("URGENTE: Agenda una asesoria con tus profesores hoy mismo." "Pausa actividades extracurriculares esta semana."))
    ((string= riesgo "medio") '("Organiza un calendario de estudio." "Revisa tus apuntes diarios por 20 minutos."))
    ((string= riesgo "bajo") '("Sigue asi, tu ritmo es excelente." "Considera ayudar a un companero para repasar."))
    (t '("Sin datos de riesgo."))))

(defun consejo-perfil (perfil)
  (cond
    ((string= perfil "fantasma") '("Problema principal: Ausentismo. Debes volver a clases inmediatamente."))
    ((string= perfil "sobrecargado") '("Problema principal: Agotamiento. Intenta dormir 7-8 horas; estudiar cansado no sirve."))
    ((string= perfil "confiado") '("Problema principal: Exceso de confianza. Haz examenes de prueba para medir tu nivel real."))
    (t nil)))

(defun generar-plan (riesgo perfil)
  (let ((plan-riesgo (consejo-riesgo riesgo))
        (plan-perfil (consejo-perfil perfil)))
    (append plan-perfil plan-riesgo)))

(let ((riesgo (first *args*))
      (perfil (second *args*)))
  (format t "~{~a~^|~}" (generar-plan riesgo perfil))) 
