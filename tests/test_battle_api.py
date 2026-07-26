from fastapi.testclient import TestClient

from battle_api.app import app, registry


client = TestClient(app)


def test_health_create_get_command_and_not_found():
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "contractVersion": "1.0"}

    created = client.post(
        "/api/v1/battles",
        json={"scenarioId": "ragnar-vs-nighthawk", "seed": 42},
    )
    assert created.status_code == 200
    body = created.json()
    battle_id = body["battleId"]
    snapshot = body["data"]["snapshot"]

    fetched = client.get(f"/api/v1/battles/{battle_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["activeCombatantId"] == snapshot["activeCombatantId"]

    action = snapshot["legalActions"][0]
    submitted = client.post(
        f"/api/v1/battles/{battle_id}/commands",
        json={
            "type": "useSkill",
            "commandId": "cmd.api.1",
            "expectedRevision": 0,
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )
    assert submitted.status_code == 200
    assert submitted.json()["data"]["accepted"] is True
    assert registry.get(battle_id).revision == 1

    missing = client.get("/api/v1/battles/not-found")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "battleNotFound"


def test_pydantic_validation_rejects_malformed_request_before_engine_mutation():
    response = client.post(
        "/api/v1/battles/not-found/commands",
        json={"type": "useSkill", "commandId": "", "expectedRevision": -1},
    )
    assert response.status_code == 422


def test_unknown_scenario_is_rejected_by_schema():
    response = client.post(
        "/api/v1/battles",
        json={"scenarioId": "arbitrary-python-class", "seed": 42},
    )
    assert response.status_code == 422


def test_missing_command_battle_returns_structured_404():
    response = client.post(
        "/api/v1/battles/not-found/commands",
        json={
            "type": "useSkill",
            "commandId": "cmd.missing",
            "expectedRevision": 0,
            "actorId": "friendly.ragnar",
            "skillId": "skill.warrior.fatal_strike",
            "targetIds": ["enemy.nighthawk"],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == {
        "code": "battleNotFound",
        "message": "Battle was not found.",
    }


def test_api_rejection_returns_authoritative_snapshot_without_revision_change():
    created = client.post(
        "/api/v1/battles",
        json={"scenarioId": "ragnar-vs-nighthawk", "seed": 42},
    ).json()
    battle_id = created["battleId"]
    snapshot = created["data"]["snapshot"]

    response = client.post(
        f"/api/v1/battles/{battle_id}/commands",
        json={
            "type": "useSkill",
            "commandId": "cmd.stale.api",
            "expectedRevision": 99,
            "actorId": snapshot["activeCombatantId"],
            "skillId": snapshot["legalActions"][0]["skillId"],
            "targetIds": snapshot["legalActions"][0]["validTargetIds"][:1],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["revision"] == 0
    assert body["data"]["accepted"] is False
    assert body["data"]["code"] == "staleRevision"
    assert body["data"]["snapshot"] == snapshot


def test_delayed_duplicate_response_keeps_its_original_revision_consistent():
    created = client.post(
        "/api/v1/battles",
        json={"scenarioId": "ragnar-vs-nighthawk", "seed": 42},
    ).json()
    battle_id = created["battleId"]

    def command(snapshot, command_id, revision):
        action = snapshot["legalActions"][0]
        return {
            "type": "useSkill",
            "commandId": command_id,
            "expectedRevision": revision,
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        }

    first_command = command(created["data"]["snapshot"], "cmd.original", 0)
    first = client.post(
        f"/api/v1/battles/{battle_id}/commands", json=first_command
    ).json()
    second_command = command(first["data"]["snapshot"], "cmd.later", 1)
    second = client.post(
        f"/api/v1/battles/{battle_id}/commands", json=second_command
    ).json()
    replay = client.post(
        f"/api/v1/battles/{battle_id}/commands", json=first_command
    ).json()

    assert second["revision"] == second["data"]["revision"] == 2
    assert registry.get(battle_id).revision == 2
    assert replay["revision"] == replay["data"]["revision"] == 1
    assert replay["data"] == first["data"]


def test_cors_allows_default_local_frontend_preflight():
    response = client.options(
        "/api/v1/battles",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") is None
    assert "POST" in response.headers["access-control-allow-methods"]


def test_cors_rejects_unlisted_origin():
    response = client.options(
        "/api/v1/battles",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
