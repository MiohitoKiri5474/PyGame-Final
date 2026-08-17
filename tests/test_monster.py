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
