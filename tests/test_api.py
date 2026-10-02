from fastapi.testclient import TestClient

from app import main
from app.schemas import Finding, Report

client = TestClient(main.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_report_ok(monkeypatch):
    fake = Report(
        company="acme",
        executive_summary="Summary",
        risks=[Finding(title="Risk", severity="High", explanation="Because", sources=["a.pdf p.1"])],
        growth_opportunities=[],
    )
    monkeypatch.setattr(main, "analyze", lambda c: fake)
    r = client.get("/report/acme")
    assert r.status_code == 200
    assert r.json()["risks"][0]["sources"] == ["a.pdf p.1"]


def test_report_no_docs(monkeypatch):
    def boom(c):
        raise ValueError("No documents found")

    monkeypatch.setattr(main, "analyze", boom)
    assert client.get("/report/unknown").status_code == 404


def test_ingest_rejects_non_pdf():
    r = client.post(
        "/ingest",
        files={"file": ("a.txt", b"hello")},
        data={"company": "x", "doc_type": "10-K", "year": "2024"},
    )
    assert r.status_code == 400