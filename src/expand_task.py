from __future__ import annotations

from typing import TYPE_CHECKING

from blocking import is_mountain_blocked
from constants import EXPAND_WORK_SECONDS, EXPAND_CLAIM_RADIUS, EXPAND_REVEAL_RADIUS
from task import Task, TaskType, register_task_type

if TYPE_CHECKING:
    from world import World
    from task import Tile


def _can_queue(world: "World", tile: "Tile") -> bool:
    x, y = tile
    if not world.grid.in_bounds(x, y):
        return False
    if is_mountain_blocked(world.grid, x, y):
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


def _can_perform(world: "World", task: Task) -> bool:
    """A different, already-completed Expand can claim this target as part
    of its own radius before this one gets worked - claim radii overlap by
    design, so this isn't rare. Once that happens the tile's just claimed
    ground now; nothing left for this task to do."""
    x, y = task.target
    return world.grid.in_bounds(x, y) and not world.grid.get(x, y).claimed


def _on_complete(world: "World", task: Task) -> bool:
    x, y = task.target
    world.grid.expand(x, y, EXPAND_CLAIM_RADIUS, EXPAND_REVEAL_RADIUS)
    return True


register_task_type(
    "Expand",
    TaskType(work_seconds=EXPAND_WORK_SECONDS, can_queue=_can_queue, on_complete=_on_complete, can_perform=_can_perform),
)
