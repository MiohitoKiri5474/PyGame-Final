from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from audio import play_sfx
from blocking import is_wall_blocked
from constants import HUNGER_EAT_THRESHOLD
from coords import tile_at, tile_center
from pathfinding import find_path

from skills import gather_speed_multiplier


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

# Task types whose target is a live wild animal rather than a fixed tile -
# both need the proximity-chase handling in update_npc_tasks below, since a
# wandering animal hops to a new tile every second or two and a "must land
# on its exact tile" rule would make it nearly unhuntable/untameable.
ANIMAL_TASK_TYPES = {"Hunt", "Tame"}


def register_task_type(name: str, task_type: TaskType) -> None:
    TASK_TYPES[name] = task_type


def resolve_task_animal(world: "World", task: "Task"):
    """Shared lookup for Hunt/Tame targets: by the id bound at claim time if
    there is one, else by whichever animal currently sits on task.target.
    Duck-typed (id/x/y/is_dead) so task.py doesn't need to import animal.py."""
    animals = getattr(world, "animals", None)
    if not animals:
        return None
    if task.target_animal_id is not None:
        return next((a for a in animals if a.id == task.target_animal_id and not a.is_dead), None)
    return next((a for a in animals if tile_at(a.x, a.y) == task.target and not a.is_dead), None)


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


def _purge_dead_tasks(world: "World") -> None:
    """Drops unassigned tasks whose can_perform now says no - covers both
    "went stale before anyone even claimed it" (e.g. an overlapping Expand
    already claimed the target) and "was assigned, went invalid mid-work,
    got unassigned a moment ago" (the per-NPC loop below only clears
    assigned_npc, it doesn't remove the Task itself). Runs once at the top
    of each tick, using last tick's assignments, so nothing gets pulled out
    from under an NPC that's still actively deciding what to do with it
    this same tick. Without this the queue would otherwise accumulate dead
    entries forever - nothing else ever removes an unassigned task."""
    world.tasks.tasks = [
        task for task in world.tasks.tasks
        if task.assigned_npc is not None or task_can_perform(world, task)
    ]


def task_can_perform(world: "World", task: Task) -> bool:
    """True if this task's own can_perform (or the absence of one) says
    it's still doable - shared by the purge above and by game.py's queued-
    marker rendering, so "is this task dead" has exactly one definition."""
    task_type = TASK_TYPES.get(task.type)
    if task_type is None or task_type.can_perform is None:
        return True
    return task_type.can_perform(world, task)


def update_npc_tasks(world: "World", dt: float) -> None:
    """Single per-tick entry point: idle NPCs claim work, assigned NPCs walk
    to and perform it. If a task is blocked (e.g. missing materials), NPCs skip
    it and work on available tasks. Hungry NPCs consume food from the colony inventory."""
    _purge_dead_tasks(world)
    for npc in world.npcs:
        if getattr(npc, "is_resting", False):
            # Resting in sanctuary: check food consumption if hungry, and update recovery/hunger
            if npc.hunger <= HUNGER_EAT_THRESHOLD and not npc.is_dead:
                if world.inventory.consume_soonest_food(1) is not None:
                    npc.eat()
            npc.update(dt)
            # Full health: forcibly auto-deploy back to map at original position!
            if npc.health >= npc.max_health:
                npc.is_resting = False
                if getattr(npc, "sanctuary_orig_pos", None) is not None:
                    npc.x, npc.y = npc.sanctuary_orig_pos
                else:
                    cx, cy = world.grid.width // 2, world.grid.height // 2
                    npc.x, npc.y = tile_center(cx, cy)
                npc.path = []
                npc._auto_deployed = True
            continue


        # Colony food consumption: hungry NPCs eat from inventory (soonest-to-expire first)
        if npc.hunger <= HUNGER_EAT_THRESHOLD and not npc.is_dead:
            if world.inventory.consume_soonest_food(1) is not None:
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

        # Hunt/Tame chase a continuously-wandering animal by proximity
        # instead of by landing on its exact tile: re-path toward its
        # current tile while out of the NPC's combat_range, and once in
        # range stop closing the distance and start working in place - the
        # same auto-engage-by-proximity model monster combat already uses.
        # Progress simply pauses (never resets) while out of range, so a
        # target hopping tiles mid-approach no longer wipes accumulated work.
        if npc.task.type in ANIMAL_TASK_TYPES:
            animal = resolve_task_animal(world, npc.task)
            if animal is not None and not animal.is_dead:
                # Tells the animal (via wildlife.py's tick, later this same
                # frame) to stop initiating fresh wander hops while someone's
                # actively working it - see animal.py's is_targeted.
                animal.is_targeted = True
                if math.hypot(npc.x - animal.x, npc.y - animal.y) > npc.combat_range:
                    animal_tile = tile_at(animal.x, animal.y)
                    if npc.task.target != animal_tile or not npc.path:
                        path = find_path(
                            lambda x, y: world.grid.in_bounds(x, y) and not is_wall_blocked(world.buildings, x, y),
                            world.grid.width,
                            world.grid.height,
                            tile_at(npc.x, npc.y),
                            animal_tile,
                        )
                        if path:
                            npc.task.target = animal_tile
                            npc.set_path(path)
                    npc.update(dt)
                    continue
                npc.set_path([])  # in range - hold position and work instead of walking onto its tile

        npc.update(dt)
        if not npc.has_arrived:
            continue

        # Periodic rhythmic work SFX while actively working on tasks
        timer = getattr(npc, "work_sfx_timer", 0.0)
        should_play = False
        if timer == 0.0:
            should_play = True
            timer = 0.001
        else:
            timer += dt
            if timer >= 0.90:
                should_play = True
                timer = 0.001
        npc.work_sfx_timer = timer

        if should_play:
            if npc.task.type == "Gather":
                tile = world.grid.get(*npc.task.target)
                if tile.resource == "wood":
                    play_sfx("chop")
                elif tile.resource in ("raw_stone", "bricks", "marble"):
                    play_sfx("mine")
                elif tile.resource is not None:
                    play_sfx("gather")
            elif npc.task.type in ("BuildWall", "BuildTower", "BuildHouse", "BuildAnimalPen", "Farmland", "Destroy"):
                play_sfx("build")



        npc.task_progress += dt
        if task_type is None:
            continue
        required_seconds = task_type.work_seconds * npc.work_multiplier
        if npc.task.type == "Gather":
            # Gather Speed skill (ticket 23) stacks multiplicatively with the
            # role's own work_multiplier rather than replacing it.
            required_seconds *= gather_speed_multiplier(world)
        if npc.task_progress < required_seconds:
            continue

        finished = task_type.on_complete(world, npc.task)
        npc.work_sfx_timer = 0.0
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

            # Hunt/Tame targets may be outside claimed territory, so allow pathing across unblocked tiles
            targets_animal = task.type in ANIMAL_TASK_TYPES
            path = find_path(
                lambda x, y: (targets_animal or world.grid.get(x, y).claimed or (x, y) == task.target)
                and (not is_wall_blocked(world.buildings, x, y) or (x, y) == task.target),
                world.grid.width,
                world.grid.height,
                tile_at(npc.x, npc.y),
                task.target,
            )
            if path is None:
                continue

            if targets_animal and task.target_animal_id is None:
                animal = resolve_task_animal(world, task)
                if animal is not None:
                    task.target_animal_id = animal.id

            task.assigned_npc = npc
            npc.task = task
            npc.set_path(path)
            return

