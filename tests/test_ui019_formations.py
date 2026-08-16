from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from battle_api.adapter import (
    BattleAdapter,
    THREE_HERO_FORMATION_IDS,
)
from battle_api.app import app, registry


client = TestClient(app)

PLAYER_TEAM = [
    "hero.warrior.weapon_master",
    "hero.warrior.defence",
    "hero.warrior.berserker",
]
ENEMY_TEAM = [
    "hero.rogue.comprehensiveness",
    "hero.priest.comprehensiveness",
    "hero.paladin.protection",
]


@pytest.mark.parametrize(
    ("formation", "positions"),
    [
        ("one-front-two-rear", ["front", "rear", "rear"]),
        ("two-front-one-rear", ["front", "front", "rear"]),
        ("all-front", ["front", "front", "front"]),
    ],
)
def test_adapter_maps_each_3v3_formation_and_snapshot_positions(
    formation, positions
):
    session, envelope = BattleAdapter().create_battle(
        battle_size=3,
        player_team=PLAYER_TEAM,
        enemy_team=ENEMY_TEAM,
        player_formation=formation,
        enemy_formation=formation,
        seed=1901,
    )

    assert [hero.position for hero in session.game.player_heroes] == positions
    assert [hero.position for hero in session.game.opponent_heroes] == positions
    snapshot = envelope["data"]["snapshot"]
    assert snapshot["formations"] == {
        "friendly": formation,
        "enemy": formation,
    }
    for side in snapshot["sides"]:
        assert [
            snapshot["combatants"][combatant_id]["position"]
            for combatant_id in side["combatantIds"]
        ] == positions


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "playerFormation is required for a 3v3 battle"),
        (
            {"playerFormation": "front-rear"},
            "playerFormation must be one-front-two-rear",
        ),
        (
            {"playerFormation": "all-front"},
            "enemyFormation is required for a player-controlled 3v3 enemy",
        ),
        (
            {
                "playerFormation": "all-front",
                "enemyFormation": "side-by-side",
            },
            "enemyFormation must be one-front-two-rear",
        ),
    ],
)
def test_http_3v3_rejects_missing_and_wrong_size_formations(payload, message):
    sessions_before = len(registry._sessions)
    response = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 3,
            "playerTeam": PLAYER_TEAM,
            "enemyTeam": ENEMY_TEAM,
            "enemyControlMode": "player",
            **payload,
        },
    )

    assert response.status_code == 422
    assert message in response.text
    assert len(registry._sessions) == sessions_before


def test_http_computer_3v3_requires_enemy_formation_omission():
    response = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 3,
            "playerTeam": PLAYER_TEAM,
            "enemyCompositionMode": "random",
            "enemyControlMode": "computer",
            "playerFormation": "all-front",
            "enemyFormation": "one-front-two-rear",
            "seed": 1902,
        },
    )

    assert response.status_code == 422
    assert "enemyFormation must be omitted" in response.text


@pytest.mark.parametrize("formation", ["one-front-two-rear", "all-front"])
def test_http_rejects_3v3_ids_for_smaller_battles(formation):
    battle_size = 1 if formation == "one-front-two-rear" else 2
    payload = {
        "battleSize": battle_size,
        "playerTeam": PLAYER_TEAM[:battle_size],
        "enemyTeam": ENEMY_TEAM[:battle_size],
        "playerFormation": formation,
    }
    if battle_size == 2:
        payload["enemyFormation"] = "front-rear"

    response = client.post("/api/v1/battles", json=payload)

    assert response.status_code == 422


def test_seeded_computer_3v3_formation_is_authoritative_and_reproducible():
    kwargs = dict(
        battle_size=3,
        player_team=PLAYER_TEAM,
        enemy_composition_mode="random",
        enemy_control_mode="computer",
        player_formation="two-front-one-rear",
        seed=1903,
    )

    first_session, first_envelope = BattleAdapter().create_battle(**kwargs)
    second_session, second_envelope = BattleAdapter().create_battle(**kwargs)

    assert first_session.enemy_formation == second_session.enemy_formation
    assert first_session.enemy_formation in THREE_HERO_FORMATION_IDS
    assert first_envelope["data"]["snapshot"]["formations"] == (
        second_envelope["data"]["snapshot"]["formations"]
    )


def test_http_seeded_computer_3v3_selection_is_reproducible():
    payload = {
        "battleSize": 3,
        "playerTeam": PLAYER_TEAM,
        "enemyCompositionMode": "random",
        "enemyControlMode": "computer",
        "playerFormation": "one-front-two-rear",
        "seed": 1907,
    }

    first = client.post("/api/v1/battles", json=payload)
    second = client.post("/api/v1/battles", json=payload)

    assert first.status_code == second.status_code == 200
    first_formations = first.json()["data"]["snapshot"]["formations"]
    second_formations = second.json()["data"]["snapshot"]["formations"]
    assert first_formations == second_formations
    assert first_formations["friendly"] == "one-front-two-rear"
    assert first_formations["enemy"] in THREE_HERO_FORMATION_IDS


