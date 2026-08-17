from constants import MONSTER_ATTACK, MONSTER_DEFENSE, MONSTER_MAX_HEALTH, MONSTER_SPEED
from coords import tile_center
from movement import step_toward_path
from pathfinding import find_path


class Monster:
    def __init__(self, x: float, y: float, speed: float = MONSTER_SPEED):
        self.x = x
        self.y = y
        self.speed = speed
        self.path: list[tuple[int, int]] = []
        self.health = MONSTER_MAX_HEALTH
        self.attack = MONSTER_ATTACK
        self.defense = MONSTER_DEFENSE

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def update(self, dt: float) -> None:
        self.x, self.y, self.path = step_toward_path(self.x, self.y, self.path, self.speed, dt)


def nearest_claimed_tile(grid, from_tile: tuple[int, int]) -> tuple[int, int] | None:
    fx, fy = from_tile
    best, best_dist = None, None
    for y in range(grid.height):
        for x in range(grid.width):
            if grid.get(x, y).claimed:
                dist = abs(x - fx) + abs(y - fy)
                if best_dist is None or dist < best_dist:
                    best, best_dist = (x, y), dist
    return best


def spawn_monster(tile: tuple[int, int], grid) -> Monster:
    """Create a Monster at `tile` and path it toward the nearest claimed tile.
    Monsters walk in from outside territory, so unlike NPCs they treat every
    in-bounds tile as walkable (fog/unclaimed included) — only Wall tiles,
    wired in by ticket 07, will block them."""
    monster = Monster(*tile_center(*tile))
    target = nearest_claimed_tile(grid, tile)
    if target is not None:
        path = find_path(grid.in_bounds, grid.width, grid.height, tile, target)
        if path:
            monster.set_path(path)
    return monster
