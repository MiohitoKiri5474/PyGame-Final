import random
from collections import Counter

from constants import (
    GRID_HEIGHT,
    GRID_WIDTH,
    MONSTER_SPAWN_WEIGHTS,
    MONSTER_WEREWOLF,
    NEST_FIRST_SPAWN_DELAY,
    NEST_MAX_COUNT,
    NEST_SPAWN_COUNT_BASE,
    NEST_SPAWN_COUNT_MAX,
    NEST_SPAWN_COUNT_ROUNDS_PER_STEP,
)
from day_night import DAY, NIGHT
from grid import Grid
from nest import Nest, NestManager, create_initial_nests, monsters_per_spawn


def test_spawn_interval_shrinks_with_round_and_floors_at_minimum():
    nest = Nest(0, 0)
    assert nest.spawn_interval(1) == 25.0
    assert nest.spawn_interval(5) == 17.0
    assert nest.spawn_interval(50) == 4.0  # floored at NEST_MIN_SPAWN_INTERVAL


def test_nest_update_fires_once_interval_elapsed_and_resets_timer():
    nest = Nest(0, 0)
    assert nest.update(dt=15.0, round_number=1) is False
    assert nest.update(dt=11.0, round_number=1) is True  # 26s total >= 25s interval
    assert nest.spawn_timer == 0.0


def test_on_night_start_primes_nest_for_vanguard_wave():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    manager.on_night_start(round_number=1)
    # Nest is primed so the first spawn emerges in ~4s
    assert manager.nests[0].spawn_timer == 21.0
    # After 4.1s at night, the vanguard monster spawns!
    spawned = manager.update(dt=4.1, round_number=1, phase=NIGHT)
    assert spawned == [(0, 0)]


def test_nest_manager_only_spawns_monsters_at_night():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    spawned = manager.update(dt=20.0, round_number=1, phase=DAY)
    assert spawned == []


def test_nest_manager_spawns_at_night_once_interval_elapsed():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    # First tick after night falls consumes the guaranteed early spawn
    # (NEST_FIRST_SPAWN_DELAY) - isolate that from the regular per-nest
    # interval mechanism being tested here.
    manager.update(dt=NEST_FIRST_SPAWN_DELAY, round_number=1, phase=NIGHT)

    spawned = manager.update(dt=41.0, round_number=1, phase=NIGHT)
    assert spawned == [(0, 0)]


def test_nest_manager_guarantees_a_spawn_soon_after_night_falls():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    spawned = manager.update(dt=NEST_FIRST_SPAWN_DELAY + 0.1, round_number=1, phase=NIGHT)
    assert spawned == [(0, 0)]


def test_nest_manager_first_spawn_guarantee_does_not_fire_before_its_delay():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    spawned = manager.update(dt=NEST_FIRST_SPAWN_DELAY - 1.0, round_number=1, phase=NIGHT)
    assert spawned == []


def test_nest_manager_first_spawn_guarantee_only_fires_once_per_night():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    manager.update(dt=NEST_FIRST_SPAWN_DELAY + 0.1, round_number=1, phase=NIGHT)  # consumes it

    spawned = manager.update(dt=0.1, round_number=1, phase=NIGHT)
    assert spawned == []

    # A fresh day->night edge (next night) re-arms it
    manager.update(dt=1.0, round_number=1, phase=DAY)
    spawned = manager.update(dt=NEST_FIRST_SPAWN_DELAY + 0.1, round_number=1, phase=NIGHT)
    assert spawned == [(0, 0)]


def test_nest_manager_adds_new_nest_after_interval_elapses():
    manager = NestManager(width=10, height=10, nests=[], rng=random.Random(1))
    manager.update(dt=241.0, round_number=1, phase=DAY)
    assert len(manager.nests) == 1


def test_nest_manager_does_not_exceed_max_nest_count():
    manager = NestManager(
        width=10, height=10, nests=[Nest(x, 0) for x in range(NEST_MAX_COUNT)], rng=random.Random(1)
    )
    manager.update(dt=241.0, round_number=1, phase=DAY)
    assert len(manager.nests) == NEST_MAX_COUNT


def test_create_initial_nests_returns_requested_count_on_map_edge():
    nests = create_initial_nests(10, 10, 3, random.Random(1))
    assert len(nests) == 3
    for nest in nests:
        assert nest.x in (0, 9) or nest.y in (0, 9)


def test_pick_monster_type_returns_a_known_type():
    manager = NestManager(width=10, height=10, rng=random.Random(1))
    assert manager.pick_monster_type() in MONSTER_SPAWN_WEIGHTS


def test_pick_monster_type_distribution_favors_higher_weight():
    manager = NestManager(width=10, height=10, rng=random.Random(1))
    picks = Counter(manager.pick_monster_type() for _ in range(500))
    assert set(picks) == set(MONSTER_SPAWN_WEIGHTS)  # every type appears
    assert picks[MONSTER_WEREWOLF] == max(picks.values())  # highest weight (4 vs 3/3)


