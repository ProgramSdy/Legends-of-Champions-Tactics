"""Thin session adapter around the existing mutable Python battle engine.

The adapter owns identity, validation, serialization and event envelopes. It
deliberately delegates every rule-bearing action to ``Skill.execute`` and the
existing ``Game`` round/status methods.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
import random
import re
import secrets
import threading
import uuid
from typing import Any

import pandas as pd

from game.game import Game
from heroes.rogue import Rogue_Comprehensiveness
from heroes.warrior import Warrior_Weapon_Master

CONTRACT_VERSION = "1.0"
ROOT = Path(__file__).resolve().parents[1]
ENGINE_RANDOM_LOCK = threading.RLock()

HERO_DEFINITIONS = {
    "Warrior_Weapon_Master": "hero.warrior.weapon_master",
    "Rogue_Comprehensiveness": "hero.rogue.comprehensiveness",
}

SKILL_DEFINITIONS = {
    ("Warrior_Weapon_Master", "Fatal Strike"): "skill.warrior.fatal_strike",
    ("Warrior_Weapon_Master", "Armor Crush"): "skill.warrior.armor_crush",
    ("Warrior_Weapon_Master", "Antivenom Potion"): "skill.warrior.antivenom_potion",
    ("Rogue_Comprehensiveness", "Sharp Blade"): "skill.rogue.sharp_blade",
    ("Rogue_Comprehensiveness", "Poisoned Dagger"): "skill.rogue.poisoned_dagger",
    ("Rogue_Comprehensiveness", "Shadow Evasion"): "skill.rogue.shadow_evasion",
}

STATUS_KINDS = {
    "fatal_strike": "debuff",
    "armor_breaker": "debuff",
    "bleeding_armor_crush": "debuff",
    "wound_armor_crush": "debuff",
    "antivenom_potion": "buff",
    "bleeding_sharp_blade": "debuff",
    "poisoned_dagger": "debuff",
    "shadow_evasion": "buff",
}

STATUS_DURATIONS = {
    "fatal_strike": None,  # duration is held on the matching Debuff
    "armor_breaker": "armor_breaker_duration",
    "bleeding_armor_crush": "bleeding_armor_crush_duration",
    "wound_armor_crush": "wound_armor_crush_duration",
    "antivenom_potion": None,  # duration is held on the matching Buff
    "bleeding_sharp_blade": "sharp_blade_debuff_duration",
    "poisoned_dagger": "poisoned_dagger_debuff_duration",
    "shadow_evasion": "shadow_evasion_buff_duration",
}

STATUS_ENGINE_NAMES = {
    "fatal_strike": "Fatal Strike",
    "antivenom_potion": "Antivenom Potion",
}


class BattleAdapterError(Exception):
    """Structured, mutation-free command rejection."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class _EngineData:
    """Headless subset of System_initialization required by Hero constructors."""

    def __init__(self) -> None:
        basic = ROOT / "data" / "Hero_basic_property.xlsx"
        resistance = ROOT / "data" / "Hero_resistance.xlsx"
        self.df_hero_basic_property = pd.read_excel(basic, sheet_name="Property List")
        self.df_hero_resistance = pd.read_excel(resistance, sheet_name="Resistance List")
        self.df_hero_basic_property.set_index(
            self.df_hero_basic_property.columns[0], inplace=True
        )
        self.df_hero_resistance.set_index(
            self.df_hero_resistance.columns[0], inplace=True
        )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


@dataclass
class BattleSession:
    battle_id: str
    game: Game
    seed: int | None
    rng_state: object
    revision: int = 0
    event_sequence: int = 0
    command_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    object_ids: dict[int, str] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock)


