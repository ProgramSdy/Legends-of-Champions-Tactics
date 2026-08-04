from fastapi.testclient import TestClient
import pytest

from battle_api.app import DEFAULT_CORS_ORIGINS, _cors_origins, app, registry


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


def test_api_status_application_exposes_additive_authoritative_presentation():
    created = client.post(
        "/api/v1/battles",
        json={"scenarioId": "ragnar-vs-nighthawk", "seed": 42},
    ).json()
    battle_id = created["battleId"]
    snapshot = created["data"]["snapshot"]
    action = next(
        action
        for action in snapshot["legalActions"]
        if action["skillId"] == "skill.rogue.shadow_evasion"
    )

    response = client.post(
        f"/api/v1/battles/{battle_id}/commands",
        json={
            "type": "useSkill",
            "commandId": "cmd.status-presentation.api",
            "expectedRevision": 0,
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": [],
        },
    )

    assert response.status_code == 200
    events = response.json()["data"]["events"]
    applied = next(event for event in events if event["type"] == "statusApplied")
    assert applied["statusId"] == "status.shadow_evasion"
    assert applied["sourceId"] == snapshot["activeCombatantId"]
    assert applied["targetId"] == snapshot["activeCombatantId"]
    assert applied["statusPresentation"] == "buff"
    assert applied["effectHint"] == "status"
    assert all(
        "statusPresentation" not in event
        for event in events
        if event["type"] != "statusApplied"
    )


@pytest.mark.parametrize(
    ("enemy_control_mode", "play_opening"),
    [("player", False), ("computer", True)],
)
def test_create_exposes_additive_opening_lifecycle_contract(enemy_control_mode, play_opening):
    response = client.post(
        "/api/v1/battles",
        json={
            "scenarioId": "ragnar-vs-nighthawk",
            "seed": 42,
            "enemyControlMode": enemy_control_mode,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["playOpening"] is play_opening
    assert "openingSnapshot" in data
    if not play_opening:
        assert data["openingSnapshot"] == data["snapshot"]
    else:
        assert data["openingSnapshot"]["activeCombatantId"] == "enemy.nighthawk"
        assert [event["sequence"] for event in data["events"]] == sorted(
            event["sequence"] for event in data["events"]
        )


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
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"
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


def test_cors_origin_configuration_is_explicit_and_never_allows_wildcard(monkeypatch):
    monkeypatch.delenv("BATTLE_API_CORS_ORIGINS", raising=False)
    assert _cors_origins() == list(DEFAULT_CORS_ORIGINS)

    monkeypatch.setenv(
        "BATTLE_API_CORS_ORIGINS",
        " https://preview.example , *, ,http://localhost:3001 ",
    )
    assert _cors_origins() == [
        "https://preview.example",
        "http://localhost:3001",
    ]


def test_roster_endpoint_exposes_only_the_eight_approved_heroes():
    response = client.get("/api/v1/heroes")

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "1.0"
    assert len(body["heroes"]) == 8
    assert {hero["definitionId"] for hero in body["heroes"]} == {
        "hero.priest.comprehensiveness",
        "hero.priest.discipline",
        "hero.paladin.retribution",
        "hero.paladin.protection",
        "hero.mage.comprehensiveness",
        "hero.warrior.defence",
        "hero.warrior.weapon_master",
        "hero.rogue.comprehensiveness",
    }


def test_api_creates_live_three_hero_player_controlled_battle():
    response = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 3,
            "playerTeam": [
                "hero.priest.comprehensiveness",
                "hero.priest.comprehensiveness",
                "hero.mage.comprehensiveness",
            ],
            "enemyCompositionMode": "specified",
            "enemyTeam": [
                "hero.paladin.retribution",
                "hero.warrior.defence",
                "hero.rogue.comprehensiveness",
            ],
            "enemyControlMode": "player",
            "seed": 12,
        },
    )

    assert response.status_code == 200
    snapshot = response.json()["data"]["snapshot"]
    assert len(snapshot["sides"][0]["combatantIds"]) == 3
    assert len(snapshot["sides"][1]["combatantIds"]) == 3
    assert len(snapshot["combatants"]) == 6
    assert all(
        combatant["isPlayerControlled"]
        for combatant in snapshot["combatants"].values()
    )


@pytest.mark.parametrize(
    "payload",
    [
        {
            "battleSize": 2,
            "playerTeam": ["hero.priest.comprehensiveness"],
            "enemyCompositionMode": "random",
            "enemyControlMode": "computer",
        },
        {
            "battleSize": 2,
            "playerTeam": [
                "hero.priest.comprehensiveness",
                "hero.mage.comprehensiveness",
            ],
            "enemyCompositionMode": "specified",
            "enemyTeam": ["hero.rogue.comprehensiveness"],
            "enemyControlMode": "player",
        },
        {
            "battleSize": 1,
            "playerTeam": ["hero.necromancer.unsupported"],
            "enemyCompositionMode": "random",
            "enemyControlMode": "computer",
        },
        {
            "battleSize": 1,
            "playerTeam": ["hero.priest.comprehensiveness"],
            "enemyCompositionMode": "random",
            "enemyTeam": ["hero.rogue.comprehensiveness"],
            "enemyControlMode": "computer",
        },
    ],
)
def test_api_rejects_invalid_team_builder_configuration(payload):
    response = client.post("/api/v1/battles", json=payload)
    assert response.status_code == 422
