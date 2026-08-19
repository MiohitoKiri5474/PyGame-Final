from __future__ import annotations

import random
from typing import TYPE_CHECKING

from animal import Animal
from constants import ANIMAL_MAX_COUNT, ANIMAL_SPAWN_INTERVAL, ANIMAL_SPECIES
from coords import tile_center
from extensions import register_tick

if TYPE_CHECKING:
    from grid import Grid
    from world import World

Tile = tuple[int, int]


def _unclaimed_tiles(grid: "Grid") -> list[Tile]:
    return [(x, y) for y in range(grid.height) for x in range(grid.width) if not grid.get(x, y).claimed]


def _spawn_animal(tile: Tile, rng: random.Random) -> Animal:
    species = rng.choice(list(ANIMAL_SPECIES.keys()))
    speed, dangerous, health = ANIMAL_SPECIES[species]
    x, y = tile_center(*tile)
    return Animal(x, y, species=species, speed=speed, dangerous=dangerous, health=health, rng=rng)


def create_initial_animals(grid: "Grid", count: int, rng: random.Random | None = None) -> list[Animal]:
    """Place animals on unclaimed/frontier tiles, away from claimed territory."""
    rng = rng or random.Random()
    candidates = _unclaimed_tiles(grid)
    chosen = rng.sample(candidates, min(count, len(candidates)))
    return [_spawn_animal(tile, rng) for tile in chosen]


def _tick_wildlife(world: "World", dt: float) -> None:
    for animal in world.animals:
        animal.update(dt, world.grid.width, world.grid.height, world.npcs)
        # task.py sets is_targeted earlier this same tick for anything being
        # actively hunted/tamed right now; clear it so next tick starts from
        # "not targeted" and task.py has to re-affirm it if still true.
        animal.is_targeted = False

    world.animal_spawn_timer += dt
    if world.animal_spawn_timer >= ANIMAL_SPAWN_INTERVAL:
        world.animal_spawn_timer = 0.0
        if len(world.animals) < ANIMAL_MAX_COUNT:
            candidates = _unclaimed_tiles(world.grid)
            if candidates:
                tile = world.wildlife_rng.choice(candidates)
                world.animals.append(_spawn_animal(tile, world.wildlife_rng))


register_tick(_tick_wildlife)
