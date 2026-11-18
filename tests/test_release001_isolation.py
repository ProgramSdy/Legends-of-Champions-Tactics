"""Focused RELEASE-001 mode-boundary regression checks.

These tests reload the FastAPI application with an isolated release-mode
environment.  They inspect routing/OpenAPI only; no real progression database
or player save is used.
"""

from __future__ import annotations

import importlib

from fastapi.testclient import TestClient
from battle_api.progression import ProgressionStore


def _app_for_mode(monkeypatch, mode: str | None, tmp_path):
    database_path = tmp_path / "release001.sqlite3"
    monkeypatch.setenv("BATTLE_API_PROGRESSION_DB", str(database_path))
    if mode is None:
        monkeypatch.delenv("LOCT_RELEASE_MODE", raising=False)
    else:
        monkeypatch.setenv("LOCT_RELEASE_MODE", mode)
    if mode == "public":
        fixture = ProgressionStore(
            database_path,
            public_mode=True,
            allow_public_initialize=True,
        )
        fixture._connection().close()
        monkeypatch.setenv("BATTLE_API_PUBLIC_DB", str(database_path))
        monkeypatch.setenv("BATTLE_API_PUBLIC_HMAC_KEY", "k" * 64)
        monkeypatch.setenv("BATTLE_API_RATE_LIMIT_HMAC_KEY", "r" * 64)
        monkeypatch.setenv("BATTLE_API_PUBLIC_ORIGIN", "https://public.test")
        monkeypatch.setenv("BATTLE_API_TRUSTED_PROXY_IPS", "127.0.0.1")
    import battle_api.app as app_module

    return importlib.reload(app_module)


def test_public_mode_is_fail_closed_and_hides_debug_route(monkeypatch, tmp_path):
    app_module = _app_for_mode(monkeypatch, "public", tmp_path)

    assert "/api/v1/debug/battles" not in app_module.app.openapi()["paths"]

    with TestClient(app_module.app) as client:
        response = client.post(
            "/api/v1/debug/battles?LOCT_RELEASE_MODE=development",
            json={"battleSize": 1, "playerTeam": ["hero.warrior.weapon_master"]},
            headers={"LOCT_RELEASE_MODE": "development"},
        )
    assert response.status_code == 404


def test_missing_or_invalid_mode_is_public_safe(monkeypatch, tmp_path):
    for mode in (None, "", "production", "staging", "PUBLIC"):
        app_module = _app_for_mode(monkeypatch, mode, tmp_path)
        assert "/api/v1/debug/battles" not in app_module.app.openapi()["paths"]


def test_development_mode_registers_debug_route_and_openapi(monkeypatch, tmp_path):
    app_module = _app_for_mode(monkeypatch, "development", tmp_path)

    assert "/api/v1/debug/battles" in app_module.app.openapi()["paths"]

    with TestClient(app_module.app) as client:
        response = client.post(
            "/api/v1/debug/battles",
            json={
                "battleSize": 1,
                "playerTeam": ["hero.warrior.weapon_master"],
                "enemyCompositionMode": "random",
                "enemyControlMode": "computer",
                "seed": 17,
            },
        )
    assert response.status_code == 200


def test_health_remains_available_in_public_mode(monkeypatch, tmp_path):
    app_module = _app_for_mode(monkeypatch, "public", tmp_path)

    with TestClient(app_module.app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_public_health_fails_closed_when_origin_is_missing(monkeypatch, tmp_path):
    app_module = _app_for_mode(monkeypatch, "public", tmp_path)
    monkeypatch.delenv("BATTLE_API_PUBLIC_ORIGIN")
    app_module = importlib.reload(app_module)

    with TestClient(app_module.app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "publicConfigurationInvalid"


def test_public_identity_route_fails_closed_without_independent_rate_key(
    monkeypatch, tmp_path
):
    app_module = _app_for_mode(monkeypatch, "public", tmp_path)
    monkeypatch.delenv("BATTLE_API_RATE_LIMIT_HMAC_KEY")
    app_module = importlib.reload(app_module)

    with TestClient(app_module.app, base_url="https://public.test") as client:
        response = client.post(
            "/api/v1/players",
            json={"playerName": "Blocked_Player"},
            headers={"Origin": "https://public.test"},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "publicIdentityNotConfigured"
