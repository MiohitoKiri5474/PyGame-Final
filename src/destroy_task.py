from __future__ import annotations

from typing import TYPE_CHECKING

from build_task import building_occupies_tile
from constants import DESTROY_WORK_SECONDS
from task import Task, TaskType, register_task_type

if TYPE_CHECKING:
    from world import World
    from task import Tile


def _find_building(world: "World", tile: "Tile"):
    x, y = tile
    return next((b for b in world.buildings if building_occupies_tile(b, x, y)), None)


def _can_queue(world: "World", tile: "Tile") -> bool:
    x, y = tile
    if not world.grid.in_bounds(x, y):
        return False
    # Must have a building occupying this tile
    b = _find_building(world, tile)
    if b is None:
        return False
    # Must not already have a Destroy task queued on any tile of this building
    return not any(
        task.type == "Destroy" and building_occupies_tile(b, task.target[0], task.target[1])
        for task in world.tasks.tasks
    )


def _can_perform(world: "World", task: Task) -> bool:
    return _find_building(world, task.target) is not None


def _on_complete(world: "World", task: Task) -> bool:
    b = _find_building(world, task.target)
    if b is not None and b in world.buildings:
        world.buildings.remove(b)
    return True


register_task_type(
    "Destroy",
    TaskType(
        work_seconds=DESTROY_WORK_SECONDS,
        can_queue=_can_queue,
        on_complete=_on_complete,
        can_perform=_can_perform,
    ),
)
