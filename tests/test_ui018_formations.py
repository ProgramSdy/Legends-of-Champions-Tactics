from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from battle_api.adapter import BattleAdapter, FORMATION_IDS, HERO_ROSTER
from battle_api.app import app, registry
from game.hero_generator import HeroGenerator
from heroes.hero import Hero
from heroes.summon_unit import SkeletonWarrior
from heroes.warrior import Warrior_Weapon_Master
from skills.skill import Skill


client = TestClient(app)


TEAM = [
    "hero.warrior.weapon_master",
    "hero.warrior.defence",
]
ENEMY = [
    "hero.rogue.comprehensiveness",
    "hero.priest.comprehensiveness",
]
HTTP_UNLOCKED_TEAM = [
    "hero.warrior.weapon_master",
    "hero.mage.comprehensiveness",
]


def test_http_2v2_requires_typed_formations_and_rejects_them_elsewhere():
    sessions_before = len(registry._sessions)
    missing_player = client.post(
        "/api/v1/battles",
        json={"battleSize": 2, "playerTeam": TEAM, "enemyTeam": ENEMY},
    )
    assert missing_player.status_code == 422
    assert "playerFormation is required" in missing_player.text

    missing_player_enemy = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 2,
            "playerTeam": HTTP_UNLOCKED_TEAM,
            "enemyTeam": ENEMY,
            "playerFormation": "front-rear",
            "enemyControlMode": "player",
        },
    )
    assert missing_player_enemy.status_code == 422
    assert "enemyFormation is required" in missing_player_enemy.text

    invalid_value = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 2,
            "playerTeam": TEAM,
            "enemyTeam": ENEMY,
            "playerFormation": "diagonal",
            "enemyFormation": "front-rear",
        },
    )
    assert invalid_value.status_code == 422

    wrong_size = client.post(
        "/api/v1/battles",
        json={
            "scenarioId": "ragnar-vs-nighthawk",
            "playerFormation": "front-rear",
        },
    )
    assert wrong_size.status_code == 422
    assert len(registry._sessions) == sessions_before


def test_http_computer_2v2_can_omit_enemy_formation():
    response = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 2,
            "playerTeam": HTTP_UNLOCKED_TEAM,
            "enemyCompositionMode": "random",
            "enemyControlMode": "computer",
            "playerFormation": "side-by-side",
            "seed": 1801,
        },
    )
    assert response.status_code == 200
    snapshot = response.json()["data"]["snapshot"]
    assert snapshot["formations"]["friendly"] == "side-by-side"
    assert snapshot["formations"]["enemy"] in FORMATION_IDS


def test_adapter_assigns_constructor_positions_and_serializes_them():
    session, envelope = BattleAdapter().create_battle(
        battle_size=2,
        player_team=TEAM,
        enemy_team=ENEMY,
        player_formation="front-rear",
        enemy_formation="side-by-side",
        seed=1802,
    )
    assert [hero.position for hero in session.game.player_heroes] == [
        "front",
        "rear",
    ]
    assert [hero.position for hero in session.game.opponent_heroes] == [
        "front",
        "front",
    ]
    snapshot = envelope["data"]["snapshot"]
    assert snapshot["formations"] == {
        "friendly": "front-rear",
        "enemy": "side-by-side",
    }
    assert [
        snapshot["combatants"][combatant_id]["position"]
        for combatant_id in snapshot["sides"][0]["combatantIds"]
    ] == ["front", "rear"]


def test_seeded_computer_formation_is_reproducible():
    kwargs = dict(
        battle_size=2,
        player_team=TEAM,
        enemy_composition_mode="random",
        enemy_control_mode="computer",
        player_formation="front-rear",
        seed=1803,
    )
    first = BattleAdapter().create_battle(**kwargs)[0]
    second = BattleAdapter().create_battle(**kwargs)[0]
    assert first.enemy_formation == second.enemy_formation
    assert first.enemy_formation in FORMATION_IDS


def test_all_live_roster_constructors_keep_default_position_compatibility():
    adapter = BattleAdapter()
    for definition_id, definition in HERO_ROSTER.items():
        hero = definition["class"](
            adapter.engine_data,
            f"Compatibility {definition_id}",
            "Group_A",
            True,
        )
        assert hero.position == "front"


def test_generator_and_summon_construction_keep_front_default():
    adapter = BattleAdapter()
    generated = HeroGenerator(adapter.engine_data).generate_hero_simulation(
        "Group_A", Warrior_Weapon_Master
    )
    summoned = SkeletonWarrior(
        adapter.engine_data,
        "UI-018 Skeleton",
        "Group_A",
        generated,
        3,
        "undead",
    )
    assert generated.position == "front"
    assert summoned.position == "front"


def test_melee_legal_targets_respect_alive_front_defender():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=TEAM,
        enemy_team=ENEMY,
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=1804,
    )
    actor = session.game.player_heroes[0]
    front, rear = session.game.opponent_heroes
    fatal_strike = next(skill for skill in actor.skills if skill.name == "Fatal Strike")

    assert adapter._valid_target_ids(session, actor, fatal_strike) == [
        adapter._combatant_id(session, front)
    ]
    front.hp = 0
    assert adapter._valid_target_ids(session, actor, fatal_strike) == [
        adapter._combatant_id(session, rear)
    ]


def test_computer_melee_target_is_reconciled_to_adapter_legality():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=ENEMY,
        enemy_team=TEAM,
        player_formation="front-rear",
        enemy_formation="front-rear",
        enemy_control_mode="computer",
        seed=1807,
    )
    friendly_front, friendly_rear = session.game.player_heroes
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
    assert skill_event["targetIds"] == [
        adapter._combatant_id(session, friendly_front)
    ]


