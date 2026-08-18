"""Which task types apply to a clicked tile (pygame-free, unit tested).

Most tiles admit exactly one sensible task - a resource tile can only be
Gathered, a frontier tile can only be Expanded, a building can only be
Destroyed - so making the player pre-select a task type before clicking was
redundant. This module infers the options from what's actually on the tile;
game.py queues directly when there's one, and asks when there's more.

Build tasks are deliberately excluded: "what to build" genuinely isn't
inferable from an empty tile, so those stay player-chosen (via the build
bar) and are placed rather than inferred.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from task import TASK_TYPES

if TYPE_CHECKING:
    from task import Tile
    from world import World

BUILD_PREFIX = "Build"


def is_build_task(task_type: str) -> bool:
    return task_type.startswith(BUILD_PREFIX)


def build_task_types() -> list[str]:
    """Registered Build* task types, in registration order."""
    return [name for name in TASK_TYPES if is_build_task(name)]


def building_label(task_type: str) -> str:
    """'BuildAnimalPen' -> 'AnimalPen'; non-build types pass through."""
    return task_type[len(BUILD_PREFIX):] if is_build_task(task_type) else task_type


def applicable_tasks(world: "World", tile: "Tile") -> list[str]:
    """Non-build task types that can currently be queued on `tile`, in
    task-registration order. Empty when the tile affords no work."""
    # Guard first: several can_queue callbacks index the grid directly and
    # would raise on an out-of-bounds tile rather than returning False.
    if not world.grid.in_bounds(*tile):
        return []
    return [
        name
        for name, task_type in TASK_TYPES.items()
        if not is_build_task(name) and task_type.can_queue(world, tile)
    ]
