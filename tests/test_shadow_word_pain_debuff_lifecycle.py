"""Regression coverage for Shadow Word Pain's object-owned debuff lifecycle."""

from __future__ import annotations

from battle_api.adapter import BattleAdapter


def _battle():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=1,
        player_team=["hero.priest.comprehensiveness"],
        enemy_team=["hero.warrior.defence"],
        enemy_control_mode="player",
        seed=7821,
    )
    return adapter, session.game.player_heroes[0], session.game.opponent_heroes[0], session


def test_expired_shadow_word_pain_reuses_its_debuff_object_without_raw_damage(monkeypatch):
    adapter, caster, target, session = _battle()
    monkeypatch.setattr("heroes.priest.random.randint", lambda _low, _high: 0)
    target.shadow_resistance = 0
    expected_damage = caster._shadow_word_pain_direct_damage(
        caster.damage, target.shadow_resistance, 0
    )

    target.hp = target.hp_max
    caster.shadow_word_pain(target, "ranged_instant")
    active_debuff = next(
        debuff for debuff in target.debuffs if debuff.name == "Shadow Word Pain"
    )
    assert target.hp == target.hp_max - expected_damage
    assert active_debuff.duration == 5

    active_debuff.duration = 1
    session.game.status_manager.check_heroes_status_effects(target)
    assert target.status["shadow_word_pain"] is False
    assert active_debuff not in target.debuffs
    assert active_debuff in target.buffs_debuffs_recycle_pool

    target.hp = target.hp_max
    caster.shadow_word_pain(target, "ranged_instant")
    assert target.hp == target.hp_max - expected_damage
    assert active_debuff in target.debuffs
    assert active_debuff not in target.buffs_debuffs_recycle_pool
    assert active_debuff.duration == 5
    serialized_status = next(
        status
        for status in adapter.snapshot(session)["combatants"][
            adapter._combatant_id(session, target)
        ]["statuses"]
        if status["id"] == "status.shadow_word_pain"
    )
    assert serialized_status["roundsRemaining"] == 5
    assert serialized_status["sourceCombatantId"] == adapter._combatant_id(session, caster)

    session.game.status_dispeller.dispell_status(["shadow_word_pain"], target)
    assert target.status["shadow_word_pain"] is False
    assert active_debuff not in target.debuffs
    assert active_debuff in target.buffs_debuffs_recycle_pool
