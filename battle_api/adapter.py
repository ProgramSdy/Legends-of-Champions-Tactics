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
from typing import Any, Literal

import pandas as pd

from game.game import Game
from game.hero_generator import HeroGenerator
from heroes.mage import Mage_Comprehensiveness
from heroes.paladin import Paladin_Protection, Paladin_Retribution
from heroes.priest import Priest_Comprehensiveness, Priest_Discipline
from heroes.rogue import Rogue_Comprehensiveness
from heroes.warrior import Warrior_Defence, Warrior_Weapon_Master

CONTRACT_VERSION = "1.0"
ROOT = Path(__file__).resolve().parents[1]
ENGINE_RANDOM_LOCK = threading.RLock()
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

HERO_ROSTER = {
    "hero.priest.comprehensiveness": {
        "class": Priest_Comprehensiveness,
        "displayName": "Aurelia",
        "faculty": "Priest",
        "specialization": "Comprehensiveness",
    },
    "hero.priest.discipline": {
        "class": Priest_Discipline,
        "displayName": "Seraphine",
        "faculty": "Priest",
        "specialization": "Discipline",
    },
    "hero.paladin.retribution": {
        "class": Paladin_Retribution,
        "displayName": "Valerius",
        "faculty": "Paladin",
        "specialization": "Retribution",
    },
    "hero.paladin.protection": {
        "class": Paladin_Protection,
        "displayName": "Bastion",
        "faculty": "Paladin",
        "specialization": "Protection",
    },
    "hero.mage.comprehensiveness": {
        "class": Mage_Comprehensiveness,
        "displayName": "Lyra",
        "faculty": "Mage",
        "specialization": "Comprehensiveness",
    },
    "hero.warrior.defence": {
        "class": Warrior_Defence,
        "displayName": "Aegis",
        "faculty": "Warrior",
        "specialization": "Defence",
    },
    "hero.warrior.weapon_master": {
        "class": Warrior_Weapon_Master,
        "displayName": "Ragnar",
        "faculty": "Warrior",
        "specialization": "Weapon Master",
    },
    "hero.rogue.comprehensiveness": {
        "class": Rogue_Comprehensiveness,
        "displayName": "Nighthawk",
        "faculty": "Rogue",
        "specialization": "Comprehensiveness",
    },
}

HERO_DEFINITIONS = {
    definition["class"].__name__: definition_id
    for definition_id, definition in HERO_ROSTER.items()
}

STATUS_KINDS = {
    "cold": "debuff",
    "stunned": "control",
    "scoff": "control",
    "fatal_strike": "debuff",
    "armor_breaker": "debuff",
    "bleeding_armor_crush": "debuff",
    "wound_armor_crush": "debuff",
    "antivenom_potion": "buff",
    "bleeding_sharp_blade": "debuff",
    "poisoned_dagger": "debuff",
    "shadow_evasion": "buff",
    "shadow_word_pain": "debuff",
    "holy_word_redemption": "buff",
    "holy_word_punishment": "debuff",
    "wrath_of_crusader": "buff",
    "hammer_of_revenge": "debuff",
    "shield_of_righteous": "buff",
    "shield_lash": "buff",
}

STATUS_DURATIONS = {
    "cold": "cold_duration",
    "stunned": "stun_duration",
    "scoff": None,
    "fatal_strike": None,  # duration is held on the matching Debuff
    "armor_breaker": "armor_breaker_duration",
    "bleeding_armor_crush": "bleeding_armor_crush_duration",
    "wound_armor_crush": "wound_armor_crush_duration",
    "antivenom_potion": None,  # duration is held on the matching Buff
    "bleeding_sharp_blade": "sharp_blade_debuff_duration",
    "poisoned_dagger": "poisoned_dagger_debuff_duration",
    "shadow_evasion": "shadow_evasion_buff_duration",
    "shadow_word_pain": "shadow_word_pain_debuff_duration",
    "holy_word_redemption": "holy_word_redemption_duration",
    "holy_word_punishment": None,
    "wrath_of_crusader": "wrath_of_crusader_duration",
    "hammer_of_revenge": "hammer_of_revenge_duration",
    "shield_of_righteous": "shield_of_righteous_duration",
    "shield_lash": None,
}

