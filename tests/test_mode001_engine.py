from __future__ import annotations

from pathlib import Path
import random
import sqlite3

import pytest

from battle_api.adapter import BattleAdapter, ENGINE_RANDOM_LOCK
from battle_api.progression import ProgressionStore, STAGE_BATTLES, StageAccessError


def _learner_mage_turn(monkeypatch: pytest.MonkeyPatch, *, seed: int = 9101):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=seed,
        battle_size=2,
        player_team=[
            "hero.warrior.weapon_master",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.mage.comprehensiveness",
            "hero.warrior.weapon_master",
        ],
        enemy_control_mode="player",
        player_formation="side-by-side",
        enemy_formation="side-by-side",
        fixed_computer_formation=True,
        stage_id="warriors-barrack",
        stage_battle_index=1,
        stage_mode="learner",
    )
    actor = session.game.opponent_heroes[0]
    actor.is_player_controlled = False
    actor.actioned = False
    session.game.unactioned_sorted_heroes = [actor]
    return adapter, session, actor


def test_learner_samples_only_a_legal_exact_multi_target_action(
    monkeypatch: pytest.MonkeyPatch,
):
    adapter, session, actor = _learner_mage_turn(monkeypatch)
    for skill in actor.skills:
        skill.if_cooldown = skill.name != "Arcane Missiles"
    monkeypatch.setattr(
        actor,
        "ai_choose_skill",
        lambda *_args: pytest.fail("Learner must not call hero strategy AI"),
    )
    captured: list[dict] = []

    def resolve(_session, command):
        captured.append(command)
        _session.game.game_state = "game_over"
        return {"events": []}

    monkeypatch.setattr(adapter, "_resolve", resolve)

    adapter._drain_automatic_turns(session)

    assert len(captured) == 1
    command = captured[0]
    action = adapter._legal_actions(session, actor, include_computer=True)[0]
    assert command["skillId"] == action["skillId"]
    assert len(command["targetIds"]) == 2
    assert len(set(command["targetIds"])) == 2
    assert set(command["targetIds"]).issubset(action["validTargetIds"])


def test_learner_no_legal_action_uses_skip_instead_of_fabricating_command(
    monkeypatch: pytest.MonkeyPatch,
):
    adapter, session, actor = _learner_mage_turn(monkeypatch)
    for skill in actor.skills:
        skill.if_cooldown = True
    skips: list[str] = []

    def skip(_session, skipped_actor, directive):
        assert skipped_actor is actor
        skips.append(directive.reason_id)
        _session.game.game_state = "game_over"
        return []

    monkeypatch.setattr(adapter, "_skip_turn", skip)
    monkeypatch.setattr(
        adapter,
        "_resolve",
        lambda *_args: pytest.fail("No command may be fabricated"),
    )

    adapter._drain_automatic_turns(session)

    assert skips == ["noLegalAction"]


def test_learner_zero_target_skill_emits_an_empty_target_set(
    monkeypatch: pytest.MonkeyPatch,
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=9103,
        player_team=["hero.warrior.weapon_master"],
        enemy_team=["hero.rogue.comprehensiveness"],
        enemy_control_mode="player",
        stage_id="warriors-barrack",
        stage_battle_index=1,
        stage_mode="learner",
    )
    actor = session.game.opponent_heroes[0]
    actor.is_player_controlled = False
    actor.actioned = False
    session.game.unactioned_sorted_heroes = [actor]
    for skill in actor.skills:
        skill.if_cooldown = skill.name != "Shadow Evasion"
    monkeypatch.setattr(
        actor,
        "ai_choose_skill",
        lambda *_args: pytest.fail("Learner must not call hero strategy AI"),
    )
    captured: list[dict] = []

    def resolve(_session, command):
        captured.append(command)
        _session.game.game_state = "game_over"
        return {"events": []}

    monkeypatch.setattr(adapter, "_resolve", resolve)

    adapter._drain_automatic_turns(session)

    assert len(captured) == 1
    assert captured[0]["skillId"] == "skill.rogue.shadow_evasion"
    assert captured[0]["targetIds"] == []


def test_learner_same_seed_reproduces_legal_action_and_target_selection(
    monkeypatch: pytest.MonkeyPatch,
):
    def chosen_command(seed: int) -> dict:
        adapter, session, actor = _learner_mage_turn(monkeypatch, seed=seed)
        monkeypatch.setattr(
            actor,
            "ai_choose_skill",
            lambda *_args: pytest.fail("Learner must not call hero strategy AI"),
        )
        legal_actions = {
            action["skillId"]: action
            for action in adapter._legal_actions(
                session, actor, include_computer=True
            )
        }
        captured: list[dict] = []

        def resolve(_session, command):
            captured.append(command)
            _session.game.game_state = "game_over"
            return {"events": []}

        monkeypatch.setattr(adapter, "_resolve", resolve)
        with ENGINE_RANDOM_LOCK:
            global_state = random.getstate()
            try:
                random.setstate(session.rng_state)
                adapter._drain_automatic_turns(session)
            finally:
                random.setstate(global_state)
        assert len(captured) == 1
        command = captured[0]
        action = legal_actions[command["skillId"]]
        assert len(command["targetIds"]) == action["minimumTargets"]
        assert len(set(command["targetIds"])) == len(command["targetIds"])
        assert set(command["targetIds"]).issubset(action["validTargetIds"])
        return {
            "skillId": command["skillId"],
            "targetIds": command["targetIds"],
        }

    assert chosen_command(9104) == chosen_command(9104)


