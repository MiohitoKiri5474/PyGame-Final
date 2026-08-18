"""Pygame-free population growth: +1 NPC every 3 rounds, capped by
population_cap(world)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from blocking import is_wall_blocked
from build_task import population_cap
from constants import ROLES
from coords import tile_center
from npc import NPC

if TYPE_CHECKING:
    from world import World

ROUND_INTERVAL = 3

# 4-cardinal first, then diagonals - same preference order build_task.py's
# _displace_npcs_from_wall uses when steering an NPC off a newly built Wall.
_ADJACENT_DELTAS = ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))


def _spawn_tile(world: "World") -> tuple[int, int]:
    """Colony center is the normal spawn point. Buildings allow free
    placement with no adjacency rule, so a Wall can end up sitting exactly on
    that tile; task.py's pathfinding treats a Wall tile as impassable even
    for the NPC standing on it (blocking.is_wall_blocked), which would leave
    a center-spawned NPC unable to path to any task, forever. Fall back to
    the nearest unblocked claimed tile in that case."""
    cx, cy = world.grid.width // 2, world.grid.height // 2
    if not is_wall_blocked(world.buildings, cx, cy):
        return cx, cy
    for dx, dy in _ADJACENT_DELTAS:
        nx, ny = cx + dx, cy + dy
        if (
            world.grid.in_bounds(nx, ny)
            and world.grid.get(nx, ny).claimed
            and not is_wall_blocked(world.buildings, nx, ny)
        ):
            return nx, ny
    return cx, cy  # no unblocked neighbor found - center is still the least-bad choice


def maybe_spawn_npc(world: "World", round_number: int, transitioned: bool) -> NPC | None:
    """Spawn 1 NPC at the colony center on round_number 3, 6, 9, ...

    `transitioned` must already mean "this was specifically the night->day
    transition" - round_number alone repeats across two consecutive
    transitions (night->day into round N, then day->night back out of round
    N), so a caller passing transitioned=True for both would double-spawn.
    game.py resolves this by passing `transitioned and cycle.phase == DAY`.
    """
    if not transitioned or round_number % ROUND_INTERVAL != 0:
        return None
    if len(world.npcs) >= population_cap(world):
        return None

    role = ROLES[len(world.npcs) % len(ROLES)]
    x, y = tile_center(*_spawn_tile(world))
    npc = NPC(x, y, role=role)
    world.npcs.append(npc)
    return npc