STATUS_ENGINE_NAMES = {
    "fatal_strike": "Fatal Strike",
    "antivenom_potion": "Antivenom Potion",
    "scoff": "Scoff",
    "holy_word_redemption": "Holy Word Redemption",
    "holy_word_punishment": "Holy Word Punishment",
    "shield_lash": "Shield Lash",
}

StatusPresentation = Literal["buff", "debuff", "neutral"]

STATUS_PRESENTATION_BY_KIND: dict[str, StatusPresentation] = {
    "buff": "buff",
    "debuff": "debuff",
    "control": "debuff",
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
    battle_size: int = 1
    enemy_control_mode: str = "player"
    revision: int = 0
    event_sequence: int = 0
    presentation_log_cursor: int = 0
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
        self,
        *,
        seed: int | None = None,
        battle_id: str | None = None,
        battle_size: int = 1,
        player_team: list[str] | None = None,
        enemy_composition_mode: str = "specified",
        enemy_team: list[str] | None = None,
        enemy_control_mode: str = "player",
    ) -> tuple[BattleSession, dict[str, Any]]:
        if player_team is None:
            player_team = ["hero.warrior.weapon_master"]
        if enemy_composition_mode == "random":
            enemy_team = None
        else:
            if enemy_team is None:
                enemy_team = ["hero.rogue.comprehensiveness"]
        self._validate_creation(
            battle_size=battle_size,
            player_team=player_team,
            enemy_composition_mode=enemy_composition_mode,
            enemy_team=enemy_team,
            enemy_control_mode=enemy_control_mode,
        )
        with ENGINE_RANDOM_LOCK:
            global_state = random.getstate()
            try:
                # Seeded sessions are reproducible. Unseeded sessions use an
                # independent entropy source so restoring the module RNG below
                # cannot accidentally clone the same battle stream.
                random.seed(seed if seed is not None else secrets.randbits(256))
                selected_enemy_team = (
                    random.sample(list(HERO_ROSTER), battle_size)
                    if enemy_composition_mode == "random"
                    else list(enemy_team or [])
                )
                # Derive names from this session's seeded stream without
                # perturbing established combat/stat generation rolls.
                pre_name_state = random.getstate()
                runtime_names = self._runtime_names(
                    list(player_team) + selected_enemy_team
                )
                random.setstate(pre_name_state)
                player_heroes = self._create_team(
                    player_team,
                    runtime_names[:battle_size],
                    group="Group_A",
                    player_controlled=True,
                )
                opponent_heroes = self._create_team(
                    selected_enemy_team,
                    runtime_names[battle_size:],
                    group="Group_B",
                    player_controlled=enemy_control_mode == "player",
                )
                game = Game(player_heroes, opponent_heroes, "simulation")
                game.game_initialization()
                game.start_round()
                session = BattleSession(
                    battle_id=battle_id or f"battle.{uuid.uuid4().hex}",
                    game=game,
                    seed=seed,
                    rng_state=random.getstate(),
                    battle_size=battle_size,
                    enemy_control_mode=enemy_control_mode,
                )
                for side, heroes in (
                    ("friendly", player_heroes),
                    ("enemy", opponent_heroes),
                ):
                    for slot, hero in enumerate(heroes, start=1):
                        definition_id = HERO_DEFINITIONS[hero.profession]
                        # Preserve the established Stage 2 fixture IDs.
                        if battle_size == 1 and definition_id == "hero.warrior.weapon_master":
                            combatant_id = f"{side}.ragnar"
                        elif battle_size == 1 and definition_id == "hero.rogue.comprehensiveness":
                            combatant_id = f"{side}.nighthawk"
                        else:
                            combatant_id = (
                                f"{side}.{definition_id.removeprefix('hero.').replace('.', '_')}.{slot}"
                            )
                        session.object_ids[id(hero)] = combatant_id
                events = [
                    self._event(session, "battleStarted", message="Battle started."),
                    self._event(
                        session,
                        "roundStarted",
                        message=f"Round {game.round_counter} started.",
                    ),
                    self._turn_started_event(session),
                ]
                # Preserve the engine-owned state before an automatic opening
                # actor is drained. Clients use this only for presentation;
                # `snapshot` below remains the final authoritative state.
                opening_snapshot = self.snapshot(session)
                events.extend(self._drain_presentation_log(session))
                automatic_events = self._drain_automatic_turns(session)
                events.extend(automatic_events)
                session.rng_state = random.getstate()
                return session, self.envelope(
                    session,
                    {
                        "events": events,
                        "snapshot": self.snapshot(session),
                        "openingSnapshot": opening_snapshot,
                        "playOpening": bool(automatic_events),
                    },
                )
            finally:
                random.setstate(global_state)

    @staticmethod
    def roster() -> list[dict[str, str]]:
        return [
            {
                "definitionId": definition_id,
                "displayName": definition["displayName"],
                "faculty": definition["faculty"],
                "specialization": definition["specialization"],
            }
            for definition_id, definition in HERO_ROSTER.items()
        ]

    @staticmethod
    def _validate_creation(
        *,
        battle_size: int,
        player_team: list[str],
        enemy_composition_mode: str,
        enemy_team: list[str] | None,
        enemy_control_mode: str,
    ) -> None:
        if battle_size not in (1, 2, 3):
            raise ValueError("battle_size must be 1, 2, or 3")
        if len(player_team) != battle_size:
            raise ValueError("player_team must contain battle_size heroes")
        if any(hero_id not in HERO_ROSTER for hero_id in player_team):
            raise ValueError("player_team contains an unsupported hero")
        if enemy_composition_mode not in ("random", "specified"):
            raise ValueError("enemy_composition_mode must be random or specified")
        if enemy_composition_mode == "specified":
            if enemy_team is None or len(enemy_team) != battle_size:
                raise ValueError("enemy_team must contain battle_size heroes")
            if any(hero_id not in HERO_ROSTER for hero_id in enemy_team):
                raise ValueError("enemy_team contains an unsupported hero")
        if enemy_control_mode not in ("computer", "player"):
            raise ValueError("enemy_control_mode must be computer or player")

    def _create_team(
        self,
        definition_ids: list[str],
        runtime_names: list[str],
        *,
        group: str,
        player_controlled: bool,
    ) -> list[Any]:
        return [
            HERO_ROSTER[definition_id]["class"](
                self.engine_data,
                runtime_name,
                group,
                player_controlled,
            )
            for definition_id, runtime_name in zip(definition_ids, runtime_names)
        ]

    def _runtime_names(self, definition_ids: list[str]) -> list[str]:
        """Choose session-scoped faculty names, unique until a pool is exhausted."""
        generator = HeroGenerator(self.engine_data)
        used_by_faculty: dict[str, set[str]] = {}
        names: list[str] = []
        for definition_id in definition_ids:
            hero_class = HERO_ROSTER[definition_id]["class"]
            pool = generator.hero_classes[hero_class]
            faculty = HERO_ROSTER[definition_id]["faculty"]
            used = used_by_faculty.setdefault(faculty, set())
            available = [name for name in pool if name not in used]
            name = random.choice(available if available else pool)
            used.add(name)
            names.append(name)
        return names

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
            "turnControl": self._turn_control(session, active, ended=ended),
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

    def _turn_control(self, session: BattleSession, actor, *, ended=False) -> dict[str, Any]:
        if ended or actor is None:
            return {
                "disposition": "ended",
                "acceptsCommands": False,
                "reasonId": None,
                "actorCombatantId": None,
                "sourceCombatantId": None,
                "forcedTargetIds": [],
            }
        directive = actor.turn_directive(
            actor.opponents, actor.allies, select_action=False
        )
        source_id = (
            self._combatant_id(session, directive.source)
            if directive.source is not None
            else None
        )
        return {
            "disposition": directive.disposition,
            "acceptsCommands": directive.accepts_commands,
            "reasonId": directive.reason_id,
            "actorCombatantId": self._combatant_id(session, actor),
            "sourceCombatantId": source_id,
            "forcedTargetIds": [source_id] if directive.reason_id == "scoff" and source_id else [],
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
                    automatic_events = self._drain_automatic_turns(session)
                    if automatic_events:
                        result["events"].extend(automatic_events)
                        result["revision"] = session.revision
                        result["snapshot"] = self.snapshot(session)
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
        directive = actor.turn_directive(
            actor.opponents, actor.allies, select_action=False
        )
        if directive.disposition != "playerCommand" or not directive.accepts_commands:
            raise BattleAdapterError(
                "notYourTurn", "The current turn does not accept player commands."
            )
        skill = self._skill_by_id(actor, command.get("skillId"))
        if skill is None or not skill.is_available or skill.if_cooldown:
            raise BattleAdapterError("illegalSkill", "The skill does not exist or is unavailable.")
        targets = command.get("targetIds")
        if not isinstance(targets, list):
            raise BattleAdapterError("invalidCommand", "targetIds must be an array.")
        published_action = next(
            (
                action
                for action in self._legal_actions(session, actor)
                if action["skillId"] == command.get("skillId")
            ),
            None,
        )
        if published_action is None:
            if targets:
                raise BattleAdapterError(
                    "illegalTargets", "One or more targets are illegal."
                )
            raise BattleAdapterError(
                "illegalSkill", "The skill is not a published legal action."
            )
        valid_ids = set(published_action["validTargetIds"])
        minimum = published_action["minimumTargets"]
        maximum = published_action["maximumTargets"]
        if len(targets) < minimum or len(targets) > maximum:
            raise BattleAdapterError(
                "illegalTargets", f"The skill requires {minimum} to {maximum} targets."
            )
        if len(set(targets)) != len(targets):
            raise BattleAdapterError("illegalTargets", "Duplicate targets are not allowed.")
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
                reasonId=command.get("_reasonId"),
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
        if skill.target_qty == 0:
            engine_targets: Any = ["none"]
        elif skill.target_type == "single":
            engine_targets = targets[0]
        else:
            engine_targets = targets
        action_result = skill.execute(engine_targets)
        if action_result:
            game.display_battle_info(action_result)
        presentation_events = self._drain_presentation_log(session)
        if presentation_events:
            self._hide_semantic_log_copy(events)
            events.extend(presentation_events)
        if command.get("_clearScoff"):
            actor.status["scoff"] = False
        for status in command.get("_clearStatuses", []):
            actor.status[status] = False
        after = self._capture(session)
        mutation_events = self._mutation_events(
            session, actor, skill, targets, before, after
        )
        if presentation_events:
            self._hide_semantic_log_copy(mutation_events)
        events.extend(mutation_events)
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
                round_log_events = self._drain_presentation_log(session)
                if round_log_events:
                    self._hide_semantic_log_copy(events)
                    events.extend(round_log_events)
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

    def _drain_presentation_log(
        self, session: BattleSession
    ) -> list[dict[str, Any]]:
        """Serialize new engine prose without treating it as state authority."""
        entries = session.game.presentation_log[session.presentation_log_cursor:]
        session.presentation_log_cursor = len(session.game.presentation_log)
        events: list[dict[str, Any]] = []
        for entry in entries:
            message = ANSI_ESCAPE.sub("", str(entry["message"])).strip()
            if not message:
                continue
            events.append(
                self._event(
                    session,
                    "battleLog",
                    channel=entry["channel"],
                    message=message,
                )
            )
        return events

    @staticmethod
    def _hide_semantic_log_copy(events: list[dict[str, Any]]) -> None:
        """Keep typed events active while suppressing duplicate generic prose."""
        visible_semantic_types = {
            "skillStarted",
            "characterMoved",
            "damageApplied",
            "attackEvaded",
            "healingApplied",
            "statusApplied",
            "statusRemoved",
            "characterDefeated",
        }
        for event in events:
            if event["type"] in visible_semantic_types:
                event["visibleInLog"] = False

    def _drain_automatic_turns(
        self, session: BattleSession, *, maximum_turns: int = 100
    ) -> list[dict[str, Any]]:
        """Resolve engine-owned skips and consecutive computer turns.

        The bound prevents a malformed legacy AI/engine state from monopolising
        an API worker. Incapacitated actors are advanced according to the same
        status semantics used by ``Hero.player_action`` and ``Hero.ai_action``
        before a snapshot can expose legal actions.
        """
        events: list[dict[str, Any]] = []
        turns = 0
        while not self._is_ended(session.game):
            actor = self._current_actor(session.game)
            if actor is None:
                break
            if turns >= maximum_turns:
                raise RuntimeError("automatic turn drain exceeded its safety bound")
            directive = actor.turn_directive(actor.opponents, actor.allies)
            if directive.disposition == "skip":
                if directive.consume_scoff:
                    actor.status["scoff"] = False
                    events.append(
                        self._event(
                            session,
                            "statusRemoved",
                            targetId=self._combatant_id(session, actor),
                            statusId="status.scoff",
                            reasonId=directive.reason_id,
                            effectHint="status",
                            message=f"{actor.name}'s Scoff ended without a legal forced attack.",
                        )
                    )
                events.extend(
                    self._consume_directive_statuses(session, actor, directive)
                )
                events.extend(self._skip_turn(session, actor, directive))
                turns += 1
                continue
            if directive.reason_id == "scoffSourceDefeated":
                if directive.consume_scoff:
                    actor.status["scoff"] = False
                session.revision += 1
                events.append(
                    self._event(
                        session,
                        "statusRemoved",
                        targetId=self._combatant_id(session, actor),
                        statusId="status.scoff",
                        effectHint="status",
                        message=f"{actor.name}'s Scoff ended because its source was defeated.",
                    )
                )
                continue
            if directive.reason_id == "scoff":
                if directive.skill is None:
                    raise RuntimeError(f"{actor.name} has no legal attack while scoffed")
                skill_id = self._skill_id(actor, directive.skill)
                chosen_targets = (
                    directive.targets
                    if isinstance(directive.targets, list)
                    else [directive.targets]
                )
                target_ids = [
                    self._combatant_id(session, target)
                    for target in chosen_targets
                    if target is not None
                ]
                valid_target_ids = self._valid_target_ids(
                    session, actor, directive.skill
                )
                required_targets = (
                    0
                    if directive.skill.target_qty == 0
                    else min(directive.skill.target_qty, len(valid_target_ids))
                )
                if (
                    len(target_ids) != required_targets
                    or len(set(target_ids)) != len(target_ids)
                    or any(
                        target_id not in valid_target_ids
                        for target_id in target_ids
                    )
                ):
                    raise RuntimeError(
                        f"{actor.name}'s engine-selected Scoff targets are not legal"
                    )
                result = self._resolve(
                    session,
                    {
                        "type": "useSkill",
                        "commandId": f"forced.scoff.{session.revision + 1:06d}",
                        "expectedRevision": session.revision,
                        "actorId": self._combatant_id(session, actor),
                        "skillId": skill_id,
                        "targetIds": target_ids,
                        "_clearScoff": directive.consume_scoff,
                    },
                )
                events.extend(result["events"])
                turns += 1
                continue
            if directive.reason_id in {"shadowWordInsanity", "magicCastingReady"}:
                if directive.skill is None:
                    raise RuntimeError(
                        f"{actor.name}'s automatic action has no executable skill"
                    )
                chosen_targets = (
                    directive.targets
                    if isinstance(directive.targets, list)
                    else [directive.targets]
                )
                target_ids = [
                    self._combatant_id(session, target)
                    for target in chosen_targets
                    if target not in (None, "none")
                ]
                result = self._resolve(
                    session,
                    {
                        "type": "useSkill",
                        "commandId": f"forced.{directive.reason_id}.{session.revision + 1:06d}",
                        "expectedRevision": session.revision,
                        "actorId": self._combatant_id(session, actor),
                        "skillId": self._skill_id(actor, directive.skill),
                        "targetIds": target_ids,
                        "_reasonId": directive.reason_id,
                        "_clearStatuses": list(directive.consume_statuses),
                    },
                )
                events.extend(result["events"])
                turns += 1
                continue
            if directive.reason_id == "vanish":
                hp_before = actor.hp
                message = actor.take_healing(int(actor.hp_max * 0.15))
                if actor.hp > hp_before:
                    events.append(
                        self._event(
                            session,
                            "healingApplied",
                            sourceId=self._combatant_id(session, actor),
                            targetId=self._combatant_id(session, actor),
                            amount=actor.hp - hp_before,
                            hpAfter={"current": actor.hp, "maximum": actor.hp_max},
                            reasonId=directive.reason_id,
                            effectHint="healing",
                            message=f"{actor.name} hid and drank a healing potion. {message}",
                        )
                    )
                events.extend(
                    self._consume_directive_statuses(session, actor, directive)
                )
                events.extend(self._skip_turn(session, actor, directive))
                turns += 1
                continue
            if directive.reason_id == "magicCasting":
                events.extend(
                    self._consume_directive_statuses(session, actor, directive)
                )
                events.extend(self._skip_turn(session, actor, directive))
                turns += 1
                continue
            if directive.disposition == "playerCommand":
                break
            actions = self._legal_actions(session, actor, include_computer=True)
            if not actions:
                raise RuntimeError(f"{actor.name} has no legal computer action")
            # Use the specialization's existing engine AI when it returns a
            # currently legal skill. Fall back only when legacy strategy code
            # selects a cooldown/unavailable action.
            chosen_skill = actor.ai_choose_skill(actor.opponents, actor.allies)
            chosen_skill_id = self._skill_id(actor, chosen_skill)
            action = next(
                (
                    candidate
                    for candidate in actions
                    if candidate["skillId"] == chosen_skill_id
                ),
                random.choice(actions),
            )
            chosen_skill = self._skill_by_id(actor, action["skillId"])
            assert chosen_skill is not None
            target_count = action["minimumTargets"]
            target_ids: list[str] = []
            if target_count:
                chosen_targets = actor.ai_choose_target(
                    chosen_skill, actor.opponents, actor.allies
                )
                if not isinstance(chosen_targets, list):
                    chosen_targets = [chosen_targets]
                for target in chosen_targets:
                    if target == "none":
                        continue
                    target_id = self._combatant_id(session, target)
                    if (
                        target_id in action["validTargetIds"]
                        and target_id not in target_ids
                    ):
                        target_ids.append(target_id)
                remaining = [
                    target_id
                    for target_id in action["validTargetIds"]
                    if target_id not in target_ids
                ]
                target_ids = target_ids[:target_count]
                if len(target_ids) < target_count:
                    target_ids.extend(
                        random.sample(remaining, target_count - len(target_ids))
                    )
            result = self._resolve(
                session,
                {
                    "type": "useSkill",
                    "commandId": f"ai.{session.revision + 1:06d}",
                    "expectedRevision": session.revision,
                    "actorId": action["actorId"],
                    "skillId": action["skillId"],
                    "targetIds": target_ids,
                },
            )
            events.extend(result["events"])
            turns += 1
        return events

    def _consume_directive_statuses(
        self, session: BattleSession, actor, directive
    ) -> list[dict[str, Any]]:
        """Apply consumed statuses when no skill-resolution delta captures them."""
        events: list[dict[str, Any]] = []
        for status in directive.consume_statuses:
            if not actor.status.get(status, False):
                continue
            actor.status[status] = False
            events.append(
                self._event(
                    session,
                    "statusRemoved",
                    targetId=self._combatant_id(session, actor),
                    statusId=f"status.{status}",
                    reasonId=directive.reason_id,
                    effectHint="status",
                    message=f"{actor.name}'s {status.replace('_', ' ')} status ended.",
                )
            )
        return events

    def _skip_turn(
        self, session: BattleSession, actor, directive
    ) -> list[dict[str, Any]]:
        """Advance one incapacitated actor without executing a skill."""
        game = session.game
        actor.actioned = True
        game.unactioned_sorted_heroes = [
            hero for hero in game.unactioned_sorted_heroes if hero is not actor
        ]
        game.update_allies_opponents_list()
        events = [
            self._event(
                session,
                "turnEnded",
                sourceId=self._combatant_id(session, actor),
                reasonId=directive.reason_id,
                message=f"{actor.name} {directive.message}; their turn ended.",
            )
        ]
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
        return events

    def _capture(self, session: BattleSession) -> dict[str, Any]:
        return {
            self._combatant_id(session, hero): {
                "hp": hero.hp,
                "maximum": hero.hp_max,
                "statuses": self._active_statuses(session, hero),
            }
            for hero in session.game.player_heroes + session.game.opponent_heroes
        }

    def _mutation_events(self, session, actor, skill, targets, before, after):
        events = []
        actor_id = self._combatant_id(session, actor)
        full_hp_healing_targets = (
            {
                self._combatant_id(session, target): target
                for target in targets
                if before[self._combatant_id(session, target)]["hp"]
                >= before[self._combatant_id(session, target)]["maximum"]
            }
            if skill.skill_type == "healing"
            else set()
        )
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
            elif skill.last_target_outcomes.get(id(target)) == "evaded":
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
            elif (
                combatant_id in full_hp_healing_targets
                and new["hp"] == old["hp"]
            ):
                events.append(
                    self._event(
                        session,
                        "healingApplied",
                        sourceId=actor_id,
                        targetId=combatant_id,
                        skillId=self._skill_id(actor, skill),
                        amount=0,
                        hpAfter={"current": new["hp"], "maximum": new["maximum"]},
                        effectHint="healing",
                        message=f"{full_hp_healing_targets[combatant_id].name} was already at full HP.",
                    )
                )
            changed_statuses = {
                status_id
                for status_id in new["statuses"].keys() & old["statuses"].keys()
                if (
                    any(
                        new["statuses"][status_id].get(field)
                        != old["statuses"][status_id].get(field)
                        for field in ("stacks", "sourceCombatantId", "kind")
                    )
                    or (
                        new["statuses"][status_id].get("roundsRemaining")
                        != old["statuses"][status_id].get("roundsRemaining")
                        and (
                            old["statuses"][status_id].get("roundsRemaining") is None
                            or new["statuses"][status_id].get("roundsRemaining") is None
                            or new["statuses"][status_id].get("roundsRemaining")
                            > old["statuses"][status_id].get("roundsRemaining")
                        )
                    )
                )
            }
            for status_id in sorted(
                (new["statuses"].keys() - old["statuses"].keys()) | changed_statuses
            ):
                status = new["statuses"][status_id]
                events.append(
                    self._event(
                        session,
                        "statusApplied",
                        sourceId=status.get("sourceCombatantId") or actor_id,
                        targetId=combatant_id,
                        skillId=self._skill_id(actor, skill),
                        statusId=status_id,
                        roundsRemaining=status["roundsRemaining"],
                        stacks=status.get("stacks"),
                        statusPresentation=self._status_presentation(status),
                        effectHint="status",
                        message=f"{status_id} was applied to {combatant_id}.",
                    )
                )
            for status_id in sorted(
                old["statuses"].keys() - new["statuses"].keys()
            ):
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
            changed_statuses = {
                status_id
                for status_id in new["statuses"].keys() & old["statuses"].keys()
                if (
                    any(
                        new["statuses"][status_id].get(field)
                        != old["statuses"][status_id].get(field)
                        for field in ("stacks", "sourceCombatantId", "kind")
                    )
                    or (
                        new["statuses"][status_id].get("roundsRemaining")
                        != old["statuses"][status_id].get("roundsRemaining")
                        and (
                            old["statuses"][status_id].get("roundsRemaining") is None
                            or new["statuses"][status_id].get("roundsRemaining") is None
                            or new["statuses"][status_id].get("roundsRemaining")
                            > old["statuses"][status_id].get("roundsRemaining")
                        )
                    )
                )
            }
            for status_id in sorted(
                (new["statuses"].keys() - old["statuses"].keys()) | changed_statuses
            ):
                status = new["statuses"][status_id]
                events.append(
                    self._event(
                        session,
                        "statusApplied",
                        targetId=combatant_id,
                        statusId=status_id,
                        roundsRemaining=status["roundsRemaining"],
                        stacks=status.get("stacks"),
                        statusPresentation=self._status_presentation(status),
                        effectHint="status",
                        message=f"{status_id} was applied to {combatant_id}.",
                    )
                )
            for status_id in sorted(
                old["statuses"].keys() - new["statuses"].keys()
            ):
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
            "statuses": list(self._active_statuses(session, hero).values()),
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

    def _active_statuses(self, session: BattleSession, hero) -> dict[str, dict[str, Any]]:
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
            source = record.initiator if record is not None else None
            result[status_id] = {
                "id": status_id,
                "instanceId": f"{status_id}.{_slug(hero.name)}",
                "kind": kind,
                "roundsRemaining": duration,
                "stacks": getattr(hero, f"{key}_stacks", None),
                "sourceCombatantId": (
                    self._combatant_id(session, source) if source is not None else None
                ),
            }
        return result

    def _legal_actions(
        self,
        session: BattleSession,
        actor,
        *,
        include_computer: bool = False,
        include_forced: bool = False,
    ) -> list[dict[str, Any]]:
        directive = actor.turn_directive(
            actor.opponents, actor.allies, select_action=False
        )
        if directive.disposition == "skip":
            return []
        if actor.status.get("scoff", False) and not include_forced:
            return []
        if not include_computer and not actor.is_player_controlled:
            return []
        actions = []
        for skill in actor.skills:
            if skill.if_cooldown or not skill.is_available:
                continue
            valid_targets = self._valid_target_ids(session, actor, skill)
            required_targets = (
                0 if skill.target_qty == 0 else min(skill.target_qty, len(valid_targets))
            )
            if skill.target_qty > 0 and required_targets == 0:
                continue
            actions.append(
                {
                    "skillId": self._skill_id(actor, skill),
                    "actorId": self._combatant_id(session, actor),
                    "minimumTargets": required_targets,
                    "maximumTargets": required_targets,
                    "validTargetIds": valid_targets,
                }
            )
        return actions

    def _valid_target_ids(self, session: BattleSession, actor, skill) -> list[str]:
        if skill.target_qty == 0:
            return []
        if skill.skill_type in {"healing", "buffs"}:
            pool = actor.allies
        elif skill.skill_type == "damage_healing":
            pool = actor.opponents + actor.allies
        else:
            pool = actor.opponents
        return [self._combatant_id(session, hero) for hero in pool if hero.hp > 0]

    def _skill_by_id(self, hero, skill_id):
        return next((s for s in hero.skills if self._skill_id(hero, s) == skill_id), None)

    def _skill_id(self, hero, skill) -> str:
        return f"skill.{_slug(hero.faculty)}.{_slug(skill.name)}"

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
        if skill.skill_type == "damage_healing":
            return "flexible"
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

    @staticmethod
    def _status_presentation(status: dict[str, Any]) -> StatusPresentation:
        """Map authoritative status metadata to its additive UI treatment."""
        return STATUS_PRESENTATION_BY_KIND.get(status.get("kind"), "neutral")

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

    def create(
        self,
        *,
        seed: int | None = None,
        battle_size: int = 1,
        player_team: list[str] | None = None,
        enemy_composition_mode: str = "specified",
        enemy_team: list[str] | None = None,
        enemy_control_mode: str = "player",
    ) -> tuple[BattleSession, dict[str, Any]]:
        session, envelope = self.adapter.create_battle(
            seed=seed,
            battle_size=battle_size,
            player_team=player_team,
            enemy_composition_mode=enemy_composition_mode,
            enemy_team=enemy_team,
            enemy_control_mode=enemy_control_mode,
        )
        with self._lock:
            self._sessions[session.battle_id] = session
        return session, envelope

    def get(self, battle_id: str) -> BattleSession | None:
        with self._lock:
            return self._sessions.get(battle_id)
