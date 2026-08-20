from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from animal import Animal
from constants import ANIMAL_MAX_COUNT, ANIMAL_SPAWN_INTERVAL, ANIMAL_SPECIES, HUNT_SCATTER_LEAD_SECONDS
from coords import tile_at, tile_center
from day_night import DAY, NIGHT
from extensions import register_tick

if TYPE_CHECKING:
    from day_night import DayNightCycle
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
    # Any animal a queued or in-progress Hunt/Tame task is bound to (not
    # just one an NPC is actively chasing right now - task.py binds the id
    # at queue time, well before any NPC gets around to claiming it) is
    # leashed to a short range around where it was when selected (see
    # Animal.update()) instead of wandering freely - otherwise a busy
    # colony could let it wander arbitrarily far away while nobody's even
    # started walking toward it yet, turning "queue Hunt" into a long/
    # impractical chase.
    bound_animal_ids = {t.target_animal_id for t in world.tasks.tasks if t.target_animal_id is not None}

    for animal in world.animals:
        if animal.id in bound_animal_ids:
            animal.is_targeted = True
        animal.update(dt, world.grid.width, world.grid.height, world.npcs)
        # task.py also sets is_targeted earlier this same tick for anything
        # actively worked by an assigned NPC; clear it so next tick starts
        # from "not targeted" and it (or the bound-id check above) has to
        # re-affirm it if still true.
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


def _flee_point(animal, grid: "Grid") -> tuple[float, float]:
    """A point further out from the map center, along the direction the
    animal already sits relative to it - "fleeing outward" away from the
    player's territory, which always starts at the map center."""
    cx, cy = grid.width / 2.0, grid.height / 2.0
    ax, ay = tile_at(animal.x, animal.y)
    dx, dy = ax - cx, ay - cy
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    flee_tiles = 10
    tx = max(0, min(grid.width - 1, round(ax + ux * flee_tiles)))
    ty = max(0, min(grid.height - 1, round(ay + uy * flee_tiles)))
    return tile_center(tx, ty)


def scatter_unselected_wildlife(world: "World", cycle: "DayNightCycle") -> None:
    """Keeps the player's visible (revealed) area free of ambient wildlife
    at night: any wild animal that's never been selected for Hunt/Tame (no
    current task - queued or in-progress - references it) and isn't
    already tamed gets sent fleeing the moment it's standing on revealed
    ground while it's night, or in the HUNT_SCATTER_LEAD_SECONDS
    before night falls (so the area's already clear by the time night
    actually starts). Runs every tick through the whole night, not just
    once, so it also catches animals that wander back into view or spawn
    fresh mid-night - otherwise night could show ordinary wildlife right
    alongside real monsters, easy to mistake for one. A selected-but-not-
    yet-hunted animal is explicitly left alone; it's a deliberate target,
    not ambient wildlife."""
    if cycle.phase == NIGHT:
        pass
    elif cycle.phase == DAY and cycle.remaining() <= HUNT_SCATTER_LEAD_SECONDS:
        pass
    else:
        return

    bound_ids = {t.target_animal_id for t in world.tasks.tasks if t.target_animal_id is not None}
    grid = world.grid
    for animal in world.animals:
        if animal.id in bound_ids or getattr(animal, "is_tamed", False):
            continue
        tx, ty = tile_at(animal.x, animal.y)
        if not grid.in_bounds(tx, ty) or not grid.get(tx, ty).revealed:
            continue  # already out of the player's visible area
        if animal.idle_target is None:  # already fleeing - let it finish this leg
            animal.idle_target = _flee_point(animal, grid)
