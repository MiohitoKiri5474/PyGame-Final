from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from blocking import is_wall_blocked
from constants import (
    WALL_WORK_SECONDS,
    WALL_COST,
    WALL_BLOCK,
    WALL_ATTACK,
    TOWER_WORK_SECONDS,
    TOWER_COST,
    TOWER_BLOCK,
    TOWER_ATTACK,
)
from coords import tile_at, tile_center
from extensions import register_hud_line
from task import Task, TaskType, register_task_type

if TYPE_CHECKING:
    from world import World
    from task import Tile


@dataclass
class Building:
    type: str
    x: int
    y: int
    block: int
    attack: int


def _can_queue(world: "World", tile: "Tile") -> bool:
    x, y = tile
    t = world.grid.get(x, y)
    if not t.claimed or t.resource is not None:
        return False
    if any(b.x == x and b.y == y for b in world.buildings):
        return False
    if any(task.type.startswith("Build") and task.target == tile for task in world.tasks.tasks):
        return False
    return True


def _can_perform_wall(world: "World", task: Task) -> bool:
    return all(world.inventory.get(res) >= amt for res, amt in WALL_COST.items())


def _can_perform_tower(world: "World", task: Task) -> bool:
    return all(world.inventory.get(res) >= amt for res, amt in TOWER_COST.items())


def _on_complete_wall(world: "World", task: Task) -> bool:
    return _try_build(world, task, "Wall", WALL_COST, WALL_BLOCK, WALL_ATTACK)


def _on_complete_tower(world: "World", task: Task) -> bool:
    return _try_build(world, task, "Tower", TOWER_COST, TOWER_BLOCK, TOWER_ATTACK)


def _try_build(world: "World", task: Task, b_type: str, cost: dict[str, int], block: int, attack: int) -> bool:
    if not world.inventory.spend_all(cost):
        return False

    x, y = task.target
    world.buildings.append(Building(type=b_type, x=x, y=y, block=block, attack=attack))

    # If building is a Wall, displace any NPCs standing on the tile to an adjacent free side
    if b_type == "Wall":
        _displace_npcs_from_wall(world, x, y)

    return True


def _displace_npcs_from_wall(world: "World", x: int, y: int) -> None:
    candidate_tiles = []
    # 4-cardinal first, then diagonals; prefer claimed, non-wall tiles
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        nx, ny = x + dx, y + dy
        if world.grid.in_bounds(nx, ny) and not is_wall_blocked(world.buildings, nx, ny):
            if world.grid.get(nx, ny).claimed:
                candidate_tiles.append((nx, ny))

    # Fallback to any unblocked tile in bounds
    if not candidate_tiles:
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = x + dx, y + dy
            if world.grid.in_bounds(nx, ny) and not is_wall_blocked(world.buildings, nx, ny):
                candidate_tiles.append((nx, ny))

    target_tile = candidate_tiles[0] if candidate_tiles else (x, y)
    target_pos = tile_center(*target_tile)

    for npc in world.npcs:
        if tile_at(npc.x, npc.y) == (x, y):
            npc.x, npc.y = target_pos
            npc.path = []
        elif (x, y) in npc.path:
            # Clear path if it previously routed through the newly built wall
            npc.path = []


_COSTS_BY_TASK_TYPE = {"BuildWall": WALL_COST, "BuildTower": TOWER_COST}


def _blocked_builds_hud_line(world: "World") -> str:
    # Insufficient-funds tasks stay queued but are skipped by NPCs until
    # affordable — report them so that's visible to the player.
    blocked = sorted(
        {
            task.type
            for task in world.tasks.tasks
            if task.type in _COSTS_BY_TASK_TYPE
            and any(world.inventory.get(res) < amt for res, amt in _COSTS_BY_TASK_TYPE[task.type].items())
        }
    )
    if not blocked:
        return ""
    return f"Build blocked (insufficient resources): {', '.join(blocked)}"


register_task_type(
    "BuildWall",
    TaskType(
        work_seconds=WALL_WORK_SECONDS,
        can_queue=_can_queue,
        on_complete=_on_complete_wall,
        can_perform=_can_perform_wall,
    ),
)

register_task_type(
    "BuildTower",
    TaskType(
        work_seconds=TOWER_WORK_SECONDS,
        can_queue=_can_queue,
        on_complete=_on_complete_tower,
        can_perform=_can_perform_tower,
    ),
)

register_hud_line(_blocked_builds_hud_line)
