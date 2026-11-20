from decimal import Decimal, ROUND_HALF_UP
import os
import time
from flask import Flask, jsonify, request

APP_NAME = "map-project"
APP_VERSION = "0.1.0"
MAX_GRADES_PER_SUBJECT = 5  # k = 5 din enuntul Temei 3[cite: 15]

STARTED_AT = time.monotonic()

app = Flask(__name__)


def round_half_up_2(value: float | int | Decimal) -> float:
    d = Decimal(str(value))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))  # rotunjire la jumatate in sus la 2 zecimale[cite: 9, 15]


def error_response(status_code: int, error_code: str, message: str):
    return jsonify({"error": error_code, "message": message}), status_code  # formatul standard de eroare[cite: 9]


class Store:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.next_id = 1
        self.items: list = []
        self.students: list[dict] = []
        self.grades: list[dict] = []
        self.next_student_id = 1
        self.next_grade_id = 1

    def get_student(self, student_id: int) -> dict | None:
        for student in self.students:
            if student["id"] == student_id:
                return student
        return None


store = Store()


@app.errorhandler(404)
def handle_not_found(_err):
    return error_response(404, "not_found", "Resource not found")  # raspuns JSON valid pe 404[cite: 9, 39]


@app.get("/health")
def health():
    uptime_seconds = int(time.monotonic() - STARTED_AT)
    return jsonify({"status": "ok", "uptime_seconds": uptime_seconds}), 200  # ruta obligatorie /health[cite: 8]


@app.get("/version")
def version():
    commit_sha = (
        os.environ.get("APP_COMMIT")
        or os.environ.get("GITHUB_SHA")
        or os.environ.get("GIT_COMMIT")
        or "unknown"
    )  # citeste APP_COMMIT din mediu[cite: 8, 9, 40]
    if len(commit_sha) > 7 and commit_sha != "unknown":
        commit_sha = commit_sha[:7]

    built_at = os.environ.get("BUILT_AT", "1970-01-01T00:00:00Z")
    return jsonify({
        "app": APP_NAME,
        "version": APP_VERSION,
        "commit": commit_sha,
        "built_at": built_at,
    }), 200  # ruta obligatorie /version[cite: 8]


@app.get("/")
def index():
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Gradebook API - Theme 3</title>
</head>
<body>
  <h1>Gradebook API</h1>
  <p>Author: Dieaconu Rebeca</p>
  <p>Group: 1.1</p>
  <p>Theme: 3</p>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}  # pagina HTML cu nume, grupa si tema[cite: 8]


@app.post("/reset")
def reset_data():
    store.reset()
    return "", 204  # 204 si goleste datele din memorie[cite: 8, 9]


@app.post("/students")
def create_student():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    group = str(data.get("group", "")).strip()

    if not name or not group:
        return error_response(400, "validation", "name and group are required")  # validare campuri obligatorii[cite: 9, 15]

    student = {
        "id": store.next_student_id,
        "name": name,
        "group": group,
    }
    store.next_student_id += 1
    store.students.append(student)
    return jsonify(student), 201  # 201 la creare[cite: 9, 15]


@app.get("/students")
def list_students():
    ordered = sorted(store.students, key=lambda s: s["name"])
    return jsonify(ordered), 200  # ordonare dupa name[cite: 9, 15]


@app.post("/grades")
def add_grade():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    subject = str(data.get("subject", "")).strip()
    grade = data.get("grade")

    if not isinstance(student_id, int) or isinstance(student_id, bool):
        return error_response(400, "validation", "student_id must be an integer")  # 400 la tip gresit[cite: 9]

    student = store.get_student(student_id)
    if student is None:
        return error_response(404, "not_found", "student not found")  # 404 daca studentul nu exista[cite: 9, 15]

    if not subject or len(subject) > 100:
        return error_response(400, "validation", "subject must be between 1 and 100 characters")  # lungime 1..100[cite: 9, 15]

    if not isinstance(grade, int) or isinstance(grade, bool) or not (1 <= grade <= 10):
        return error_response(400, "validation", "grade must be an integer between 1 and 10")  # nota intreg 1..10[cite: 9, 15]

    same_subject_count = sum(
        1
        for g in store.grades
        if g["student_id"] == student_id and g["subject"] == subject
    )
    if same_subject_count >= MAX_GRADES_PER_SUBJECT:
        return error_response(409, "conflict", "maximum grades per subject reached")  # max k=5 note per disciplina[cite: 9, 15]

    grade_item = {
        "id": store.next_grade_id,
        "student_id": student_id,
        "subject": subject,
        "grade": grade,
    }
    store.next_grade_id += 1
    store.grades.append(grade_item)
    return jsonify(grade_item), 201  # 201 la adaugarea notei[cite: 9, 15]


@app.get("/students/<int:student_id>/grades")
def get_student_grades(student_id: int):
    student = store.get_student(student_id)
    if student is None:
        return error_response(404, "not_found", "student not found")  # 404 daca studentul nu exista[cite: 9, 15]

    student_grades = [g for g in store.grades if g["student_id"] == student_id]
    if not student_grades:
        avg = None  # media unui student fara note este null[cite: 15]
    else:
        total = sum(g["grade"] for g in student_grades)
        avg = round_half_up_2(Decimal(total) / Decimal(len(student_grades)))  # rotunjita la 2 zecimale[cite: 9, 15]

    return jsonify({"grades": student_grades, "average": avg}), 200  # formatul cerut pentru notele studentului[cite: 15]


@app.get("/report")
def subject_report():
    subject = request.args.get("subject", "").strip()
    if not subject:
        return error_response(400, "validation", "subject query parameter is required")  # subject este obligatoriu[cite: 9, 15]

    values = [g["grade"] for g in store.grades if g["subject"] == subject]
    if not values:
        return jsonify({
            "subject": subject,
            "average": None,
            "min": None,
            "max": None,
            "count": 0,
        }), 200  # fara impartire la zero cand nu sunt note[cite: 15]

    total = sum(values)
    avg = round_half_up_2(Decimal(total) / Decimal(len(values)))  # media rotunjita la 2 zecimale[cite: 9, 15]
    return jsonify({
        "subject": subject,
        "average": avg,
        "min": min(values),
        "max": max(values),
        "count": len(values),
    }), 200  # raportul pe disciplina[cite: 15]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # asculta pe portul 8080[cite: 9]