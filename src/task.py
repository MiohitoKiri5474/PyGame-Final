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
    target_animal_id: int | None = None


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

    def add(self, task_type: str, target: Tile, target_animal_id: int | None = None) -> Task:
        task = Task(type=task_type, target=target, target_animal_id=target_animal_id)
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

        # Moving-target re-path check (ticket 25): for Hunt tasks, if target animal moved
        if npc.task.type == "Hunt" and hasattr(world, "animals"):
            animal = None
            if npc.task.target_animal_id is not None:
                animal = next((a for a in world.animals if a.id == npc.task.target_animal_id), None)
            if animal is None:
                animal = next((a for a in world.animals if tile_at(a.x, a.y) == npc.task.target and not a.is_dead), None)

            if animal is not None and not animal.is_dead:
                animal_tile = tile_at(animal.x, animal.y)
                npc_tile = tile_at(npc.x, npc.y)
                if animal_tile != npc_tile:
                    # Animal moved! Recompute path to animal's current tile
                    path = find_path(
                        lambda x, y: world.grid.in_bounds(x, y) and not is_wall_blocked(world.buildings, x, y),
                        world.grid.width,
                        world.grid.height,
                        npc_tile,
                        animal_tile,
                    )
                    if path:
                        npc.task.target = animal_tile
                        npc.set_path(path)
                        npc.task_progress = 0.0
                        continue

        npc.task_progress += dt
        if task_type is None or npc.task_progress < task_type.work_seconds:
            continue

        finished = task_type.on_complete(world, npc.task)
        if finished:
            world.tasks.remove(npc.task)
        else:
            # Task could not be completed (e.g. missing materials or animal still alive);
            # unassign NPC or reset progress so it re-evaluates
            npc.task_progress = 0.0
            if npc.task.type != "Hunt":
                npc.task.assigned_npc = None
                npc.task = None
            continue

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

            # Hunt task targets may be outside claimed territory, so allow pathing across unblocked tiles
            is_hunt = (task.type == "Hunt")
            path = find_path(
                lambda x, y: (is_hunt or world.grid.get(x, y).claimed or (x, y) == task.target)
                and (not is_wall_blocked(world.buildings, x, y) or (x, y) == task.target),
                world.grid.width,
                world.grid.height,
                tile_at(npc.x, npc.y),
                task.target,
            )
            if path is None:
                continue

            if is_hunt and task.target_animal_id is None and hasattr(world, "animals"):
                animal = next((a for a in world.animals if tile_at(a.x, a.y) == task.target and not a.is_dead), None)
                if animal is not None:
                    task.target_animal_id = animal.id

            task.assigned_npc = npc
            npc.task = task
            npc.set_path(path)
            return

