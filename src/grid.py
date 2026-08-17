import random
from dataclasses import dataclass

from constants import GRID_WIDTH, GRID_HEIGHT, START_CLAIM_RADIUS, START_REVEAL_RADIUS

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
        self.expand(start_x, start_y, START_CLAIM_RADIUS, START_REVEAL_RADIUS)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

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
                    self.get(x, y).claimed = True
