from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from constants import (
    WALL_WORK_SECONDS,
    WALL_COST,
    WALL_BLOCK,
    WALL_ATTACK,
    TOWER_WORK_SECONDS,
    TOWER_COST,
    TOWER_BLOCK,
    TOWER_ATTACK,
)
from task import Task, TaskType, register_task_type
from extensions import register_hud_line

if TYPE_CHECKING:
    from world import World
    from task import Tile


@dataclass
class Building:
    type: str
    x: int
    y: int
    block: int
    attack: int


def _can_queue(world: "World", tile: "Tile") -> bool:
    x, y = tile
    t = world.grid.get(x, y)
    if not t.claimed or t.resource is not None:
        return False
    if any(b.x == x and b.y == y for b in world.buildings):
        return False
    if any(task.type.startswith("Build") and task.target == tile for task in world.tasks.tasks):
        return False
    return True


def _on_complete_wall(world: "World", task: Task) -> bool:
    return _try_build(world, task, "Wall", WALL_COST, WALL_BLOCK, WALL_ATTACK)


def _on_complete_tower(world: "World", task: Task) -> bool:
    return _try_build(world, task, "Tower", TOWER_COST, TOWER_BLOCK, TOWER_ATTACK)


def _try_build(world: "World", task: Task, b_type: str, cost: dict[str, int], block: int, attack: int) -> bool:
    if not world.inventory.spend_all(cost):
        return False

    x, y = task.target
    world.buildings.append(Building(type=b_type, x=x, y=y, block=block, attack=attack))
    return True


_COSTS_BY_TASK_TYPE = {"BuildWall": WALL_COST, "BuildTower": TOWER_COST}


def _blocked_builds_hud_line(world: "World") -> str:
    # Insufficient-funds tasks stay queued (on_complete returns False) and
    # retry silently every work cycle - report them so that's visible
    # rather than the NPC just looking stuck for no apparent reason.
    blocked = sorted(
        {
            task.type
            for task in world.tasks.tasks
            if task.type in _COSTS_BY_TASK_TYPE
            and any(world.inventory.get(res) < amt for res, amt in _COSTS_BY_TASK_TYPE[task.type].items())
        }
    )
    if not blocked:
        return ""
    return f"Build blocked (insufficient resources): {', '.join(blocked)}"


register_task_type(
    "BuildWall",
    TaskType(work_seconds=WALL_WORK_SECONDS, can_queue=_can_queue, on_complete=_on_complete_wall),
)

register_task_type(
    "BuildTower",
    TaskType(work_seconds=TOWER_WORK_SECONDS, can_queue=_can_queue, on_complete=_on_complete_tower),
)

register_hud_line(_blocked_builds_hud_line)
