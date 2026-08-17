from coords import tile_center
from monster import Monster, nearest_claimed_tile, spawn_monster


class _FakeTile:
    def __init__(self, claimed: bool):
        self.claimed = claimed


class _FakeGrid:
    def __init__(self, width: int, height: int, claimed: set[tuple[int, int]]):
        self.width = width
        self.height = height
        self._tiles = {
            (x, y): _FakeTile(claimed=(x, y) in claimed)
            for x in range(width)
            for y in range(height)
        }

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> _FakeTile:
        return self._tiles[(x, y)]


def test_nearest_claimed_tile_picks_closest():
    grid = _FakeGrid(5, 5, claimed={(2, 2), (4, 4)})
    assert nearest_claimed_tile(grid, (0, 0)) == (2, 2)


def test_nearest_claimed_tile_returns_none_when_nothing_claimed():
    grid = _FakeGrid(3, 3, claimed=set())
    assert nearest_claimed_tile(grid, (0, 0)) is None


def test_spawn_monster_paths_toward_nearest_claimed_tile():
    grid = _FakeGrid(5, 5, claimed={(4, 0)})
    monster = spawn_monster((0, 0), grid)
    assert monster.path
    assert monster.path[0] == (0, 0)
    assert monster.path[-1] == (4, 0)


def test_spawn_monster_has_no_path_when_no_claimed_tile_exists():
    grid = _FakeGrid(3, 3, claimed=set())
    monster = spawn_monster((0, 0), grid)
    assert monster.path == []


def test_monster_update_moves_toward_waypoint():
    start_x, start_y = tile_center(0, 0)
    monster = Monster(x=start_x, y=start_y, speed=100.0)
    monster.set_path([(2, 0)])
    monster.update(0.1)
    assert monster.x > start_x
    assert monster.y == start_y


def test_monster_is_dead_at_zero_health():
    monster = Monster(x=0.0, y=0.0)
    monster.health = 0
    assert monster.is_dead


class TestBurn:
    def test_apply_burn_sets_state(self):
        monster = Monster(x=0.0, y=0.0)
        monster.apply_burn(damage_per_tick=5, ticks=3)
        assert monster.burn_ticks_remaining == 3
        assert monster.burn_damage_per_tick == 5

    def test_burn_deals_damage_once_per_second(self):
        monster = Monster(x=0.0, y=0.0)
        start_health = monster.health
        monster.apply_burn(damage_per_tick=5, ticks=3)

        monster.update(0.5)
        assert monster.health == start_health  # under 1s, no tick yet

        monster.update(0.5)  # crosses the 1.0s mark
        assert monster.health == start_health - 5
        assert monster.burn_ticks_remaining == 2

    def test_burn_deals_total_damage_over_full_duration(self):
        monster = Monster(x=0.0, y=0.0)
        start_health = monster.health
        monster.apply_burn(damage_per_tick=5, ticks=3)

        for _ in range(4):  # 4 seconds, generous margin over the 3 ticks
            monster.update(1.0)

        assert monster.health == start_health - 15  # 3 ticks * 5
        assert monster.burn_ticks_remaining == 0

    def test_burn_expires_and_stops_dealing_damage(self):
        monster = Monster(x=0.0, y=0.0)
        monster.apply_burn(damage_per_tick=5, ticks=1)
        monster.update(1.0)
        health_after_expiry = monster.health

        monster.update(5.0)  # well past expiry
        assert monster.health == health_after_expiry

    def test_no_burn_by_default(self):
        monster = Monster(x=0.0, y=0.0)
        start_health = monster.health
        monster.update(10.0)
        assert monster.health == start_health

    def test_burn_does_not_error_when_monster_dies_mid_burn(self):
        monster = Monster(x=0.0, y=0.0)
        monster.health = 3
        monster.apply_burn(damage_per_tick=5, ticks=3)
        monster.update(1.0)  # first tick drops health below zero
        assert monster.is_dead
        monster.update(1.0)  # must not raise even though "dead"
        assert monster.burn_ticks_remaining == 1


class _Building:
    def __init__(self, type_: str, x: int, y: int):
        self.type = type_
        self.x = x
        self.y = y


def test_spawn_monster_routes_around_a_wall_blocking_the_direct_path():
    grid = _FakeGrid(3, 3, claimed={(2, 0)})
    buildings = [_Building("Wall", 1, 0)]  # sits on the straight-line route
    monster = spawn_monster((0, 0), grid, buildings)
    assert monster.path
    assert (1, 0) not in monster.path
    assert monster.path[-1] == (2, 0)


def test_spawn_monster_has_no_path_when_a_wall_blocks_the_only_route():
    grid = _FakeGrid(1, 3, claimed={(0, 2)})  # 1-tile-wide corridor, no detour possible
    buildings = [_Building("Wall", 0, 1)]
    monster = spawn_monster((0, 0), grid, buildings)
    assert monster.path == []
