from blocking import is_wall_blocked
from constants import (
    FIRE_BURN_TICK_INTERVAL,
    MONSTER_ATTACK,
    MONSTER_DEFENSE,
    MONSTER_MAX_HEALTH,
    MONSTER_SPEED,
)
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
        self.burn_ticks_remaining = 0
        self.burn_damage_per_tick = 0
        self.burn_tick_timer = 0.0

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def apply_burn(self, damage_per_tick: int, ticks: int) -> None:
        self.burn_damage_per_tick = damage_per_tick
        self.burn_ticks_remaining = ticks
        self.burn_tick_timer = 0.0

    def _tick_burn(self, dt: float) -> None:
        # Same "accumulate dt, fire at interval, reset to 0" shape as
        # DayNightCycle.update/Nest.update - a stalled frame just delays the
        # next tick by that same amount rather than catching up multiple
        # ticks at once, matching how those two already behave.
        if self.burn_ticks_remaining <= 0:
            return
        self.burn_tick_timer += dt
        if self.burn_tick_timer >= FIRE_BURN_TICK_INTERVAL:
            self.burn_tick_timer = 0.0
            self.health -= self.burn_damage_per_tick
            self.burn_ticks_remaining -= 1

    def update(self, dt: float) -> None:
        self._tick_burn(dt)
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


def spawn_monster(tile: tuple[int, int], grid, buildings=()) -> Monster:
    """Create a Monster at `tile` and path it toward the nearest claimed tile.
    Monsters walk in from outside territory, so unlike NPCs they treat every
    in-bounds tile as walkable (fog/unclaimed included) — except Wall tiles,
    which block like they do for NPCs (ticket 07)."""
    monster = Monster(*tile_center(*tile))
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
