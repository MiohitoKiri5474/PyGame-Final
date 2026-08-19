"""Hunt task type (ticket 25): queue hunt on wild animal, path to it,
re-path if the animal moves, resolve combat with Knight crit bonus,
and remove hunted animal on death."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from constants import (
    HUNT_WORK_SECONDS,
    KNIGHT_CRIT_MULTIPLIER,
    ROLE_KNIGHT,
)
from coords import tile_at
from skills import hunting_crit_chance
from task import register_task_type, TaskType

if TYPE_CHECKING:
    from task import Task
    from world import World


def can_queue_hunt(world: "World", tile: tuple[int, int]) -> bool:
    """Hunt task can only be queued on a tile with a living wild animal."""
    if not hasattr(world, "animals"):
        return False
    return any(tile_at(a.x, a.y) == tile and not a.is_dead for a in world.animals)


def can_perform_hunt(world: "World", task: "Task") -> bool:
    """Hunt task can be performed if the target animal exists and is alive."""
    if not hasattr(world, "animals"):
        return False
    if task.target_animal_id is not None:
        return any(a.id == task.target_animal_id and not a.is_dead for a in world.animals)
    return any(tile_at(a.x, a.y) == task.target and not a.is_dead for a in world.animals)


def on_complete_hunt(world: "World", task: "Task", rng: random.Random | None = None) -> bool:
    """Resolve attack against the hunted animal.
    If animal dies, removes it and completes the task.
    Returns True when task is finished, False if target moved or still alive."""
    if not hasattr(world, "animals"):
        return True

    rng = rng or random.Random()
    animal = None
    if task.target_animal_id is not None:
        animal = next((a for a in world.animals if a.id == task.target_animal_id), None)
    if animal is None:
        animal = next((a for a in world.animals if tile_at(a.x, a.y) == task.target and not a.is_dead), None)

    if animal is None or animal.is_dead:
        return True

    npc = task.assigned_npc
    base_attack = getattr(npc, "attack", 12) if npc else 12
    npc_role = getattr(npc, "role", None) if npc else None

    damage = float(base_attack)
    if npc_role == ROLE_KNIGHT and rng.random() < hunting_crit_chance(world):
        damage *= KNIGHT_CRIT_MULTIPLIER

    if npc and hasattr(npc, "trigger_attack"):
        npc.trigger_attack(animal.x, animal.y)

    animal.take_damage(damage)


    # If dangerous animal is hostile and still alive, retaliate against NPC
    if animal.dangerous and animal.is_hostile and npc and not animal.is_dead:
        animal.retaliate(npc)


    if animal.is_dead:
        world.animals[:] = [a for a in world.animals if not a.is_dead]
        return True

    # Animal is still alive; task keeps going
    return False


register_task_type(
    "Hunt",
    TaskType(
        work_seconds=HUNT_WORK_SECONDS,
        can_queue=can_queue_hunt,
        on_complete=on_complete_hunt,
        can_perform=can_perform_hunt,
    ),
)
