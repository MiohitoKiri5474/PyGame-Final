from __future__ import annotations

from typing import TYPE_CHECKING

from constants import DESTROY_WORK_SECONDS
from task import Task, TaskType, register_task_type

if TYPE_CHECKING:
    from world import World
    from task import Tile


def _can_queue(world: "World", tile: "Tile") -> bool:
    x, y = tile
    if not world.grid.in_bounds(x, y):
        return False
    # Must have a building on this tile
    if not any(b.x == x and b.y == y for b in world.buildings):
        return False
    # Must not already have a Destroy task queued on this tile
    return not any(task.type == "Destroy" and task.target == tile for task in world.tasks.tasks)


def _can_perform(world: "World", task: Task) -> bool:
    x, y = task.target
    return any(b.x == x and b.y == y for b in world.buildings)


def _on_complete(world: "World", task: Task) -> bool:
    x, y = task.target
    world.buildings[:] = [b for b in world.buildings if not (b.x == x and b.y == y)]
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
