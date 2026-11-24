import pytest

from src.app import APP_NAME, app, store


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body


def test_version_reads_environment(client, monkeypatch):
    monkeypatch.setenv("APP_COMMIT", "abc1234")
    body = client.get("/version").get_json()
    assert body["commit"] == "abc1234"
    assert body["app"] == APP_NAME
    assert body["version"]
    assert body["built_at"]


def test_reset_returns_no_content(client):
    assert client.post("/reset").status_code == 204


def test_reset_rejects_get(client):
    assert client.get("/reset").status_code == 405


def test_reset_clears_store(client):
    store.next_id = 42
    client.post("/reset")
    assert store.next_id == 1


def test_home_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


def test_unknown_route_returns_not_found(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"] == "not_found"

def test_create_and_list_students_sorted(client):
    client.post("/reset")
    r1 = client.post("/students", json={"name": "Popescu Ana", "group": "1.1"})
    r2 = client.post("/students", json={"name": "Albu Maria", "group": "1.1"})

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.get_json()["id"] == 1
    assert r2.get_json()["id"] == 2

    listing = client.get("/students")
    assert listing.status_code == 200
    names = [s["name"] for s in listing.get_json()]
    assert names == ["Albu Maria", "Popescu Ana"]


def test_create_student_validation_error(client):
    client.post("/reset")
    resp = client.post("/students", json={"name": "Ion"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation"


def test_add_grade_student_not_found(client):
    client.post("/reset")
    resp = client.post("/grades", json={"student_id": 999, "subject": "MAP", "grade": 9})
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


def test_add_grade_invalid_grade_and_subject_boundaries(client):
    client.post("/reset")
    st = client.post("/students", json={"name": "Test Student", "group": "1.1"}).get_json()

    resp_low = client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": 0})
    resp_high = client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": 11})
    resp_bool = client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": True})
    resp_long_subj = client.post(
        "/grades",
        json={"student_id": st["id"], "subject": "A" * 101, "grade": 8},
    )

    assert resp_low.status_code == 400
    assert resp_high.status_code == 400
    assert resp_bool.status_code == 400
    assert resp_long_subj.status_code == 400

    ok_min = client.post("/grades", json={"student_id": st["id"], "subject": "A" * 100, "grade": 1})
    ok_max = client.post("/grades", json={"student_id": st["id"], "subject": "A" * 100, "grade": 10})
    assert ok_min.status_code == 201
    assert ok_max.status_code == 201


def test_max_five_grades_per_subject_conflict(client):
    client.post("/reset")
    st = client.post("/students", json={"name": "Elev Limita", "group": "1.1"}).get_json()

    for g in [7, 8, 9, 10, 8]:
        ok = client.post("/grades", json={"student_id": st["id"], "subject": "POO", "grade": g})
        assert ok.status_code == 201

    sixth = client.post("/grades", json={"student_id": st["id"], "subject": "POO", "grade": 10})
    assert sixth.status_code == 409
    assert sixth.get_json()["error"] == "conflict"


def test_student_grades_empty_average_and_round_half_up(client):
    client.post("/reset")
    st = client.post("/students", json={"name": "Elev Medie", "group": "1.1"}).get_json()

    empty_resp = client.get(f"/students/{st['id']}/grades")
    assert empty_resp.status_code == 200
    assert empty_resp.get_json() == {"grades": [], "average": None}

    client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": 7})
    client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": 8})
    client.post("/grades", json={"student_id": st["id"], "subject": "POO", "grade": 10})

    grades_resp = client.get(f"/students/{st['id']}/grades")
    assert grades_resp.status_code == 200
    assert grades_resp.get_json()["average"] == 8.33


def test_subject_report_empty_and_populated(client):
    client.post("/reset")
    missing_param = client.get("/report")
    assert missing_param.status_code == 400

    empty_report = client.get("/report?subject=MAP")
    assert empty_report.status_code == 200
    assert empty_report.get_json() == {
        "subject": "MAP",
        "average": None,
        "min": None,
        "max": None,
        "count": 0,
    }

    st = client.post("/students", json={"name": "Elev Raport", "group": "1.1"}).get_json()
    client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": 8})
    client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": 9})

    rep = client.get("/report?subject=MAP")
    assert rep.status_code == 200
    assert rep.get_json() == {
        "subject": "MAP",
        "average": 8.5,
        "min": 8,
        "max": 9,
        "count": 2,
    }
def test_list_students_filter_by_group(client):
    client.post("/reset")
    client.post("/students", json={"name": "Popescu Ana", "group": "1.1"})
    client.post("/students", json={"name": "Albu Maria", "group": "1.2"})
    client.post("/students", json={"name": "Ionescu Dan", "group": "1.1"})

    resp = client.get("/students?group=1.1")
    assert resp.status_code == 200
    names = [s["name"] for s in resp.get_json()]
    assert names == ["Ionescu Dan", "Popescu Ana"]


def test_store_summary_stats(client):
    client.post("/reset")
    assert store.get_summary_stats() == {
        "students_count": 0,
        "grades_count": 0,
        "overall_average": None,
    }

    st = client.post("/students", json={"name": "Elev Test", "group": "1.1"}).get_json()
    client.post("/grades", json={"student_id": st["id"], "subject": "MAP", "grade": 8})
    client.post("/grades", json={"student_id": st["id"], "subject": "POO", "grade": 9})

    assert store.get_summary_stats() == {
        "students_count": 1,
        "grades_count": 2,
        "overall_average": 8.5,
    }
    