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
import render_buildings  # noqa: F401  # registers the buildings overlay renderer

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
    for res, amount in cost.items():
        if world.inventory.get(res) < amount:
            return False

    for res, amount in cost.items():
        world.inventory.spend(res, amount)

    x, y = task.target
    world.buildings.append(Building(type=b_type, x=x, y=y, block=block, attack=attack))
    return True


register_task_type(
    "BuildWall",
    TaskType(work_seconds=WALL_WORK_SECONDS, can_queue=_can_queue, on_complete=_on_complete_wall),
)

register_task_type(
    "BuildTower",
    TaskType(work_seconds=TOWER_WORK_SECONDS, can_queue=_can_queue, on_complete=_on_complete_tower),
)
