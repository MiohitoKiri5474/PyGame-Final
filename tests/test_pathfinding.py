from pathfinding import find_path


def walkable_all(width, height):
    def fn(x, y):
        return 0 <= x < width and 0 <= y < height

    return fn


def assert_valid_path(path, start, goal, is_walkable):
    assert path is not None
    assert path[0] == start
    assert path[-1] == goal
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        assert abs(x1 - x2) + abs(y1 - y2) == 1  # 4-neighbour step
    for tile in path:
        assert is_walkable(*tile)


def test_finds_shortest_path_on_open_grid():
    is_walkable = walkable_all(5, 5)
    path = find_path(is_walkable, 5, 5, (0, 0), (3, 2))
    assert_valid_path(path, (0, 0), (3, 2), is_walkable)
    assert len(path) == 1 + 3 + 2  # start tile + manhattan distance steps


def test_returns_none_when_goal_unreachable():
    walls = {(1, 0), (1, 1), (1, 2)}  # vertical wall splitting a 3x3 grid

    def is_walkable(x, y):
        return 0 <= x < 3 and 0 <= y < 3 and (x, y) not in walls

    path = find_path(is_walkable, 3, 3, (0, 0), (2, 0))
    assert path is None


def test_returns_none_when_goal_is_unwalkable():
    def is_walkable(x, y):
        return (x, y) != (1, 1)

    path = find_path(is_walkable, 3, 3, (0, 0), (1, 1))
    assert path is None


def test_start_equals_goal_returns_single_tile_path():
    is_walkable = walkable_all(3, 3)
    path = find_path(is_walkable, 3, 3, (1, 1), (1, 1))
    assert path == [(1, 1)]


def test_path_routes_around_obstacle():
    walls = {(1, 1)}

    def is_walkable(x, y):
        return 0 <= x < 3 and 0 <= y < 3 and (x, y) not in walls

    path = find_path(is_walkable, 3, 3, (0, 1), (2, 1))
    assert_valid_path(path, (0, 1), (2, 1), is_walkable)
    assert len(path) == 5  # forced detour around the wall, optimal is 5 tiles
