import random
from dataclasses import dataclass

from constants import GRID_WIDTH, GRID_HEIGHT, START_REVEAL_RADIUS

RESOURCE_CHANCE = 0.12


@dataclass
class Tile:
    resource: str | None
    revealed: bool = False
    claimed: bool = False


class Grid:
    def __init__(self, seed: int | None = None):
        rng = random.Random(seed)
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.tiles = [
            [
                Tile(resource="crop" if rng.random() < RESOURCE_CHANCE else None)
                for _ in range(GRID_WIDTH)
            ]
            for _ in range(GRID_HEIGHT)
        ]
        start_x, start_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.expand(start_x, start_y, START_REVEAL_RADIUS)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def expand(self, cx: int, cy: int, radius: int) -> None:
        # ponytail: square-radius reveal, not circular — good enough until Expand task exists
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if self.in_bounds(x, y):
                    tile = self.get(x, y)
                    tile.revealed = True
                    tile.claimed = True
