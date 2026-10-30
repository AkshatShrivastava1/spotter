"""Week 5: getting ready for a real deploy."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import Settings, check_production, get_settings
from app.db import engine
from app.main import app
from app.models import PhotoData, ProgressPhoto

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def _upload(client, h, data=PNG, media="image/png", pose="front"):
    return client.post("/progress-photos", files={"file": ("f.png", data, media)}, data={"pose": pose}, headers=h)


# ---------- progress photos live in the database, not on the server's disk ----------

def test_photo_bytes_are_saved_in_the_database(client, user):
    pid = _upload(client, user["h"]).json()["id"]
    with Session(engine) as s:
        photo = s.get(ProgressPhoto, pid)
        assert photo.path == "" and photo.media_type == "image/png"
        assert s.get(PhotoData, pid).data == PNG
    img = client.get(f"/progress-photos/{pid}/image", headers=user["h"])
    assert img.status_code == 200 and img.content == PNG and img.headers["content-type"] == "image/png"


def test_photo_list_has_no_image_bytes(client, user):
    _upload(client, user["h"], pose="side")
    rows = client.get("/progress-photos", headers=user["h"]).json()
    assert rows and set(rows[0]) == {"id", "day", "pose"}


def test_only_images_are_accepted(client, user):
    assert _upload(client, user["h"], data=b"<script>", media="text/html").status_code == 415
    assert _upload(client, user["h"], data=b"", media="image/jpeg").status_code == 422


def test_oversized_photo_is_rejected(client, user):
    big = b"0" * (5 * 1024 * 1024 + 1)
    assert _upload(client, user["h"], data=big, media="image/jpeg").status_code == 413


def test_photos_saved_to_disk_before_the_move_still_load(client, user, tmp_path):
    old = tmp_path / "old.jpg"
    old.write_bytes(b"old-jpeg")
    with Session(engine) as s:
        p = ProgressPhoto(user_id=user["id"], day=date(2026, 10, 1), pose="front", path=str(old))
        s.add(p)
        s.commit()
        s.refresh(p)
        pid = p.id
    assert client.get(f"/progress-photos/{pid}/image", headers=user["h"]).content == b"old-jpeg"
    old.unlink()  # the disk got wiped by a redeploy
    assert client.get(f"/progress-photos/{pid}/image", headers=user["h"]).status_code == 404


# ---------- production refuses to start with unsafe settings ----------

GOOD = {"env": "production", "jwt_secret": "x" * 48, "cron_secret": "c" * 32, "scheduler_enabled": False}


def test_production_with_everything_set_is_fine(monkeypatch):
    monkeypatch.setenv("SPOTTER_DATABASE_URL", "postgres://u:p@db.example.com/spotter")
    s = Settings(**GOOD)
    assert s.production_problems() == []
    check_production(s)


@pytest.mark.parametrize("change, problem", [
    ({"jwt_secret": ""}, "SPOTTER_JWT_SECRET"),
    ({"jwt_secret": "short"}, "SPOTTER_JWT_SECRET"),
    ({"cron_secret": ""}, "SPOTTER_CRON_SECRET"),
])
def test_production_flags_missing_secrets(monkeypatch, change, problem):
    monkeypatch.setenv("SPOTTER_DATABASE_URL", "postgres://u:p@db.example.com/spotter")
    s = Settings(**{**GOOD, **change})
    with pytest.raises(RuntimeError, match=problem):
        check_production(s)


def test_production_refuses_sqlite(monkeypatch):
    monkeypatch.setenv("SPOTTER_DATABASE_URL", "sqlite:///./spotter.db")
    assert any("Postgres" in p for p in Settings(**GOOD).production_problems())


def test_development_skips_the_checks():
    check_production(Settings(env="development", jwt_secret=""))


def test_server_will_not_boot_misconfigured(monkeypatch):
    monkeypatch.setattr(get_settings(), "env", "production")
    monkeypatch.setattr(get_settings(), "jwt_secret", "")
    with pytest.raises(RuntimeError, match="Refusing to start in production"):
        with TestClient(app):
            pass
