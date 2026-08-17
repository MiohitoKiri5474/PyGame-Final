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
    if any(task.type == "Expand" and task.target == tile for task in world.tasks.tasks):
        return False
    # Must be reachable from claimed territory (4-adjacent to a claimed
    # tile) - otherwise find_path can never reach it and the task would
    # permanently deadlock the queue (claim_for keeps retrying the
    # unreachable head-of-queue task, starving everything behind it).
    return any(
        world.grid.in_bounds(nx, ny) and world.grid.get(nx, ny).claimed
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
    )


def _on_complete(world: "World", task: Task) -> bool:
    x, y = task.target
    world.grid.expand(x, y, EXPAND_CLAIM_RADIUS, EXPAND_REVEAL_RADIUS)
    return True


register_task_type(
    "Expand",
    TaskType(work_seconds=EXPAND_WORK_SECONDS, can_queue=_can_queue, on_complete=_on_complete),
)
