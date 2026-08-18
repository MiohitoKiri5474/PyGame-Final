"""Skill upgrade tree (ticket 23): a single global skill-level pool spent
from the shared points ticket 22 awards at night-clear settlement, not
tracked per-NPC (game-detail.md awards points per-round, not per-character).

Skill levels live on World (world.skills), same placement as Spellbook,
so every consumer (task.py, magic.py, hunt_task.py, tame_task.py) can reach
them through the world parameter they already receive."""

from __future__ import annotations

from typing import TYPE_CHECKING

from constants import (
    AOE_RADIUS_BONUS_PER_LEVEL,
    DEFENSE_BONUS_PER_LEVEL,
    FREEZE_RADIUS,
    GATHER_SPEED_REDUCTION_PER_LEVEL,
    HEALTH_BONUS_PER_LEVEL,
    HUNTING_ACCURACY_CRIT_BONUS_PER_LEVEL,
    KNIGHT_CRIT_CHANCE,
    MAGIC_DAMAGE_MULTIPLIER_PER_LEVEL,
    SKILL_AOE_ATTACK,
    SKILL_DEFENSE_ABILITY,
    SKILL_GATHER_SPEED,
    SKILL_HUNTING_ACCURACY,
    SKILL_MAGIC_ATTACK,
    SKILL_NAMES,
    SKILL_TAMING_ABILITY,
    TAMING_SUCCESS_BONUS_PER_LEVEL,
)

if TYPE_CHECKING:
    from world import World


def new_skill_levels() -> dict[str, int]:
    return {name: 0 for name in SKILL_NAMES}


def spend_point(world: "World", points_available: int, skill: str) -> tuple[int, bool]:
    """Spend one available point on `skill`. Returns (remaining_points, success).
    No-op (success=False, points unchanged) if no points are available or the
    skill name isn't recognized."""
    if points_available <= 0 or skill not in world.skills:
        return points_available, False

    world.skills[skill] += 1
    if skill == SKILL_DEFENSE_ABILITY:
        _apply_defense_bonus_to_all_living(world)
    return points_available - 1, True


def _apply_defense_bonus_to_all_living(world: "World") -> None:
    """Defense Ability's bonus is a flat stat add, not a dynamically-derived
    value read each combat tick (matching how role-based stats already work:
    set once, mutated directly, never recomputed from world state). So each
    point spent immediately buffs every currently-alive NPC once, rather than
    combat.py needing to look up the global level every tick."""
    for npc in world.npcs:
        if npc.is_dead:
            continue
        npc.defense += DEFENSE_BONUS_PER_LEVEL
        npc.max_health += HEALTH_BONUS_PER_LEVEL
        npc.health += HEALTH_BONUS_PER_LEVEL


def gather_speed_multiplier(world: "World") -> float:
    """Multiplies Gather's work-seconds requirement. Stacks multiplicatively
    with Farmer's role work_multiplier (task.py applies both), not in place
    of it - a Farmer with levels in this skill gathers faster than a Farmer
    without, and both gather faster than a non-Farmer at the same level."""
    level = world.skills[SKILL_GATHER_SPEED]
    return max(0.1, 1.0 - GATHER_SPEED_REDUCTION_PER_LEVEL * level)


def magic_damage_multiplier(world: "World") -> float:
    level = world.skills[SKILL_MAGIC_ATTACK]
    return 1.0 + MAGIC_DAMAGE_MULTIPLIER_PER_LEVEL * level


def aoe_radius(world: "World") -> int:
    level = world.skills[SKILL_AOE_ATTACK]
    return FREEZE_RADIUS + AOE_RADIUS_BONUS_PER_LEVEL * level


def hunting_crit_chance(world: "World") -> float:
    level = world.skills[SKILL_HUNTING_ACCURACY]
    return min(1.0, KNIGHT_CRIT_CHANCE + HUNTING_ACCURACY_CRIT_BONUS_PER_LEVEL * level)


def taming_success_bonus(world: "World") -> float:
    level = world.skills[SKILL_TAMING_ABILITY]
    return TAMING_SUCCESS_BONUS_PER_LEVEL * level


def defense_bonus_defense(world: "World") -> int:
    """Total Defense Ability defense bonus already applied across all spent
    points - read-only helper for display/tests, not itself applied anywhere
    (the actual application happens once per spend in spend_point)."""
    return DEFENSE_BONUS_PER_LEVEL * world.skills[SKILL_DEFENSE_ABILITY]


def defense_bonus_health(world: "World") -> int:
    return HEALTH_BONUS_PER_LEVEL * world.skills[SKILL_DEFENSE_ABILITY]
