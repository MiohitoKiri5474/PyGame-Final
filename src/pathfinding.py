import heapq
from typing import Callable

Tile = tuple[int, int]
IsWalkable = Callable[[int, int], bool]

_NEIGHBOR_DELTAS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _manhattan(a: Tile, b: Tile) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbors(tile: Tile, width: int, height: int, is_walkable: IsWalkable):
    x, y = tile
    for dx, dy in _NEIGHBOR_DELTAS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height and is_walkable(nx, ny):
            yield (nx, ny)


def find_path(
    is_walkable: IsWalkable, width: int, height: int, start: Tile, goal: Tile
) -> list[Tile] | None:
    """4-directional A* over a width x height grid. Returns the tile path
    including start and goal, or None if unreachable/unwalkable goal."""
    if not is_walkable(*start) or not is_walkable(*goal):
        return None
    if start == goal:
        return [start]

    open_heap: list[tuple[int, int, Tile]] = [(0, 0, start)]
    came_from: dict[Tile, Tile] = {}
    g_score: dict[Tile, int] = {start: 0}
    counter = 1  # tie-breaker so heap never compares Tile tuples directly

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        for neighbor in _neighbors(current, width, height, is_walkable):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + _manhattan(neighbor, goal)
                heapq.heappush(open_heap, (f_score, counter, neighbor))
                counter += 1

    return None
