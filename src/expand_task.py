from __future__ import annotations

from typing import TYPE_CHECKING

from constants import EXPAND_WORK_SECONDS, EXPAND_CLAIM_RADIUS, EXPAND_REVEAL_RADIUS
from task import Task, TaskType, register_task_type

if TYPE_CHECKING:
    from world import World
    from task import Tile


def _can_queue(world: "World", tile: "Tile") -> bool:
    x, y = tile
    if not world.grid.in_bounds(x, y):
        return False
    t = world.grid.get(x, y)
    if t.claimed:
        return False
    return not any(task.type == "Expand" and task.target == tile for task in world.tasks.tasks)


def _on_complete(world: "World", task: Task) -> bool:
    x, y = task.target
    world.grid.expand(x, y, EXPAND_CLAIM_RADIUS, EXPAND_REVEAL_RADIUS)
    return True


register_task_type(
    "Expand",
    TaskType(work_seconds=EXPAND_WORK_SECONDS, can_queue=_can_queue, on_complete=_on_complete),
)
