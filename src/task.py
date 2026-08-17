from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from blocking import is_wall_blocked
from constants import HUNGER_EAT_THRESHOLD
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
    # queue and frees the NPC). Returning False keeps it queued (unassigns the
    # NPC so it can skip to other work rather than getting permanently stuck).
    on_complete: Callable[["World", Task], bool]
    can_perform: Callable[["World", Task], bool] | None = None


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

    def claim_for(self, npc: "NPC", world: "World | None" = None) -> Task | None:
        order = npc.priority or list(TASK_TYPES.keys())
        for task_type_name in order:
            task_type = TASK_TYPES.get(task_type_name)
            for task in self.tasks:
                if task.type == task_type_name and task.assigned_npc is None:
                    if world is not None and task_type and task_type.can_perform is not None:
                        if not task_type.can_perform(world, task):
                            continue
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
    to and perform it. If a task is blocked (e.g. missing materials), NPCs skip
    it and work on available tasks. Hungry NPCs consume food from the colony inventory."""
    for npc in world.npcs:
        # Colony food consumption: hungry NPCs eat from inventory
        if npc.hunger <= HUNGER_EAT_THRESHOLD and not npc.is_dead:
            if world.inventory.spend("crop", 1):
                npc.eat()

        if npc.task is None:
            _try_claim_and_path(world, npc)
            if npc.task is None:
                npc.update(dt)
                continue

        task_type = TASK_TYPES.get(npc.task.type)
        if task_type is not None and task_type.can_perform is not None:
            if not task_type.can_perform(world, npc.task):
                # Task became blocked in-progress; skip and try other work
                npc.task.assigned_npc = None
                npc.task = None
                npc.task_progress = 0.0
                npc.set_path([])
                _try_claim_and_path(world, npc)
                if npc.task is None:
                    npc.update(dt)
                continue

        npc.update(dt)
        if not npc.has_arrived:
            continue

        npc.task_progress += dt
        if task_type is None:
            continue
        if npc.task_progress < task_type.work_seconds * npc.work_multiplier:
            continue

        finished = task_type.on_complete(world, npc.task)
        if finished:
            world.tasks.remove(npc.task)
        else:
            # Task could not be completed (e.g. missing materials); unassign NPC so
            # it skips to other available tasks instead of staying stuck
            npc.task.assigned_npc = None
        npc.task = None
        npc.task_progress = 0.0


def _try_claim_and_path(world: "World", npc: "NPC") -> None:
    order = npc.priority or list(TASK_TYPES.keys())
    for task_type_name in order:
        task_type = TASK_TYPES.get(task_type_name)
        if task_type is None:
            continue
        for task in world.tasks.tasks:
            if task.type != task_type_name or task.assigned_npc is not None:
                continue
            if task_type.can_perform is not None and not task_type.can_perform(world, task):
                continue

            path = find_path(
                lambda x, y: (world.grid.get(x, y).claimed or (x, y) == task.target)
                and (not is_wall_blocked(world.buildings, x, y) or (x, y) == task.target),
                world.grid.width,
                world.grid.height,
                tile_at(npc.x, npc.y),
                task.target,
            )
            if path is None:
                continue

            task.assigned_npc = npc
            npc.task = task
            npc.set_path(path)
            return
