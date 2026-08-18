from __future__ import annotations

from typing import TYPE_CHECKING

from build_task import _can_queue, _try_build, register_build_cost
from constants import (
    FARMLAND_ATTACK,
    FARMLAND_BLOCK,
    FARMLAND_COST,
    FARMLAND_GROW_SECONDS,
    FARMLAND_WORK_SECONDS,
    FARMLAND_YIELD,
    HARVEST_FARMLAND_WORK_SECONDS,
)
from extensions import register_tick
from task import Task, TaskType, register_task_type

if TYPE_CHECKING:
    from world import World
    from task import Tile

_can_queue_build_farmland = _can_queue  # same claimed-empty-resource-free rule as Wall/Tower/House


def _can_perform_build_farmland(world: "World", task: Task) -> bool:
    return all(world.inventory.get(res) >= amt for res, amt in FARMLAND_COST.items())


def _on_complete_build_farmland(world: "World", task: Task) -> bool:
    return _try_build(world, task, "Farmland", FARMLAND_COST, FARMLAND_BLOCK, FARMLAND_ATTACK)


def _find_farmland(world: "World", tile: "Tile"):
    x, y = tile
    return next((b for b in world.buildings if b.x == x and b.y == y and b.type == "Farmland"), None)


def _can_queue_harvest(world: "World", tile: "Tile") -> bool:
    farmland = _find_farmland(world, tile)
    if farmland is None or not farmland.ready:
        return False
    return not any(task.type == "HarvestFarmland" and task.target == tile for task in world.tasks.tasks)


def _can_perform_harvest(world: "World", task: Task) -> bool:
    # Unlike a gathered wild-resource tile (which never gets a new distinct
    # resource at the same coordinates), a destroyed Farmland CAN be rebuilt
    # on the same tile - identifying the target by coordinates alone would
    # let a stale queued task credit yield from an unrelated, not-yet-ready
    # Farmland that happens to occupy the old one's tile. Re-verify readiness
    # every tick, not just at completion.
    farmland = _find_farmland(world, task.target)
    return farmland is not None and farmland.ready


def _on_complete_harvest(world: "World", task: Task) -> bool:
    # can_perform already guarantees a ready Farmland is still there; this
    # None-guard only covers the (currently unreachable but cheap-to-keep-
    # safe) case of on_complete being called without going through it.
    farmland = _find_farmland(world, task.target)
    if farmland is None:
        return True
    world.inventory.add("crop", FARMLAND_YIELD)
    farmland.growth_timer = 0.0
    farmland.ready = False
    return True


def _tick_farmland_growth(world: "World", dt: float) -> None:
    for building in world.buildings:
        if building.type != "Farmland" or building.ready:
            continue
        building.growth_timer += dt
        if building.growth_timer >= FARMLAND_GROW_SECONDS:
            building.ready = True


register_task_type(
    "BuildFarmland",
    TaskType(
        work_seconds=FARMLAND_WORK_SECONDS,
        can_queue=_can_queue_build_farmland,
        on_complete=_on_complete_build_farmland,
        can_perform=_can_perform_build_farmland,
    ),
)

register_task_type(
    "HarvestFarmland",
    TaskType(
        work_seconds=HARVEST_FARMLAND_WORK_SECONDS,
        can_queue=_can_queue_harvest,
        on_complete=_on_complete_harvest,
        can_perform=_can_perform_harvest,
    ),
)

register_build_cost("BuildFarmland", FARMLAND_COST)
register_tick(_tick_farmland_growth)
