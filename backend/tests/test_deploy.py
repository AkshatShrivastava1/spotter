"""Week 3: things that matter once the backend runs in the cloud."""

from app.config import get_settings, normalize_db_url


def test_host_database_urls_get_the_psycopg_driver():
    assert normalize_db_url("postgres://u:p@h:5432/db") == "postgresql+psycopg://u:p@h:5432/db"
    assert normalize_db_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_db_url("sqlite:///./spotter.db") == "sqlite:///./spotter.db"


def test_health_checks_the_database(client):
    body = client.get("/health").json()
    assert body["ok"] is True and body["db"] in ("sqlite", "postgresql")


def test_cron_endpoint_hidden_without_secret(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "cron_secret", "")
    assert client.post("/internal/run-nudges").status_code == 404


def test_cron_endpoint_requires_matching_secret(client, user, monkeypatch):
    monkeypatch.setattr(get_settings(), "cron_secret", "s3cret")
    assert client.post("/internal/run-nudges", headers={"X-Cron-Secret": "nope"}).status_code == 401
    r = client.post("/internal/run-nudges", headers={"X-Cron-Secret": "s3cret"})
    assert r.status_code == 200 and isinstance(r.json()["sent"], int)
