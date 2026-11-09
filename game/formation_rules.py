"""Pure, authoritative formation rules shared by combat and read-only clients.

This module deliberately has no hero, battle-session, persistence, or random
dependencies.  Live combat and static rule catalogues consume the same small
functions so presentation clients never need to copy these mechanics.
"""

from __future__ import annotations

from typing import Literal, Sequence


Position = Literal["front", "rear"]
DirectDamageAttackType = Literal[
    "melee", "ranged_projectile", "ranged_instant"
]
FormationId = Literal[
    "front-rear",
    "side-by-side",
    "one-front-two-rear",
    "two-front-one-rear",
    "all-front",
]

FORMATION_POSITIONS: dict[FormationId, tuple[Position, ...]] = {
    "front-rear": ("front", "rear"),
    "side-by-side": ("front", "front"),
    "one-front-two-rear": ("front", "rear", "rear"),
    "two-front-one-rear": ("front", "front", "rear"),
    "all-front": ("front", "front", "front"),
}

DIRECT_DAMAGE_ATTACK_TYPES: tuple[DirectDamageAttackType, ...] = (
    "melee",
    "ranged_projectile",
    "ranged_instant",
)

_API_ATTACK_TYPES = {
    "melee": "melee",
    "ranged_projectile": "rangedProjectile",
    "ranged_instant": "rangedInstant",
}


def direct_damage_target_is_eligible(
    attack_type: str,
    target_position: Position,
    living_enemy_positions: Sequence[Position],
) -> bool:
    """Return formation-only target eligibility for classified direct damage."""

    return not (
        attack_type == "melee"
        and "front" in living_enemy_positions
        and target_position != "front"
    )


def direct_damage_formation_multiplier(
    attacker_position: Position,
    defender_position: Position,
    attack_type: str,
) -> float:
    """Return the one live-combat direct-hit formation multiplier."""

    if attack_type == "melee" and attacker_position == "rear":
        return 0.7
    if attack_type == "ranged_projectile":
        if attacker_position == "rear" and defender_position == "rear":
            return 0.6
        if attacker_position != defender_position:
            return 0.8
    return 1.0


def _target_fact(
    *,
    target_slot: int,
    target_position: Position,
    defeated: bool,
    attacker_position: Position,
    attack_type: DirectDamageAttackType,
    living_enemy_positions: Sequence[Position],
) -> dict[str, object]:
    if defeated:
        return {
            "targetSlot": target_slot,
            "targetPosition": target_position,
            "eligible": False,
            "multiplierPercent": None,
            "reason": "defeated",
        }
    eligible = direct_damage_target_is_eligible(
        attack_type, target_position, living_enemy_positions
    )
    return {
        "targetSlot": target_slot,
        "targetPosition": target_position,
        "eligible": eligible,
        "multiplierPercent": (
            round(
                100
                * direct_damage_formation_multiplier(
                    attacker_position, target_position, attack_type
                )
            )
            if eligible
            else None
        ),
        "reason": "eligible" if eligible else "protectedByFrontLine",
    }


def _explanation(
    attacker_position: Position,
    attack_type: DirectDamageAttackType,
    targets: Sequence[dict[str, object]],
) -> str:
    label = {
        "melee": "melee",
        "ranged_projectile": "ranged projectile",
        "ranged_instant": "ranged instant",
    }[attack_type]
    eligible = [target for target in targets if target["eligible"]]
    summaries: list[str] = []
    for position in ("front", "rear"):
        matching = [
            target
            for target in eligible
            if target["targetPosition"] == position
        ]
        if matching:
            summaries.append(
                f"enemy {position} heroes at "
                f"{matching[0]['multiplierPercent']}% direct damage"
            )
    if summaries:
        reach = " and ".join(summaries)
        sentence = (
            f"Your {attacker_position} hero can attack {reach} with {label}."
        )
    else:
        sentence = f"Your {attacker_position} hero has no living target for {label}."
    if any(target["reason"] == "protectedByFrontLine" for target in targets):
        sentence += " Enemy rear heroes remain protected while a front defender is alive."
    return sentence


def formation_demonstration_catalogue() -> dict[str, object]:
    """Build the exhaustive, deterministic Manual rule catalogue."""

    formations: list[dict[str, object]] = []
    for formation_id, positions in FORMATION_POSITIONS.items():
        has_rear_enemies = "rear" in positions
        slots = [
            {"slot": index, "position": position}
            for index, position in enumerate(positions, start=1)
        ]
        evaluations: list[dict[str, object]] = []
        front_states = (False, True) if has_rear_enemies else (False,)
        for attacker_slot, attacker_position in enumerate(positions, start=1):
            for attack_type in DIRECT_DAMAGE_ATTACK_TYPES:
                for enemy_front_defeated in front_states:
                    defeated = [
                        enemy_front_defeated and position == "front"
                        for position in positions
                    ]
                    living_positions = [
                        position
                        for position, is_defeated in zip(positions, defeated)
                        if not is_defeated
                    ]
                    targets = [
                        _target_fact(
                            target_slot=target_slot,
                            target_position=target_position,
                            defeated=is_defeated,
                            attacker_position=attacker_position,
                            attack_type=attack_type,
                            living_enemy_positions=living_positions,
                        )
                        for target_slot, (target_position, is_defeated) in enumerate(
                            zip(positions, defeated), start=1
                        )
                    ]
                    evaluations.append(
                        {
                            "attackerSlot": attacker_slot,
                            "attackerPosition": attacker_position,
                            "attackType": _API_ATTACK_TYPES[attack_type],
                            "enemyFrontDefeated": enemy_front_defeated,
                            "targets": targets,
                            "explanation": _explanation(
                                attacker_position, attack_type, targets
                            ),
                        }
                    )
        formations.append(
            {
                "id": formation_id,
                "battleSize": len(positions),
                "hasRearEnemies": has_rear_enemies,
                "friendlySlots": slots,
                "enemySlots": slots,
                "evaluations": evaluations,
            }
        )
    return {
        "contractVersion": "1.0",
        "attackTypes": list(_API_ATTACK_TYPES.values()),
        "formations": formations,
    }