def test_monsters_per_spawn_ramps_with_round_and_caps():
    assert monsters_per_spawn(1) == NEST_SPAWN_COUNT_BASE
    assert monsters_per_spawn(NEST_SPAWN_COUNT_ROUNDS_PER_STEP + 1) == NEST_SPAWN_COUNT_BASE + 1
    assert monsters_per_spawn(1000) == NEST_SPAWN_COUNT_MAX  # capped, not unbounded


def test_nest_manager_spawns_multiple_monsters_per_firing_on_later_rounds():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    round_number = NEST_SPAWN_COUNT_ROUNDS_PER_STEP + 1  # bumps monsters_per_spawn to BASE + 1
    # First tick after night falls consumes the guaranteed early spawn -
    # isolate that from the regular per-nest interval mechanism being
    # tested here (it also produces monsters_per_spawn() monsters, which
    # would otherwise double up with the assertion below).
    manager.update(dt=NEST_FIRST_SPAWN_DELAY, round_number=round_number, phase=NIGHT)

    spawned = manager.update(dt=1000.0, round_number=round_number, phase=NIGHT)
    assert spawned == [(0, 0)] * (NEST_SPAWN_COUNT_BASE + 1)


def test_create_initial_nests_uses_revealed_frontier_when_grid_given():
    grid = Grid(seed=1)
    nests = create_initial_nests(GRID_WIDTH, GRID_HEIGHT, 3, random.Random(1), grid=grid)
    assert len(nests) == 3
    for nest in nests:
        assert not grid.get(nest.x, nest.y).revealed
        # sits right beside the revealed area, not out at the map's outer edge
        assert 0 < nest.x < GRID_WIDTH - 1 or 0 < nest.y < GRID_HEIGHT - 1


def test_create_initial_nests_falls_back_to_map_edge_without_a_grid():
    nests = create_initial_nests(10, 10, 3, random.Random(1))
    assert len(nests) == 3
    for nest in nests:
        assert nest.x in (0, 9) or nest.y in (0, 9)


def test_nest_manager_new_nest_follows_revealed_frontier_when_grid_given():
    grid = Grid(seed=1)
    manager = NestManager(GRID_WIDTH, GRID_HEIGHT, nests=[], rng=random.Random(1), grid=grid)
    manager.update(dt=241.0, round_number=1, phase=DAY)
    assert len(manager.nests) == 1
    new_nest = manager.nests[0]
    assert not grid.get(new_nest.x, new_nest.y).revealed
    assert new_nest.x not in (0, GRID_WIDTH - 1) and new_nest.y not in (0, GRID_HEIGHT - 1)


class _FakeTile:
    def __init__(self, revealed: bool, resource: str | None = None):
        self.revealed = revealed
        self.resource = resource


class _FakeGrid:
    """Minimal duck-typed grid for pinning exact revealed/resource layouts,
    rather than relying on a real Grid's random terrain/resource rolls."""

    def __init__(self, width: int, height: int, revealed: set[tuple[int, int]], resources: dict[tuple[int, int], str]):
        self.width = width
        self.height = height
        self._tiles = {
            (x, y): _FakeTile(revealed=(x, y) in revealed, resource=resources.get((x, y)))
            for x in range(width)
            for y in range(height)
        }

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> _FakeTile:
        return self._tiles[(x, y)]


def test_create_initial_nests_avoids_tiles_with_a_resource():
    # Every frontier tile of a 3x3 revealed square except (1, 4) below it
    # carries a crop - the nest must land on the one resource-free tile.
    revealed = {(x, y) for x in range(1, 4) for y in range(1, 4)}
    frontier = {(0, 1), (0, 2), (0, 3), (4, 1), (4, 2), (4, 3), (1, 0), (2, 0), (3, 0), (1, 4), (2, 4), (3, 4)}
    resources = {t: "crop" for t in frontier if t != (1, 4)}
    grid = _FakeGrid(5, 5, revealed=revealed, resources=resources)

    nests = create_initial_nests(5, 5, 1, random.Random(1), grid=grid)
    assert nests[0].x == 1 and nests[0].y == 4


def test_nest_manager_new_nest_avoids_tiles_with_a_resource():
    revealed = {(x, y) for x in range(1, 4) for y in range(1, 4)}
    frontier = {(0, 1), (0, 2), (0, 3), (4, 1), (4, 2), (4, 3), (1, 0), (2, 0), (3, 0), (1, 4), (2, 4), (3, 4)}
    resources = {t: "wood" for t in frontier if t != (2, 4)}
    grid = _FakeGrid(5, 5, revealed=revealed, resources=resources)

    manager = NestManager(5, 5, nests=[], rng=random.Random(1), grid=grid)
    manager.update(dt=241.0, round_number=1, phase=DAY)

    assert len(manager.nests) == 1
    assert (manager.nests[0].x, manager.nests[0].y) == (2, 4)
