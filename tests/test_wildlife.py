import math
import random

from animal import Animal
from constants import ANIMAL_MAX_COUNT, ANIMAL_SPAWN_INTERVAL, ANIMAL_SPECIES, HUNT_SCATTER_LEAD_SECONDS
from coords import tile_center
from day_night import DAY, DayNightCycle, NIGHT
from grid import Grid
from wildlife import _tick_wildlife, _unclaimed_tiles, create_initial_animals, scatter_unselected_wildlife
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


def test_tick_wildlife_leashes_animal_bound_to_a_queued_hunt_task():
    # Bug repro (now with a leash rather than a full freeze): a wild animal
    # kept wandering arbitrarily far even after Hunt/Tame is queued on it,
    # since target_animal_id used to only get bound once an NPC actually
    # claimed the task - it could wander off its original tile before that
    # ever happened, and _purge_dead_tasks would then see no animal left at
    # task.target and silently drop the still-valid task. Binding the id at
    # queue time (task.py's TaskQueue.add) plus this leash together close
    # that gap while still letting the animal move a little.
    from constants import HUNT_TARGET_LEASH_RADIUS_TILES
    from coords import tile_at

    world = World(npc_count=0)
    world.animals = []

    bound = Animal(100.0, 100.0, species="Fish", speed=1000.0, dangerous=False, health=10)
    free = Animal(200.0, 200.0, species="Fish", speed=60.0, dangerous=False, health=10)
    world.animals = [bound, free]
    world.tasks.add("Hunt", (2, 2), target_animal_id=bound.id)

    start_tile = tile_at(bound.x, bound.y)
    for _ in range(60):
        _tick_wildlife(world, 1 / 60)
        tile = tile_at(bound.x, bound.y)
        assert math.hypot(tile[0] - start_tile[0], tile[1] - start_tile[1]) <= HUNT_TARGET_LEASH_RADIUS_TILES

    assert (free.x, free.y) != (200.0, 200.0) or free.path  # unbound animal is free to wander


def _cycle_with_remaining(phase: str, remaining: float) -> DayNightCycle:
    cycle = DayNightCycle()
    cycle.phase = phase
    cycle.timer = cycle.duration() - remaining
    return cycle


def _revealed_tile(world: "World") -> tuple[int, int]:
    """A tile guaranteed revealed on a fresh World() - the small radius
    around the map center that Grid.__init__ reveals at start."""
    return world.grid.width // 2, world.grid.height // 2


class TestScatterUnselectedWildlife:
    def test_never_selected_animal_flees_within_the_scatter_window(self):
        world = World(npc_count=0, animal_count=0)
        animal = Animal(*tile_center(*_revealed_tile(world)), species="WildBoar", speed=52.5, dangerous=False, health=30)
        world.animals.append(animal)
        cycle = _cycle_with_remaining(DAY, HUNT_SCATTER_LEAD_SECONDS - 1)

        scatter_unselected_wildlife(world, cycle)

        assert animal.idle_target is not None

    def test_leaves_an_animal_bound_to_a_queued_or_in_progress_task_alone(self):
        world = World(npc_count=0, animal_count=0)
        tile = _revealed_tile(world)
        animal = Animal(*tile_center(*tile), species="WildBoar", speed=52.5, dangerous=False, health=30)
        world.animals.append(animal)
        world.tasks.add("Hunt", tile, target_animal_id=animal.id)  # queued, not yet assigned
        cycle = _cycle_with_remaining(DAY, HUNT_SCATTER_LEAD_SECONDS - 1)

        scatter_unselected_wildlife(world, cycle)

        assert animal.idle_target is None

    def test_leaves_an_already_tamed_animal_alone(self):
        world = World(npc_count=0, animal_count=0)
        animal = Animal(*tile_center(*_revealed_tile(world)), species="WildBoar", speed=52.5, dangerous=False, health=30)
        animal.is_tamed = True
        world.animals.append(animal)
        cycle = _cycle_with_remaining(DAY, HUNT_SCATTER_LEAD_SECONDS - 1)

        scatter_unselected_wildlife(world, cycle)

        assert animal.idle_target is None

    def test_leaves_an_animal_outside_the_revealed_area_alone(self):
        # Nothing to gain by fleeing something the player can't see yet.
        world = World(npc_count=0, animal_count=0)
        far_tile = (1, 1)
        assert not world.grid.get(*far_tile).revealed  # precondition
        animal = Animal(*tile_center(*far_tile), species="WildBoar", speed=52.5, dangerous=False, health=30)
        world.animals.append(animal)
        cycle = _cycle_with_remaining(DAY, HUNT_SCATTER_LEAD_SECONDS - 1)

        scatter_unselected_wildlife(world, cycle)

        assert animal.idle_target is None

    def test_does_nothing_outside_the_scatter_window_during_day(self):
        world = World(npc_count=0, animal_count=0)
        animal = Animal(*tile_center(*_revealed_tile(world)), species="WildBoar", speed=52.5, dangerous=False, health=30)
        world.animals.append(animal)
        cycle = _cycle_with_remaining(DAY, HUNT_SCATTER_LEAD_SECONDS + 30)

        scatter_unselected_wildlife(world, cycle)

        assert animal.idle_target is None

    def test_scatters_a_never_selected_animal_throughout_the_night_too(self):
        # Not just a one-time pre-night sweep: catches wildlife that wanders
        # back into view, or spawns fresh, at any point during the night.
        world = World(npc_count=0, animal_count=0)
        animal = Animal(*tile_center(*_revealed_tile(world)), species="WildBoar", speed=52.5, dangerous=False, health=30)
        world.animals.append(animal)
        cycle = _cycle_with_remaining(NIGHT, 45.0)  # well into the night, not just the first tick

        scatter_unselected_wildlife(world, cycle)

        assert animal.idle_target is not None
