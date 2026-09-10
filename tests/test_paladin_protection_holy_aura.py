from __future__ import annotations

from battle_api.adapter import BattleAdapter
from skills import Buff


def _battle():
    adapter = BattleAdapter()
    session, envelope = adapter.create_battle(
        battle_size=2,
        player_team=["hero.paladin.protection", "hero.warrior.weapon_master"],
        enemy_team=["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=2601,
    )
    return adapter, session, envelope


def test_holy_aura_is_a_non_selectable_passive_skill_and_visible_team_buff():
    _adapter, session, envelope = _battle()
    paladin, ally = session.game.player_heroes
    snapshot = envelope["data"]["snapshot"]

    aura_skill = next(skill for skill in paladin.skills if skill.name == "Holy Aura")
    assert aura_skill.is_passive is True
    serialized_aura = next(
        skill
        for skill in snapshot["combatants"]["friendly.paladin_protection.1"]["skills"]
        if skill["displayName"] == "Holy Aura"
    )
    assert serialized_aura["isPassive"] is True
    assert all(
        action["skillId"] != "skill.paladin.holy_aura"
        for action in snapshot["legalActions"]
    )

    paladin_id = "friendly.paladin_protection.1"
    for hero in (paladin, ally):
        statuses = snapshot["combatants"][
            "friendly.paladin_protection.1"
            if hero is paladin
            else "friendly.warrior_weapon_master.2"
        ]["statuses"]
        aura = next(status for status in statuses if status["id"] == "status.holy_aura")
        assert aura["kind"] == "buff"
        assert aura["sourceCombatantId"] == paladin_id


def test_holy_aura_heals_every_living_friendly_for_twelve_when_round_starts(monkeypatch):
    _adapter, session, _envelope = _battle()
    paladin, ally = session.game.player_heroes
    paladin.hp -= 30
    ally.hp -= 30
    monkeypatch.setattr(
        "game.status_effect_manager.random.randint", lambda _low, _high: 0
    )

    session.game.update_battle_information()

    assert paladin.hp == paladin.hp_max - 18
    assert ally.hp == ally.hp_max - 18


def test_holy_aura_round_healing_event_names_the_protection_paladin_source(monkeypatch):
    adapter, session, _envelope = _battle()
    paladin, ally = session.game.player_heroes
    ally.hp -= 30
    before = adapter._capture(session)
    monkeypatch.setattr(
        "game.status_effect_manager.random.randint", lambda _low, _high: 0
    )

    session.game.update_battle_information()
    events = adapter._state_delta_events(session, before, adapter._capture(session))

    healing = next(
        event
        for event in events
        if event["type"] == "healingApplied"
        and event["targetId"] == "friendly.warrior_weapon_master.2"
    )
    assert healing["amount"] == 12
    assert healing["sourceId"] == adapter._combatant_id(session, paladin)


def test_status_phase_emits_aura_then_each_dot_as_distinct_ordered_events(monkeypatch):
    """Round-status presentation follows check_heroes_status_effects order."""
    adapter, session, _envelope = _battle()
    paladin, ally = session.game.player_heroes
    ally.hp -= 40
    ally.status["bleeding_slash"] = True
    ally.bleeding_slash_duration = 2
    ally.bleeding_slash_continuous_damage = 7
    ally.status["shadow_word_pain"] = True
    ally.shadow_word_pain_debuff_duration = 2
    ally.shadow_word_pain_continuous_damage = 9
    monkeypatch.setattr(
        "game.status_effect_manager.random.randint", lambda _low, _high: 0
    )

    session.game.update_battle_information()
    ally_events = [
        event
        for event in adapter._drain_status_effect_events(session)
        if event["targetId"] == "friendly.warrior_weapon_master.2"
    ]

    assert [event["type"] for event in ally_events] == [
        "healingApplied",
        "damageApplied",
        "damageApplied",
    ]
    assert [event["amount"] for event in ally_events] == [12, 7, 9]
    assert ally_events[0]["sourceId"] == adapter._combatant_id(session, paladin)
    assert ally_events[0]["statusId"] == "status.holy_aura"
    assert [event["statusId"] for event in ally_events[1:]] == [
        "status.bleeding_slash",
        "status.shadow_word_pain",
    ]
    assert [event["hpAfter"]["current"] for event in ally_events] == [
        ally.hp_max - 28,
        ally.hp_max - 35,
        ally.hp_max - 44,
    ]
    assert [event["sequence"] for event in ally_events] == sorted(
        event["sequence"] for event in ally_events
    )


def test_holy_aura_is_removed_when_its_paladin_source_is_defeated():
    adapter, session, _envelope = _battle()
    paladin, ally = session.game.player_heroes
    paladin.hp = 0

    session.game.refresh_holy_auras()
    snapshot = adapter.snapshot(session)

    assert ally.status["holy_aura"] is False
    assert all(
        status["id"] != "status.holy_aura"
        for status in snapshot["combatants"]["friendly.warrior_weapon_master.2"]["statuses"]
    )


def test_status_damage_records_void_connection_for_target_and_linked_summon(monkeypatch):
    """Direct linked-HP mutation must not bypass the status UI event stream."""
    adapter, session, _envelope = _battle()
    target, linked_summon = session.game.player_heroes
    target.status["void_connection"] = True
    target.summoned_unit = linked_summon
    target.add_buff(
        Buff("Void Connection", duration=3, initiator=linked_summon, effect=0.5)
    )
    target.status["bleeding_slash"] = True
    target.bleeding_slash_duration = 2
    target.bleeding_slash_continuous_damage = 10
    monkeypatch.setattr(
        "game.status_effect_manager.random.randint", lambda _low, _high: 0
    )

    session.game.status_effect_events.clear()
    session.game.status_manager.check_heroes_status_effects(target)
    events = adapter._drain_status_effect_events(session)
    shared_damage = [
        event
        for event in events
        if event["type"] == "damageApplied"
        and event["statusId"] == "status.bleeding_slash"
    ]

    assert [event["targetId"] for event in shared_damage] == [
        "friendly.warrior_weapon_master.2",
        "friendly.paladin_protection.1",
    ]
    assert [event["amount"] for event in shared_damage] == [5, 5]
    assert [event["sequence"] for event in shared_damage] == sorted(
        event["sequence"] for event in shared_damage
    )
