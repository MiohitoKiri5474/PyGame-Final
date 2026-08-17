import random

from constants import NEST_MAX_COUNT
from day_night import DAY, NIGHT
from nest import Nest, NestManager, create_initial_nests


def test_spawn_interval_shrinks_with_round_and_floors_at_minimum():
    nest = Nest(0, 0)
    assert nest.spawn_interval(1) == 15.0
    assert nest.spawn_interval(5) == 11.0
    assert nest.spawn_interval(50) == 4.0  # floored at NEST_MIN_SPAWN_INTERVAL


def test_nest_update_fires_once_interval_elapsed_and_resets_timer():
    nest = Nest(0, 0)
    assert nest.update(dt=10.0, round_number=1) is False
    assert nest.update(dt=6.0, round_number=1) is True  # 16s total >= 15s interval
    assert nest.spawn_timer == 0.0


def test_nest_manager_only_spawns_monsters_at_night():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    spawned = manager.update(dt=20.0, round_number=1, phase=DAY)
    assert spawned == []


def test_nest_manager_spawns_at_night_once_interval_elapsed():
    manager = NestManager(width=10, height=10, nests=[Nest(0, 0)])
    spawned = manager.update(dt=20.0, round_number=1, phase=NIGHT)
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
