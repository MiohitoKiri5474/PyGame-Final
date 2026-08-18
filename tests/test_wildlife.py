import random

from animal import Animal
from constants import ANIMAL_MAX_COUNT, ANIMAL_SPAWN_INTERVAL, ANIMAL_SPECIES
from grid import Grid
from wildlife import _tick_wildlife, _unclaimed_tiles, create_initial_animals
from world import World


def _mostly_unclaimed_grid() -> Grid:
    grid = Grid()
    # new-game Grid already claims a small radius around the center; the
    # rest of the map (most of it) stays unclaimed, which is what we need
    return grid


def test_create_initial_animals_only_spawns_on_unclaimed_tiles():
    grid = _mostly_unclaimed_grid()
    animals = create_initial_animals(grid, count=15, rng=random.Random(1))
    for animal in animals:
        from coords import tile_at

        tx, ty = tile_at(animal.x, animal.y)
        assert not grid.get(tx, ty).claimed


def test_create_initial_animals_respects_requested_count():
    grid = _mostly_unclaimed_grid()
    animals = create_initial_animals(grid, count=7, rng=random.Random(2))
    assert len(animals) == 7


def test_create_initial_animals_caps_at_available_unclaimed_tiles():
    grid = _mostly_unclaimed_grid()
    available = len(_unclaimed_tiles(grid))
    animals = create_initial_animals(grid, count=available + 1000, rng=random.Random(3))
    assert len(animals) == available


def test_create_initial_animals_uses_species_from_the_named_table():
    grid = _mostly_unclaimed_grid()
    animals = create_initial_animals(grid, count=20, rng=random.Random(4))
    for animal in animals:
        assert animal.species in ANIMAL_SPECIES
        speed, dangerous, health = ANIMAL_SPECIES[animal.species]
        assert animal.speed == speed
        assert animal.dangerous == dangerous
        assert animal.health == health


def _dummy_animals(n: int) -> list[Animal]:
    return [Animal(0.0, 0.0, species="Fish", speed=60.0, dangerous=False, health=10) for _ in range(n)]


def test_tick_wildlife_tops_up_population_after_interval_elapses():
    world = World(npc_count=0)
    world.animals = []
    world.animal_spawn_timer = 0.0

    _tick_wildlife(world, ANIMAL_SPAWN_INTERVAL)

    assert len(world.animals) == 1


def test_tick_wildlife_does_not_spawn_before_interval_elapses():
    world = World(npc_count=0)
    world.animals = []
    world.animal_spawn_timer = 0.0

    _tick_wildlife(world, ANIMAL_SPAWN_INTERVAL - 1.0)

    assert len(world.animals) == 0


def test_tick_wildlife_never_exceeds_max_count():
    world = World(npc_count=0)
    world.animals = _dummy_animals(ANIMAL_MAX_COUNT)
    world.animal_spawn_timer = 0.0

    _tick_wildlife(world, ANIMAL_SPAWN_INTERVAL)

    assert len(world.animals) == ANIMAL_MAX_COUNT
