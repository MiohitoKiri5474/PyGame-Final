"""Hunt task type (ticket 25): queue hunt on wild animal, path to it,
re-path if the animal moves, resolve combat with Knight crit bonus,
and remove hunted animal on death."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from constants import (
    HUNT_SCATTER_LEAD_SECONDS,
    HUNT_WORK_SECONDS,
    KNIGHT_CRIT_MULTIPLIER,
    ROLE_KNIGHT,
)
from coords import tile_at, tile_center
from day_night import DAY
from skills import hunting_crit_chance
from task import register_task_type, resolve_task_animal, TaskType

if TYPE_CHECKING:
    from day_night import DayNightCycle
    from task import Task
    from world import World


def can_queue_hunt(world: "World", tile: tuple[int, int]) -> bool:
    """Hunt task can only be queued on a tile with a living wild animal."""
    if not hasattr(world, "animals"):
        return False
    return any(tile_at(a.x, a.y) == tile and not a.is_dead for a in world.animals)


def can_perform_hunt(world: "World", task: "Task") -> bool:
    """Hunt task can be performed if the target animal exists and is alive."""
    return resolve_task_animal(world, task) is not None


def on_complete_hunt(world: "World", task: "Task", rng: random.Random | None = None) -> bool:
    """Resolve attack against the hunted animal.
    If animal dies, removes it and completes the task.
    Returns True when task is finished, False if target moved or still alive."""
    rng = rng or random.Random()
    animal = resolve_task_animal(world, task)

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


def _flee_point(animal, grid) -> tuple[float, float]:
    """A point further out from the map center, along the direction the
    animal already sits relative to it - "fleeing outward" away from the
    player's territory, which always starts at the map center."""
    cx, cy = grid.width / 2.0, grid.height / 2.0
    ax, ay = tile_at(animal.x, animal.y)
    dx, dy = ax - cx, ay - cy
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    flee_tiles = 10
    tx = max(0, min(grid.width - 1, round(ax + ux * flee_tiles)))
    ty = max(0, min(grid.height - 1, round(ay + uy * flee_tiles)))
    return tile_center(tx, ty)


def scatter_unclaimed_hunt_targets(world: "World", cycle: "DayNightCycle") -> None:
    """In the last HUNT_SCATTER_LEAD_SECONDS of the day, cancel any Hunt
    task no NPC has claimed yet and send its target animal fleeing outward
    - otherwise the player would see a queued-Hunt marker sitting right
    alongside real night monsters, which reads as confusing (which threat
    is which?). Claimed/in-progress Hunts are left alone; an NPC already
    working one keeps going into the night."""
    if cycle.phase != DAY or cycle.remaining() > HUNT_SCATTER_LEAD_SECONDS:
        return
    stale = [t for t in world.tasks.tasks if t.type == "Hunt" and t.assigned_npc is None]
    for task in stale:
        animal = resolve_task_animal(world, task)
        world.tasks.remove(task)
        if animal is not None:
            animal.idle_target = _flee_point(animal, world.grid)