@pytest.mark.parametrize(
    ("stage_mode", "actor_side"),
    [("tactics", "enemy"), ("learner", "friendly")],
)
def test_non_learner_enemy_keeps_existing_strategy_path(
    monkeypatch: pytest.MonkeyPatch, stage_mode: str, actor_side: str
):
    adapter, session, enemy = _learner_mage_turn(monkeypatch)
    session.stage_mode = stage_mode
    actor = enemy if actor_side == "enemy" else session.game.player_heroes[0]
    actor.is_player_controlled = False
    actor.actioned = False
    session.game.unactioned_sorted_heroes = [actor]
    skill = next(item for item in actor.skills if not item.is_passive)
    calls: list[str] = []
    monkeypatch.setattr(
        actor,
        "ai_choose_skill",
        lambda *_args: calls.append("skill") or skill,
    )
    target = actor.opponents[0]
    monkeypatch.setattr(
        actor,
        "ai_choose_target",
        lambda *_args: calls.append("target") or target,
    )

    def resolve(_session, _command):
        _session.game.game_state = "game_over"
        return {"events": []}

    monkeypatch.setattr(adapter, "_resolve", resolve)

    adapter._drain_automatic_turns(session)

    assert calls == ["skill", "target"]


def test_mode_does_not_change_seeded_combatant_construction():
    def create(mode: str):
        return BattleAdapter().create_battle(
            seed=9102,
            battle_size=2,
            player_team=[
                "hero.warrior.weapon_master",
                "hero.priest.comprehensiveness",
            ],
            enemy_team=[
                "hero.mage.comprehensiveness",
                "hero.warrior.weapon_master",
            ],
            enemy_control_mode="player",
            player_formation="side-by-side",
            enemy_formation="side-by-side",
            fixed_computer_formation=True,
            stage_id="warriors-barrack",
            stage_battle_index=1,
            stage_mode=mode,
        )[0]

    learner = create("learner")
    tactics = create("tactics")

    def stats(session):
        return [
            (
                hero.profession,
                hero.hp_max,
                hero.damage,
                hero.defense,
                hero.agility,
                hero.fire_resistance,
                hero.frost_resistance,
                hero.arcane_resistance,
                hero.shadow_resistance,
                hero.death_resistance,
                hero.poison_resistance,
                hero.nature_resistance,
            )
            for hero in session.game.player_heroes + session.game.opponent_heroes
        ]

    assert stats(learner) == stats(tactics)


def test_tactics_unlock_and_completion_are_campaign_scoped_and_reward_free(
    tmp_path: Path,
):
    store = ProgressionStore(tmp_path / "mode001-engine.sqlite3")
    store.create_save_slot(1)
    for battle in STAGE_BATTLES["warriors-barrack"]:
        store.commit_victory(
            battle_id=f"learner.{battle.battle_index}",
            stage_id="warriors-barrack",
            battle_index=battle.battle_index,
            mode="learner",
        )

    with pytest.raises(StageAccessError, match="Learner mode"):
        store.assert_stage_battle_access(
            "paladins-altar", 9, mode="tactics"
        )
    store.assert_stage_battle_access("warriors-barrack", 9, mode="tactics")
    before = store.read_progression()
    result = store.commit_victory(
        battle_id="tactics.9",
        stage_id="warriors-barrack",
        battle_index=9,
        mode="tactics",
    )

    assert result["newlyGrantedRewards"] == []
    assert result["progression"]["grantedRewards"] == before["grantedRewards"]
    warrior = next(
        item
        for item in result["progression"]["stageProgress"]
        if item["stageId"] == "warriors-barrack"
    )
    assert warrior["modes"]["tactics"]["completedBattleIndices"] == [9]
    assert ProgressionStore(store.database_path).read_progression() == result["progression"]


def test_schema_v3_migration_backfills_learner_history_without_tactics(
    tmp_path: Path,
):
    database = tmp_path / "mode001-v3.sqlite3"
    original = ProgressionStore(database)
    original.create_save_slot(1)
    for battle_index in range(1, 4):
        original.commit_victory(
            battle_id=f"legacy.{battle_index}",
            stage_id="warriors-barrack",
            battle_index=battle_index,
        )
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE stage_mode_completions")
        connection.execute(
            "UPDATE metadata SET value = '3' WHERE key = 'schema_version'"
        )

    migrated = ProgressionStore(database).read_progression()
    warrior = next(
        item
        for item in migrated["stageProgress"]
        if item["stageId"] == "warriors-barrack"
    )

    assert warrior["modes"]["learner"]["completedBattleIndices"] == [1, 2, 3]
    assert warrior["modes"]["tactics"] == {
        "available": False,
        "completed": False,
        "completedBattleIndices": [],
    }
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "4"