def test_adapter_3v3_requires_player_and_player_controlled_enemy_formations():
    adapter = BattleAdapter()
    with pytest.raises(ValueError, match="player_formation is required"):
        adapter.create_battle(
            battle_size=3,
            player_team=PLAYER_TEAM,
            enemy_team=ENEMY_TEAM,
        )
    with pytest.raises(ValueError, match="enemy_formation is required"):
        adapter.create_battle(
            battle_size=3,
            player_team=PLAYER_TEAM,
            enemy_team=ENEMY_TEAM,
            player_formation="all-front",
        )
    with pytest.raises(ValueError, match="player_formation must be"):
        adapter.create_battle(
            battle_size=3,
            player_team=PLAYER_TEAM,
            enemy_team=ENEMY_TEAM,
            player_formation="front-rear",
            enemy_formation="all-front",
        )


def test_3v3_warrior_melee_legality_releases_rear_after_all_fronts_fall():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=3,
        player_team=PLAYER_TEAM,
        enemy_team=ENEMY_TEAM,
        player_formation="one-front-two-rear",
        enemy_formation="two-front-one-rear",
        seed=1904,
    )
    actor = session.game.player_heroes[0]
    front_one, front_two, rear = session.game.opponent_heroes
    fatal_strike = next(skill for skill in actor.skills if skill.name == "Fatal Strike")

    assert adapter._valid_target_ids(session, actor, fatal_strike) == [
        adapter._combatant_id(session, front_one),
        adapter._combatant_id(session, front_two),
    ]
    front_one.hp = 0
    front_two.hp = 0
    assert adapter._valid_target_ids(session, actor, fatal_strike) == [
        adapter._combatant_id(session, rear)
    ]


def test_3v3_projectile_and_ranged_instant_keep_all_living_targets_legal():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=3,
        player_team=[
            "hero.rogue.comprehensiveness",
            "hero.warrior.defence",
            "hero.warrior.berserker",
        ],
        enemy_team=ENEMY_TEAM,
        player_formation="one-front-two-rear",
        enemy_formation="two-front-one-rear",
        seed=1905,
    )
    defence = session.game.player_heroes[1]
    berserker = session.game.player_heroes[2]
    enemies = session.game.opponent_heroes
    shield_lash = next(skill for skill in defence.skills if skill.name == "Shield Lash")
    moon_slash = next(skill for skill in berserker.skills if skill.name == "Moon Slash")
    enemy_ids = [adapter._combatant_id(session, enemy) for enemy in enemies]

    assert defence.position == berserker.position == "rear"
    assert adapter._valid_target_ids(session, defence, shield_lash) == enemy_ids
    assert adapter._valid_target_ids(session, berserker, moon_slash) == enemy_ids
    assert enemies[2].take_damage_calculation(100, "ranged_projectile", defence) == 75
    assert enemies[2].take_damage_calculation(100, "ranged_instant", berserker) == 100


def test_3v3_computer_melee_target_is_reconciled_to_front_line():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=3,
        player_team=ENEMY_TEAM,
        enemy_team=PLAYER_TEAM,
        player_formation="two-front-one-rear",
        enemy_control_mode="computer",
        seed=1906,
    )
    friendly_fronts = session.game.player_heroes[:2]
    friendly_rear = session.game.player_heroes[2]
    actor = session.game.opponent_heroes[0]
    fatal_strike = next(skill for skill in actor.skills if skill.name == "Fatal Strike")
    fatal_strike.evasion_check = lambda _target: False
    actor.ai_choose_skill = lambda _opponents, _allies: fatal_strike
    actor.ai_choose_target = lambda _skill, _opponents, _allies: friendly_rear
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    events = adapter._drain_automatic_turns(session)
    skill_event = next(event for event in events if event["type"] == "skillStarted")

    assert skill_event["targetIds"][0] in {
        adapter._combatant_id(session, hero) for hero in friendly_fronts
    }
    assert skill_event["targetIds"] != [
        adapter._combatant_id(session, friendly_rear)
    ]


def test_openapi_exposes_size_specific_formation_literal_groups():
    schema = app.openapi()
    properties = schema["components"]["schemas"]["CreateBattleRequest"][
        "properties"
    ]

    for field_name in ("playerFormation", "enemyFormation"):
        literal_groups = [
            set(branch["enum"])
            for branch in properties[field_name]["anyOf"]
            if "enum" in branch
        ]
        assert {"front-rear", "side-by-side"} in literal_groups
        assert set(THREE_HERO_FORMATION_IDS) in literal_groups
