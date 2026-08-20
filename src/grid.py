import random
from dataclasses import dataclass

from constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    START_CLAIM_RADIUS,
    START_REVEAL_RADIUS,
    RESOURCE_WEIGHTS,
    TERRAIN_PLAIN,
    TERRAIN_RIVER,
    TERRAIN_MOUNTAIN,
    TERRAIN_MUD,
    TERRAIN_SCORCHED,
)

_RESOURCE_POOL = list(RESOURCE_WEIGHTS.keys())
_RESOURCE_POOL_WEIGHTS = list(RESOURCE_WEIGHTS.values())


@dataclass
class Tile:
    resource: str | None
    revealed: bool = False
    claimed: bool = False
    terrain: str = TERRAIN_PLAIN


def _roll_resource(rng: random.Random, terrain: str = TERRAIN_PLAIN) -> str | None:
    if terrain == TERRAIN_MOUNTAIN:
        return None
    return rng.choices(_RESOURCE_POOL, weights=_RESOURCE_POOL_WEIGHTS, k=1)[0]



def _generate_terrain_map(
    width: int, height: int, rng: random.Random, start_x: int, start_y: int, safe_radius: int
) -> list[list[str]]:
    grid_terrain = [[TERRAIN_PLAIN for _ in range(width)] for _ in range(height)]

    # 1. Winding River across the map
    rx = rng.randint(width // 4, width * 3 // 4)
    for y in range(height):
        for w_offset in (-1, 0):
            cur_x = rx + w_offset
            if 0 <= cur_x < width:
                if abs(cur_x - start_x) > safe_radius or abs(y - start_y) > safe_radius:
                    grid_terrain[y][cur_x] = TERRAIN_RIVER
        rx = max(2, min(width - 3, rx + rng.choice([-1, 0, 0, 1])))

    # 2. Mountain Ranges & Massifs (3-4 organic connected ranges)
    num_ranges = rng.randint(3, 4)
    for _ in range(num_ranges):
        # Pick anchor away from colony start
        for _attempt in range(20):
            mx = rng.randint(4, width - 5)
            my = rng.randint(4, height - 5)
            if abs(mx - start_x) > safe_radius + 3 or abs(my - start_y) > safe_radius + 3:
                break

        length = rng.randint(6, 10)
        cur_x, cur_y = mx, my
        primary_axis = rng.choice(["H", "V"])

        for _step in range(length):
            # Place a solid connected cluster (2-3 tiles wide) around current spine point
            w_span = rng.randint(1, 2)
            h_span = rng.randint(1, 2)
            for ox in range(-w_span + 1, w_span + 1):
                for oy in range(-h_span + 1, h_span + 1):
                    cx, cy = cur_x + ox, cur_y + oy
                    if 1 <= cx < width - 1 and 1 <= cy < height - 1:
                        if abs(cx - start_x) > safe_radius or abs(cy - start_y) > safe_radius:
                            grid_terrain[cy][cx] = TERRAIN_MOUNTAIN

            # Step cardinally along spine with natural wander
            if primary_axis == "H":
                cur_x += rng.choice([1, 1, 2])
                cur_y += rng.choice([-1, 0, 0, 1])
            else:
                cur_y += rng.choice([1, 1, 2])
                cur_x += rng.choice([-1, 0, 0, 1])

    # 3. Mud / Swamp Patches (2-4 patches)
    num_swamps = rng.randint(2, 4)
    for _ in range(num_swamps):
        sx = rng.randint(3, width - 4)
        sy = rng.randint(3, height - 4)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                cx, cy = sx + dx, sy + dy
                if 0 <= cx < width and 0 <= cy < height:
                    if abs(cx - start_x) > safe_radius or abs(cy - start_y) > safe_radius:
                        if grid_terrain[cy][cx] != TERRAIN_MOUNTAIN and grid_terrain[cy][cx] != TERRAIN_RIVER:
                            grid_terrain[cy][cx] = TERRAIN_MUD

    # 4. Scorched Earth Zones (2-4 patches)
    num_scorched = rng.randint(2, 4)
    for _ in range(num_scorched):
        sc_x = rng.randint(3, width - 4)
        sc_y = rng.randint(3, height - 4)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                cx, cy = sc_x + dx, sc_y + dy
                if 0 <= cx < width and 0 <= cy < height:
                    if abs(cx - start_x) > safe_radius or abs(cy - start_y) > safe_radius:
                        if grid_terrain[cy][cx] == TERRAIN_PLAIN:
                            grid_terrain[cy][cx] = TERRAIN_SCORCHED

    # Ensure safe zone around start is guaranteed plain
    for y in range(max(0, start_y - safe_radius), min(height, start_y + safe_radius + 1)):
        for x in range(max(0, start_x - safe_radius), min(width, start_x + safe_radius + 1)):
            grid_terrain[y][x] = TERRAIN_PLAIN

    return grid_terrain


class Grid:
    def __init__(self, seed: int | None = None):
        rng = random.Random(seed)
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        start_x, start_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        terrain_map = _generate_terrain_map(
            GRID_WIDTH, GRID_HEIGHT, rng, start_x, start_y, START_CLAIM_RADIUS
        )

        self.tiles = [
            [
                Tile(
                    resource=_roll_resource(rng, terrain_map[y][x]),
                    terrain=terrain_map[y][x],
                )
                for x in range(GRID_WIDTH)
            ]
            for y in range(GRID_HEIGHT)
        ]
        # Strictly guarantee mountains never have any resources
        for row in self.tiles:
            for tile in row:
                if tile.terrain == TERRAIN_MOUNTAIN:
                    tile.resource = None

        self.expand(start_x, start_y, START_CLAIM_RADIUS, START_REVEAL_RADIUS)


    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def _reveal_mountain_massif(self, start_x: int, start_y: int) -> None:

        """Flood-reveals and claims an entire connected mountain massif when any part is explored,
        ensuring mountain interiors are never trapped in fog/parchment."""
        queue = [(start_x, start_y)]
        visited = {(start_x, start_y)}
        while queue:
            x, y = queue.pop(0)
            tile = self.get(x, y)
            tile.revealed = True
            tile.claimed = True
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny) and (nx, ny) not in visited:
                    nbr = self.get(nx, ny)
                    if getattr(nbr, "terrain", "plain") == TERRAIN_MOUNTAIN:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

    def expand(self, cx: int, cy: int, claim_radius: int, reveal_radius: int | None = None) -> None:
        # ponytail: square-radius, not circular — good enough for this game's feel
        if reveal_radius is None:
            reveal_radius = claim_radius
        for y in range(cy - reveal_radius, cy + reveal_radius + 1):
            for x in range(cx - reveal_radius, cx + reveal_radius + 1):
                if self.in_bounds(x, y):
                    self.get(x, y).revealed = True
        for y in range(cy - claim_radius, cy + claim_radius + 1):
            for x in range(cx - claim_radius, cx + claim_radius + 1):
                if self.in_bounds(x, y):
                    tile = self.get(x, y)
                    tile.claimed = True
                    if getattr(tile, "terrain", "plain") == TERRAIN_MOUNTAIN:
                        self._reveal_mountain_massif(x, y)