class BattleAdapter:
    """Creates and advances engine-backed battle sessions."""

    def __init__(self) -> None:
        self._engine_data: _EngineData | None = None

    @property
    def engine_data(self) -> _EngineData:
        if self._engine_data is None:
            self._engine_data = _EngineData()
        return self._engine_data

    def create_battle(
        self, *, seed: int | None = None, battle_id: str | None = None
    ) -> tuple[BattleSession, dict[str, Any]]:
        with ENGINE_RANDOM_LOCK:
            global_state = random.getstate()
            try:
                # Seeded sessions are reproducible. Unseeded sessions use an
                # independent entropy source so restoring the module RNG below
                # cannot accidentally clone the same battle stream.
                random.seed(seed if seed is not None else secrets.randbits(256))
                ragnar = Warrior_Weapon_Master(
                    self.engine_data, "Ragnar", "Group_A", True
                )
                nighthawk = Rogue_Comprehensiveness(
                    self.engine_data, "Nighthawk", "Group_B", True
                )
                game = Game([ragnar], [nighthawk], "simulation")
                game.game_initialization()
                game.start_round()
                session = BattleSession(
                    battle_id=battle_id or f"battle.{uuid.uuid4().hex}",
                    game=game,
                    seed=seed,
                    rng_state=random.getstate(),
                )
                session.object_ids[id(ragnar)] = "friendly.ragnar"
                session.object_ids[id(nighthawk)] = "enemy.nighthawk"
                events = [
                    self._event(session, "battleStarted", message="Battle started."),
                    self._event(
                        session,
                        "roundStarted",
                        message=f"Round {game.round_counter} started.",
                    ),
                    self._turn_started_event(session),
                ]
                return session, self.envelope(session, {"events": events, "snapshot": self.snapshot(session)})
            finally:
                random.setstate(global_state)

    def envelope(self, session: BattleSession, data: Any) -> dict[str, Any]:
        return {
            "contractVersion": CONTRACT_VERSION,
            "battleId": session.battle_id,
            "revision": session.revision,
            "data": data,
        }

    def snapshot(self, session: BattleSession) -> dict[str, Any]:
        game = session.game
        ended = self._is_ended(game)
        active = None if ended else self._current_actor(game)
        active_id = self._combatant_id(session, active) if active else None
        living = [hero for hero in game.heroes if hero.hp > 0]
        ordered = sorted(living, key=lambda hero: hero.agility, reverse=True)
        total = len(ordered)
        acted = sum(bool(hero.actioned) for hero in ordered)
        outcome = self._outcome(game) if ended else None
        return {
            "phase": "ended" if ended else "awaitingCommand",
            "round": game.round_counter,
            "turn": {"index": min(acted + (1 if active else 0), total), "total": total},
            "activeCombatantId": active_id,
            "outcome": outcome,
            "sides": [
                {
                    "id": side,
                    "combatantIds": [
                        self._combatant_id(session, hero)
                        for hero in (game.player_heroes if side == "friendly" else game.opponent_heroes)
                    ],
                    "maxSlots": 3,
                }
                for side in ("friendly", "enemy")
            ],
            "combatants": {
                self._combatant_id(session, hero): self._serialize_combatant(session, hero)
                for hero in game.player_heroes + game.opponent_heroes
            },
            "turnOrder": [
                {
                    "combatantId": self._combatant_id(session, hero),
                    "hasActed": bool(hero.actioned),
                    "isCurrent": hero is active,
                }
                for hero in ordered
            ],
            "legalActions": self._legal_actions(session, active) if active else [],
        }

    def submit(self, session: BattleSession, command: dict[str, Any]) -> dict[str, Any]:
        command_id = command.get("commandId", "")
        with session.lock:
            if command_id in session.command_results:
                return deepcopy(session.command_results[command_id])
            try:
                self._validate(session, command)
            except BattleAdapterError as exc:
                result = self._rejection(session, command_id, exc)
                if command_id:
                    session.command_results[command_id] = deepcopy(result)
                return result

            with ENGINE_RANDOM_LOCK:
                global_state = random.getstate()
                try:
                    random.setstate(session.rng_state)
                    result = self._resolve(session, command)
                    session.rng_state = random.getstate()
                finally:
                    random.setstate(global_state)
            session.command_results[command_id] = deepcopy(result)
            return result

    def _validate(self, session: BattleSession, command: dict[str, Any]) -> None:
        if command.get("type") != "useSkill":
            raise BattleAdapterError("invalidCommand", "Only useSkill is supported.")
        if self._is_ended(session.game):
            raise BattleAdapterError("battleEnded", "The battle has ended.")
        if command.get("expectedRevision") != session.revision:
            raise BattleAdapterError("staleRevision", "The expected revision is stale.")
        actor = self._current_actor(session.game)
        if actor is None or command.get("actorId") != self._combatant_id(session, actor):
            raise BattleAdapterError("notYourTurn", "The actor is not the current combatant.")
        skill = self._skill_by_id(actor, command.get("skillId"))
        if skill is None or not skill.is_available or skill.if_cooldown:
            raise BattleAdapterError("illegalSkill", "The skill does not exist or is unavailable.")
        targets = command.get("targetIds")
        if not isinstance(targets, list):
            raise BattleAdapterError("invalidCommand", "targetIds must be an array.")
        minimum = 0 if skill.target_qty == 0 else skill.target_qty
        maximum = skill.target_qty
        if len(targets) < minimum or len(targets) > maximum:
            raise BattleAdapterError(
                "illegalTargets", f"The skill requires {minimum} to {maximum} targets."
            )
        if len(set(targets)) != len(targets):
            raise BattleAdapterError("illegalTargets", "Duplicate targets are not allowed.")
        valid_ids = set(self._valid_target_ids(session, actor, skill))
        if any(target_id not in valid_ids for target_id in targets):
            raise BattleAdapterError("illegalTargets", "One or more targets are illegal.")

    def _resolve(self, session: BattleSession, command: dict[str, Any]) -> dict[str, Any]:
        game = session.game
        actor = self._current_actor(game)
        assert actor is not None
        skill = self._skill_by_id(actor, command["skillId"])
        assert skill is not None
        targets = [self._hero_by_id(session, value) for value in command["targetIds"]]
        before = self._capture(session)
        events = [
            self._event(
                session,
                "skillStarted",
                sourceId=self._combatant_id(session, actor),
                targetIds=command["targetIds"],
                skillId=command["skillId"],
                effectHint=self._effect_hint(skill),
                message=f"{actor.name} used {skill.name}.",
            )
        ]
        if skill.skill_type == "damage":
            events.append(
                self._event(
                    session,
                    "characterMoved",
                    sourceId=self._combatant_id(session, actor),
                    targetId=command["targetIds"][0] if command["targetIds"] else None,
                    skillId=command["skillId"],
                    movement="lunge",
                    effectHint="melee",
                    message=f"{actor.name} moved to attack.",
                )
            )
        # The legacy Skill boundary uses the literal sentinel ``["none"]`` for
        # targetless buffs; preserve that engine convention at this seam.
        skill.execute(["none"] if skill.target_qty == 0 else targets)
        after = self._capture(session)
        events.extend(self._mutation_events(session, actor, skill, targets, before, after))
        actor.actioned = True
        if game.unactioned_sorted_heroes and game.unactioned_sorted_heroes[0] is actor:
            game.unactioned_sorted_heroes.pop(0)
        else:
            game.unactioned_sorted_heroes = [
                hero for hero in game.unactioned_sorted_heroes if hero is not actor
            ]
        game.update_allies_opponents_list()
        events.append(
            self._event(
                session,
                "turnEnded",
                sourceId=self._combatant_id(session, actor),
                message=f"{actor.name}'s turn ended.",
            )
        )
        if len(game.check_groups_status()) <= 1:
            game.game_state = "game_over"
        elif not [hero for hero in game.unactioned_sorted_heroes if hero.hp > 0]:
            game.end_round()
            if game.game_state != "game_over":
                round_before = self._capture(session)
                game.start_round()
                events.append(
                    self._event(
                        session,
                        "roundStarted",
                        message=f"Round {game.round_counter} started.",
                    )
                )
                events.extend(
                    self._state_delta_events(
                        session, round_before, self._capture(session)
                    )
                )
        if self._is_ended(game):
            events.append(
                self._event(session, "battleEnded", message=self._outcome_message(game))
            )
        else:
            events.append(self._turn_started_event(session))
        session.revision += 1
        return {
            "accepted": True,
            "commandId": command["commandId"],
            "revision": session.revision,
            "events": events,
            "snapshot": self.snapshot(session),
        }

    def _capture(self, session: BattleSession) -> dict[str, Any]:
        return {
            self._combatant_id(session, hero): {
                "hp": hero.hp,
                "maximum": hero.hp_max,
                "statuses": self._active_statuses(hero),
            }
            for hero in session.game.player_heroes + session.game.opponent_heroes
        }

    def _mutation_events(self, session, actor, skill, targets, before, after):
        events = []
        actor_id = self._combatant_id(session, actor)
        for target in targets:
            target_id = self._combatant_id(session, target)
            old, new = before[target_id], after[target_id]
            if new["hp"] < old["hp"]:
                events.append(
                    self._event(
                        session,
                        "damageApplied",
                        sourceId=actor_id,
                        targetId=target_id,
                        skillId=self._skill_id(actor, skill),
                        amount=old["hp"] - new["hp"],
                        hpAfter={"current": new["hp"], "maximum": new["maximum"]},
                        effectHint=self._effect_hint(skill),
                        message=f"{target.name} took {old['hp'] - new['hp']} damage.",
                    )
                )
            elif skill.skill_type == "damage":
                events.append(
                    self._event(
                        session,
                        "attackEvaded",
                        sourceId=actor_id,
                        targetId=target_id,
                        skillId=self._skill_id(actor, skill),
                        movement="offset",
                        message=f"{target.name} evaded {skill.name}.",
                    )
                )
        for combatant_id, old in before.items():
            new = after[combatant_id]
            if new["hp"] > old["hp"]:
                events.append(
                    self._event(
                        session,
                        "healingApplied",
                        sourceId=actor_id,
                        targetId=combatant_id,
                        skillId=self._skill_id(actor, skill),
                        amount=new["hp"] - old["hp"],
                        hpAfter={"current": new["hp"], "maximum": new["maximum"]},
                        effectHint="healing",
                        message=f"{combatant_id} recovered {new['hp'] - old['hp']} HP.",
                    )
                )
            for status_id in new["statuses"].keys() - old["statuses"].keys():
                status = new["statuses"][status_id]
                events.append(
                    self._event(
                        session,
                        "statusApplied",
                        sourceId=actor_id,
                        targetId=combatant_id,
                        skillId=self._skill_id(actor, skill),
                        statusId=status_id,
                        roundsRemaining=status["roundsRemaining"],
                        effectHint="status",
                        message=f"{status_id} was applied to {combatant_id}.",
                    )
                )
            for status_id in old["statuses"].keys() - new["statuses"].keys():
                events.append(
                    self._event(
                        session,
                        "statusRemoved",
                        sourceId=actor_id,
                        targetId=combatant_id,
                        skillId=self._skill_id(actor, skill),
                        statusId=status_id,
                        effectHint="status",
                        message=f"{status_id} was removed from {combatant_id}.",
                    )
                )
            if old["hp"] > 0 and new["hp"] <= 0:
                events.append(
                    self._event(
                        session,
                        "characterDefeated",
                        sourceId=actor_id,
                        targetId=combatant_id,
                        message=f"{combatant_id} was defeated.",
                    )
                )
        return events

    def _state_delta_events(self, session, before, after):
        """Serialize engine-owned round-start mutations without reading prose."""
        events = []
        for combatant_id, old in before.items():
            new = after[combatant_id]
            if new["hp"] < old["hp"]:
                events.append(
                    self._event(
                        session,
                        "damageApplied",
                        targetId=combatant_id,
                        amount=old["hp"] - new["hp"],
                        hpAfter={"current": new["hp"], "maximum": new["maximum"]},
                        effectHint="status",
                        message=f"{combatant_id} took {old['hp'] - new['hp']} status damage.",
                    )
                )
            elif new["hp"] > old["hp"]:
                events.append(
                    self._event(
                        session,
                        "healingApplied",
                        targetId=combatant_id,
                        amount=new["hp"] - old["hp"],
                        hpAfter={"current": new["hp"], "maximum": new["maximum"]},
                        effectHint="healing",
                        message=f"{combatant_id} recovered {new['hp'] - old['hp']} HP.",
                    )
                )
            for status_id in new["statuses"].keys() - old["statuses"].keys():
                status = new["statuses"][status_id]
                events.append(
                    self._event(
                        session,
                        "statusApplied",
                        targetId=combatant_id,
                        statusId=status_id,
                        roundsRemaining=status["roundsRemaining"],
                        effectHint="status",
                        message=f"{status_id} was applied to {combatant_id}.",
                    )
                )
            for status_id in old["statuses"].keys() - new["statuses"].keys():
                events.append(
                    self._event(
                        session,
                        "statusRemoved",
                        targetId=combatant_id,
                        statusId=status_id,
                        effectHint="status",
                        message=f"{status_id} expired on {combatant_id}.",
                    )
                )
            if old["hp"] > 0 and new["hp"] <= 0:
                events.append(
                    self._event(
                        session,
                        "characterDefeated",
                        targetId=combatant_id,
                        message=f"{combatant_id} was defeated.",
                    )
                )
        return events

    def _serialize_combatant(self, session: BattleSession, hero) -> dict[str, Any]:
        combatant_id = self._combatant_id(session, hero)
        side = "friendly" if hero.group == "Group_A" else "enemy"
        team = session.game.player_heroes if side == "friendly" else session.game.opponent_heroes
        return {
            "id": combatant_id,
            "definitionId": HERO_DEFINITIONS.get(hero.profession, f"hero.{_slug(hero.profession)}"),
            "sideId": side,
            "slot": team.index(hero),
            "displayName": hero.name,
            "faculty": hero.faculty,
            "specialization": hero.major,
            "isSummon": bool(hero.is_summoned),
            "masterCombatantId": None,
            "summonRoundsRemaining": None,
            "isPlayerControlled": bool(hero.is_player_controlled),
            "alive": hero.hp > 0,
            "hp": {"current": hero.hp, "maximum": hero.hp_max},
            "resource": None,
            "statuses": list(self._active_statuses(hero).values()),
            "skills": [
                {
                    "id": self._skill_id(hero, skill),
                    "displayName": skill.name,
                    "targetMode": self._target_mode(skill),
                    "maximumTargets": skill.target_qty,
                    "cooldownRemaining": skill.cooldown if skill.if_cooldown else 0,
                    "available": bool(skill.is_available and not skill.if_cooldown),
                    "unavailableReason": (
                        "cooldown" if skill.if_cooldown else
                        ("unavailable" if not skill.is_available else None)
                    ),
                    "resourceCost": None,
                }
                for skill in hero.skills
            ],
        }

    def _active_statuses(self, hero) -> dict[str, dict[str, Any]]:
        result = {}
        records = list(hero.buffs) + list(hero.debuffs)
        for key, kind in STATUS_KINDS.items():
            if not hero.status.get(key, False):
                continue
            duration_attr = STATUS_DURATIONS[key]
            duration = getattr(hero, duration_attr, None) if duration_attr else None
            engine_name = STATUS_ENGINE_NAMES.get(key)
            record = next((item for item in records if item.name == engine_name), None)
            if record is not None:
                duration = record.duration
            status_id = f"status.{key}"
            result[status_id] = {
                "id": status_id,
                "instanceId": f"{status_id}.{_slug(hero.name)}",
                "kind": kind,
                "roundsRemaining": duration,
                "stacks": getattr(hero, f"{key}_stacks", None),
                "sourceCombatantId": None,
            }
        return result

    def _legal_actions(self, session: BattleSession, actor) -> list[dict[str, Any]]:
        actions = []
        for skill in actor.skills:
            if skill.if_cooldown or not skill.is_available:
                continue
            actions.append(
                {
                    "skillId": self._skill_id(actor, skill),
                    "actorId": self._combatant_id(session, actor),
                    "minimumTargets": 0 if skill.target_qty == 0 else skill.target_qty,
                    "maximumTargets": skill.target_qty,
                    "validTargetIds": self._valid_target_ids(session, actor, skill),
                }
            )
        return actions

    def _valid_target_ids(self, session: BattleSession, actor, skill) -> list[str]:
        if skill.target_qty == 0:
            return []
        pool = actor.allies if skill.skill_type in {"healing", "buffs"} else actor.opponents
        return [self._combatant_id(session, hero) for hero in pool if hero.hp > 0]

    def _skill_by_id(self, hero, skill_id):
        return next((s for s in hero.skills if self._skill_id(hero, s) == skill_id), None)

    def _skill_id(self, hero, skill) -> str:
        return SKILL_DEFINITIONS.get(
            (hero.profession, skill.name), f"skill.{_slug(hero.profession)}.{_slug(skill.name)}"
        )

    def _combatant_id(self, session: BattleSession, hero) -> str:
        if id(hero) not in session.object_ids:
            side = "friendly" if hero.group == "Group_A" else "enemy"
            session.object_ids[id(hero)] = f"{side}.{_slug(hero.name)}.{len(session.object_ids) + 1}"
        return session.object_ids[id(hero)]

    def _hero_by_id(self, session: BattleSession, combatant_id: str):
        return next(
            hero for hero in session.game.player_heroes + session.game.opponent_heroes
            if self._combatant_id(session, hero) == combatant_id
        )

    @staticmethod
    def _current_actor(game: Game):
        return next((hero for hero in game.unactioned_sorted_heroes if hero.hp > 0), None)

    @staticmethod
    def _is_ended(game: Game) -> bool:
        return game.game_state == "game_over" or len(game.check_groups_status()) <= 1

    @staticmethod
    def _target_mode(skill) -> str:
        if skill.target_qty == 0:
            return "self"
        if skill.skill_type in {"healing", "buffs"}:
            return "singleAlly" if skill.target_type == "single" else "multipleAllies"
        return "singleEnemy" if skill.target_type == "single" else "multipleEnemies"

    @staticmethod
    def _effect_hint(skill) -> str:
        if skill.skill_type == "healing":
            return "healing"
        if skill.skill_type == "buffs":
            return "status"
        return "melee"

    def _event(self, session: BattleSession, event_type: str, *, message: str, **fields):
        session.event_sequence += 1
        return {
            "id": f"{session.battle_id}.evt.{session.event_sequence:06d}",
            "sequence": session.event_sequence,
            "type": event_type,
            **{key: value for key, value in fields.items() if value is not None},
            "message": message,
        }

    def _turn_started_event(self, session: BattleSession) -> dict[str, Any]:
        actor = self._current_actor(session.game)
        assert actor is not None
        return self._event(
            session,
            "turnStarted",
            sourceId=self._combatant_id(session, actor),
            message=f"{actor.name}'s turn started.",
        )

    @staticmethod
    def _outcome(game: Game) -> dict[str, Any]:
        groups = game.check_groups_status()
        if len(groups) == 1:
            side = "friendly" if next(iter(groups)) == "Group_A" else "enemy"
            return {"kind": "victory", "winningSideId": side}
        if game.round_counter >= game.round_counter_max:
            return {"kind": "roundLimit", "winningSideId": None}
        return {"kind": "draw", "winningSideId": None}

    def _outcome_message(self, game: Game) -> str:
        outcome = self._outcome(game)
        return (
            f"{outcome['winningSideId']} won the battle."
            if outcome["winningSideId"]
            else "The battle ended without a winner."
        )

    def _rejection(self, session, command_id, exc):
        return {
            "accepted": False,
            "commandId": command_id,
            "revision": session.revision,
            "code": exc.code,
            "message": exc.message,
            "snapshot": self.snapshot(session),
        }


class BattleRegistry:
    """Thread-safe process-local session registry for development."""

    def __init__(self, adapter: BattleAdapter | None = None) -> None:
        self.adapter = adapter or BattleAdapter()
        self._sessions: dict[str, BattleSession] = {}
        self._lock = threading.RLock()

    def create(self, *, seed: int | None = None) -> tuple[BattleSession, dict[str, Any]]:
        session, envelope = self.adapter.create_battle(seed=seed)
        with self._lock:
            self._sessions[session.battle_id] = session
        return session, envelope

    def get(self, battle_id: str) -> BattleSession | None:
        with self._lock:
            return self._sessions.get(battle_id)
