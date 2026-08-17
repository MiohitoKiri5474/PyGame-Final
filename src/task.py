from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from blocking import is_wall_blocked
from coords import tile_at
from pathfinding import find_path

if TYPE_CHECKING:
    from world import World
    from npc import NPC

Tile = tuple[int, int]


@dataclass
class Task:
    type: str
    target: Tile
    assigned_npc: "NPC | None" = None


@dataclass
class TaskType:
    work_seconds: float
    can_queue: Callable[["World", Tile], bool]
    # Returns True once the task has actually finished (removes it from the
    # queue and frees the NPC). Returning False keeps it queued and the NPC
    # assigned/waiting - e.g. ticket 04's insufficient-funds case - and it's
    # retried after another work_seconds instead of every single frame.
    on_complete: Callable[["World", Task], bool]


TASK_TYPES: dict[str, TaskType] = {}


def register_task_type(name: str, task_type: TaskType) -> None:
    TASK_TYPES[name] = task_type


class TaskQueue:
    def __init__(self):
        self.tasks: list[Task] = []

    def add(self, task_type: str, target: Tile) -> Task:
        task = Task(type=task_type, target=target)
        self.tasks.append(task)
        return task

    def claim_for(self, npc: "NPC") -> Task | None:
        order = npc.priority or list(TASK_TYPES.keys())
        for task_type in order:
            for task in self.tasks:
                if task.type == task_type and task.assigned_npc is None:
                    task.assigned_npc = npc
                    return task
        return None

    def remove(self, task: Task) -> None:
        # by identity, not list.remove()'s value equality: Task is a plain
        # dataclass, so two distinct unassigned tasks of the same type/target
        # compare equal and value-based removal could drop the wrong one.
        self.tasks = [t for t in self.tasks if t is not task]


def update_npc_tasks(world: "World", dt: float) -> None:
    """Single per-tick entry point: idle NPCs claim work, assigned NPCs walk
    to and perform it. This is the one place NPC/task state changes each
    tick — task-type modules extend behavior via TASK_TYPES, not by editing
    this function."""
    for npc in world.npcs:
        if npc.task is None:
            _try_claim_and_path(world, npc)
            continue

        npc.update(dt)
        if not npc.has_arrived:
            continue

        npc.task_progress += dt
        task_type = TASK_TYPES[npc.task.type]
        if npc.task_progress < task_type.work_seconds:
            continue

        finished = task_type.on_complete(world, npc.task)
        if finished:
            world.tasks.remove(npc.task)
            npc.task = None
        npc.task_progress = 0.0


def _try_claim_and_path(world: "World", npc: "NPC") -> None:
    task = world.tasks.claim_for(npc)
    if task is None:
        return

    # A task's own target is always a valid destination even if unclaimed
    # (e.g. Expand's whole point is walking onto not-yet-claimed frontier).
    # Walls block regardless (ticket 07) - an NPC can't walk onto one even
    # as its own task target, since build placement already forbids that.
    path = find_path(
        lambda x, y: (world.grid.get(x, y).claimed or (x, y) == task.target)
        and not is_wall_blocked(world.buildings, x, y),
        world.grid.width,
        world.grid.height,
        tile_at(npc.x, npc.y),
        task.target,
    )
    if path is None:
        task.assigned_npc = None
        return

    npc.task = task
    npc.set_path(path)
