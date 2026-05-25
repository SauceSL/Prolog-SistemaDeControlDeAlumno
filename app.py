import os
import sqlite3
import subprocess
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE = DATA_DIR / "alumnos.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")


PREGUNTAS = [
    {
        "name": "estudio",
        "label": "¿Estudiaste para el examen?",
        "type": "select",
        "options": [("si", "Sí"), ("poco", "Poco"), ("no", "No")],
    },
    {
        "name": "horas_sueno",
        "label": "¿Cuántas horas dormiste?",
        "type": "number",
        "min": 0,
        "max": 12,
    },
    {
        "name": "tareas",
        "label": "¿Entregaste tus tareas?",
        "type": "select",
        "options": [("si", "Sí"), ("parcial", "Parcialmente"), ("no", "No")],
    },
    {
        "name": "comprension",
        "label": "¿Comprendiste los temas?",
        "type": "select",
        "options": [("si", "Sí"), ("parcial", "Parcialmente"), ("no", "No")],
    },
    {
        "name": "faltas",
        "label": "¿Tienes muchas faltas?",
        "type": "select",
        "options": [("no", "No"), ("algunas", "Algunas"), ("si", "Sí")],
    },
    {
        "name": "traslado_tec",
        "label": "¿Cuánto tardas en llegar al Instituto Tecnológico de Morelia?",
        "type": "select",
        "options": [("largo", "Más de 1 hora"), ("corto", "Menos de 1 hora")],
    },
    {
        "name": "horas_codigo",
        "label": "Horas semanales dedicadas a código (ej. Hermes, BiblioLink):",
        "type": "number",
        "min": 0,
        "max": 60,
    }
]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS diagnosticos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            estudio TEXT NOT NULL,
            horas_sueno INTEGER NOT NULL,
            tareas TEXT NOT NULL,
            comprension TEXT NOT NULL,
            faltas TEXT NOT NULL,
            traslado_tec TEXT,          
            horas_codigo INTEGER,       
            riesgo TEXT NOT NULL,
            perfil TEXT,                
            recomendacion TEXT NOT NULL,
            creado_en TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        );
        """
    )
    db.commit()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


@app.before_request
def load_logged_in_user():
    g.usuario = None
    if "usuario_id" in session:
        g.usuario = get_db().execute(
            "SELECT id, nombre, usuario FROM usuarios WHERE id = ?",
            (session["usuario_id"],),
        ).fetchone()


def normalizar_hechos(respuestas):
    horas_sueno = int(respuestas.get("horas_sueno", 7))
    horas_codigo = int(respuestas.get("horas_codigo", 0))
    
    hechos = {
        "estudio": respuestas["estudio"],
        "horas_sueno": horas_sueno,
        "tareas": respuestas["tareas"],
        "comprension": respuestas["comprension"],
        "faltas": respuestas["faltas"],
        "no_estudia": respuestas["estudio"] == "no",
        "estudia_poco": respuestas["estudio"] == "poco",
        "duerme_poco": horas_sueno < 6,
        "no_entrega_tareas": respuestas["tareas"] == "no",
        "entrega_tareas": respuestas["tareas"] in {"si", "parcial"},
        "no_comprende": respuestas["comprension"] == "no",
        "comprende_parcial": respuestas["comprension"] == "parcial",
        "muchas_faltas": respuestas["faltas"] == "si",
        "algunas_faltas": respuestas["faltas"] == "algunas",
        # Nuevos booleanos para Prolog:
        "traslado_largo": respuestas.get("traslado_tec") == "largo",
        "mucho_codigo": horas_codigo > 20
    }
    return hechos


def diagnostico_python(hechos):
    if (
        hechos["no_estudia"]
        and hechos["muchas_faltas"]
        and hechos["no_entrega_tareas"]
    ) or (hechos["no_comprende"] and hechos["duerme_poco"] and hechos["no_estudia"]):
        return "alto"

    if (
        hechos["estudia_poco"]
        or hechos["comprende_parcial"]
        or hechos["algunas_faltas"]
        or hechos["duerme_poco"]
        or hechos["tareas"] == "parcial"
    ):
        return "medio"

    return "bajo"


def diagnostico_prolog(hechos):
    consulta = (
        "consult('experto.pl'), "
        f"diagnostico_completo({str(hechos['no_estudia']).lower()}, "
        f"{str(hechos['estudia_poco']).lower()}, "
        f"{str(hechos['duerme_poco']).lower()}, "
        f"{str(hechos['no_entrega_tareas']).lower()}, "
        f"{str(hechos['comprende_parcial']).lower()}, "
        f"{str(hechos['no_comprende']).lower()}, "
        f"{str(hechos['muchas_faltas']).lower()}, "
        f"{str(hechos['algunas_faltas']).lower()}, "
        f"{str(hechos['traslado_largo']).lower()}, "
        f"{str(hechos['mucho_codigo']).lower()}, Riesgo, Perfil), "
        "write(Riesgo), write(','), write(Perfil), halt."
    )
    try:
        resultado = subprocess.run(
            ["swipl", "-q", "-g", consulta],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        salida = resultado.stdout.strip().split(',')
        if len(salida) == 2:
            return salida[0], salida[1] 
        return "medio", "regular"
    except (FileNotFoundError, subprocess.SubprocessError):
        return "medio", "regular"


def recomendacion_python(riesgo):
    recomendaciones = {
        "alto": "Debes crear un plan de estudio urgente, asistir a asesorías y regularizar tareas pendientes.",
        "medio": "Debes reforzar tus hábitos de estudio, dormir mejor y repasar los temas que no quedaron claros.",
        "bajo": "Mantén tu ritmo actual y sigue entregando tus actividades a tiempo.",
    }
    return recomendaciones[riesgo]


def recomendacion_clisp(riesgo, perfil):
    try:
        resultado = subprocess.run(
            ["clisp", "recomendaciones.lisp", riesgo, perfil],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        recomendaciones_raw = resultado.stdout.strip()
        return recomendaciones_raw.split('|') if recomendaciones_raw else ["Recomendación no disponible."]
    except (FileNotFoundError, subprocess.SubprocessError):
        return ["Revisa tus hábitos de estudio."]


@app.route("/")
def index():
    if g.usuario:
        return redirect(url_for("diagnostico"))
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/registro", methods=("GET", "POST"))
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        usuario = request.form["usuario"].strip().lower()
        password = request.form["password"]

        if not nombre or not usuario or not password:
            flash("Completa todos los campos.", "error")
        else:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO usuarios (nombre, usuario, password_hash) VALUES (?, ?, ?)",
                    (nombre, usuario, generate_password_hash(password)),
                )
                db.commit()
                flash("Cuenta creada. Ahora inicia sesión.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Ese usuario ya existe.", "error")

    return render_template("registro.html")


@app.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip().lower()
        password = request.form["password"]
        cuenta = get_db().execute(
            "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()

        if cuenta is None or not check_password_hash(cuenta["password_hash"], password):
            flash("Usuario o contraseña incorrectos.", "error")
        else:
            session.clear()
            session["usuario_id"] = cuenta["id"]
            return redirect(url_for("diagnostico"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/diagnostico", methods=("GET", "POST"))
@login_required
def diagnostico():
    if request.method == "POST":
        respuestas = request.form.to_dict() 
        hechos = normalizar_hechos(respuestas)
        riesgo, perfil = diagnostico_prolog(hechos)
        lista_recomendaciones = recomendacion_clisp(riesgo, perfil)
        recomendaciones_texto = "\n".join(lista_recomendaciones)
        
        db = get_db()
        db.execute(
            """
            INSERT INTO diagnosticos
            (usuario_id, estudio, horas_sueno, tareas, comprension, faltas, 
             traslado_tec, horas_codigo, riesgo, perfil, recomendacion, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                g.usuario["id"],
                respuestas["estudio"],
                hechos["horas_sueno"],
                respuestas["tareas"],
                respuestas["comprension"],
                respuestas["faltas"],
                respuestas.get("traslado_tec"),     
                hechos["horas_codigo"],             
                riesgo,
                perfil,                             
                recomendaciones_texto,              
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            ),
        )
        db.commit()
        
        return render_template(
            "resultado.html",
            riesgo=riesgo,
            perfil=perfil,
            recomendaciones=lista_recomendaciones, 
            respuestas=respuestas,
        )

    return render_template("diagnostico.html", preguntas=PREGUNTAS)

@app.route("/historial")
@login_required
def historial():
    diagnosticos = get_db().execute(
        """
        SELECT * FROM diagnosticos
        WHERE usuario_id = ?
        ORDER BY creado_en DESC
        """,
        (g.usuario["id"],),
    ).fetchall()
    return render_template("historial.html", diagnosticos=diagnosticos)


with app.app_context():
    init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