@pytest.mark.parametrize(
    ("attack_type", "attacker_position", "defender_position", "expected"),
    [
        ("melee", "front", "rear", 100),
        ("melee", "rear", "front", 70),
        ("ranged_projectile", "front", "front", 100),
        ("ranged_projectile", "front", "rear", 80),
        ("ranged_projectile", "rear", "front", 80),
        ("ranged_projectile", "rear", "rear", 60),
        ("ranged_instant", "rear", "rear", 100),
        ("NA", "rear", "rear", 100),
        ("future_type", "rear", "rear", 100),
    ],
)
def test_take_damage_calculation_applies_once_with_floor_and_clamp(
    attack_type, attacker_position, defender_position, expected
):
    attacker = object.__new__(Hero)
    defender = object.__new__(Hero)
    attacker.position = attacker_position
    defender.position = defender_position
    assert defender.take_damage_calculation(100, attack_type, attacker) == expected
    assert defender.take_damage_calculation(-10, attack_type, attacker) == 0


def test_take_damage_pipeline_does_not_apply_position_modifier_twice():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=TEAM,
        enemy_team=ENEMY,
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=1808,
    )
    attacker = session.game.player_heroes[1]
    defender = session.game.opponent_heroes[0]
    defender.hp = 100
    defender.hp_max = 100

    defender.take_damage(10, "melee", attacker)

    assert defender.hp == 93


def test_skill_dispatcher_only_passes_attack_type_to_opted_in_actions():
    calls = []

    def legacy(target, mode):
        calls.append((target, mode))
        return "legacy"

    def modern(target, attack_type="NA"):
        calls.append((target, attack_type))
        return "modern"

    legacy_skill = Skill(None, "Legacy", legacy, "single", "damage")
    modern_skill = Skill(
        None,
        "Modern",
        modern,
        "single",
        "damage",
        attack_type="melee",
    )

    assert legacy_skill._call_skill_action("target", "opponent") == "legacy"
    assert modern_skill._call_skill_action("target") == "modern"
    assert calls == [("target", "opponent"), ("target", "melee")]


@pytest.mark.parametrize(
    ("definition_id", "skill_name", "expected_attack_type"),
    [
        ("hero.warrior.weapon_master", "Fatal Strike", "melee"),
        ("hero.warrior.weapon_master", "Armor Crush", "melee"),
        ("hero.warrior.defence", "Devastate", "melee"),
        ("hero.warrior.defence", "Shield Bash", "melee"),
        ("hero.warrior.defence", "Shield Lash", "ranged_projectile"),
        ("hero.warrior.berserker", "Moon Slash", "ranged_instant"),
        ("hero.warrior.berserker", "Strike of Meteorite", "melee"),
    ],
)
def test_live_warrior_skills_propagate_declared_attack_type(
    definition_id, skill_name, expected_attack_type
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=["hero.rogue.comprehensiveness", definition_id],
        enemy_team=ENEMY,
        player_formation="front-rear",
        enemy_formation="side-by-side",
        seed=1805,
    )
    actor = session.game.player_heroes[1]
    targets = session.game.opponent_heroes
    captured = []

    for target in targets:
        def capture(damage, attack_type="NA", attacker=None, *, _target=target):
            captured.append((_target, damage, attack_type, attacker))
            return "captured"

        target.take_damage = capture

    skill = next(skill for skill in actor.skills if skill.name == skill_name)
    skill.evasion_check = lambda _target: False
    chosen_targets = targets if skill.target_type == "multi" else targets[0]
    skill.execute(chosen_targets)

    assert captured
    assert all(call[2] == expected_attack_type for call in captured)
    assert all(call[3] is actor for call in captured)


@pytest.mark.parametrize(
    "skill_name",
    ["Fireball", "Arcane Missiles", "Frost Bolt"],
)
def test_live_mage_projectiles_propagate_attack_type_through_adapter(skill_name):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=[
            "hero.mage.comprehensiveness",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=ENEMY,
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=1809,
    )
    actor = session.game.player_heroes[0]
    targets = session.game.opponent_heroes
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    captured = []
    for target in targets:
        def capture(damage, attack_type="NA", attacker=None, *, _target=target):
            captured.append((_target, damage, attack_type, attacker))
            return "captured"

        target.take_damage = capture

    skill = next(skill for skill in actor.skills if skill.name == skill_name)
    skill.evasion_check = lambda _target: False
    action = next(
        action
        for action in adapter._legal_actions(session, actor)
        if action["skillId"] == adapter._skill_id(actor, skill)
    )
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.ui018.{skill_name}",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )

    assert result["accepted"] is True
    assert len(captured) == action["minimumTargets"]
    assert all(call[2] == "ranged_projectile" for call in captured)
    assert all(call[3] is actor for call in captured)


def test_strike_of_meteorite_propagates_attack_type_during_blood_frenzy():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        player_team=["hero.warrior.berserker"],
        enemy_team=["hero.rogue.comprehensiveness"],
        seed=1806,
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    actor.status["blood_frenzy"] = True
    captured = []

    def capture(damage, attack_type="NA", attacker=None):
        captured.append((damage, attack_type, attacker))
        return "captured"

    target.take_damage = capture
    skill = next(
        skill for skill in actor.skills if skill.name == "Strike of Meteorite"
    )
    skill.evasion_check = lambda _target: False
    skill.execute(target)

    assert len(captured) == 1
    assert captured[0][1:] == ("melee", actor)
