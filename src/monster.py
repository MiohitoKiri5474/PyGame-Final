from blocking import is_wall_blocked
from constants import (
    MONSTER_ATTACK,
    MONSTER_DEFENSE,
    MONSTER_MAX_HEALTH,
    MONSTER_SPEED,
    MONSTER_STATS,
)
from coords import tile_center
from movement import step_toward_path
from pathfinding import find_path


class Monster:
    def __init__(
        self,
        x: float,
        y: float,
        speed: float = MONSTER_SPEED,
        type: str | None = None,
    ):
        self.x = x
        self.y = y
        self.type = type
        self.path: list[tuple[int, int]] = []

        stats = MONSTER_STATS.get(type)
        if stats is not None:
            self.speed = stats["speed"]
            self.health = stats["max_health"]
            self.max_health = stats["max_health"]
            self.attack = stats["attack"]
            self.defense = stats["defense"]
            self.life_steal = stats.get("life_steal", False)
        else:
            self.speed = speed
            self.health = MONSTER_MAX_HEALTH
            self.max_health = MONSTER_MAX_HEALTH
            self.attack = MONSTER_ATTACK
            self.defense = MONSTER_DEFENSE
            self.life_steal = False

        self.burn_remaining: float = 0.0
        self.burn_dps: float = 0.0
        self.frozen_timer: float = 0.0

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def update(self, dt: float) -> None:
        if self.burn_remaining > 0:
            burn_dt = min(dt, self.burn_remaining)
            self.health -= self.burn_dps * burn_dt
            self.burn_remaining -= burn_dt

        if self.frozen_timer > 0:
            self.frozen_timer = max(0.0, self.frozen_timer - dt)
            return  # Skip movement step while frozen

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


def spawn_monster(tile: tuple[int, int], grid, buildings=(), monster_type: str | None = None) -> Monster:
    """Create a Monster at `tile` and path it toward the nearest claimed tile.
    Monsters walk in from outside territory, so unlike NPCs they treat every
    in-bounds tile as walkable (fog/unclaimed included) — except Wall tiles,
    which block like they do for NPCs (ticket 07)."""
    monster = Monster(*tile_center(*tile), type=monster_type)
    target = nearest_claimed_tile(grid, tile)
    if target is not None:
        path = find_path(
            lambda x, y: grid.in_bounds(x, y) and not is_wall_blocked(buildings, x, y),
            grid.width,
            grid.height,
            tile,
            target,
        )
        if path:
            monster.set_path(path)
    return monster

