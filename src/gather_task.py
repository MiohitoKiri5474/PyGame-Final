from __future__ import annotations

from typing import TYPE_CHECKING

from audio import play_sfx
from constants import GATHER_WORK_SECONDS, GATHER_YIELD
from task import Task, TaskType, register_task_type

if TYPE_CHECKING:
    from world import World
    from task import Tile


def _can_queue(world: "World", tile: "Tile") -> bool:
    x, y = tile
    t = world.grid.get(x, y)
    if not t.claimed or t.resource is None:
        return False
    return not any(task.type == "Gather" and task.target == tile for task in world.tasks.tasks)


def _can_perform(world: "World", task: Task) -> bool:
    x, y = task.target
    return world.grid.in_bounds(x, y) and world.grid.get(x, y).resource is not None


def _on_complete(world: "World", task: Task) -> bool:
    x, y = task.target
    tile = world.grid.get(x, y)
    if tile.resource is not None:
        if tile.resource == "wood":
            play_sfx("chop")
        else:
            play_sfx("gather")
        world.inventory.add(tile.resource, GATHER_YIELD)
        tile.resource = None
    return True  # nothing left to wait for either way (already-gone is a no-op, not a retry)



register_task_type(
    "Gather",
    TaskType(
        work_seconds=GATHER_WORK_SECONDS,
        can_queue=_can_queue,
        on_complete=_on_complete,
        can_perform=_can_perform,
    ),
)
