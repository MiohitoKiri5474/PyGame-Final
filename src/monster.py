import math

from blocking import is_wall_blocked
from constants import (
    FIRE_BURN_TICK_INTERVAL,
    MONSTER_ATTACK,
    MONSTER_DEFENSE,
    MONSTER_MAX_HEALTH,
    MONSTER_SPEED,
    MONSTER_STATS,
)
from coords import tile_at, tile_center
from movement import step_toward_path
from pathfinding import find_path


class Monster:
    def __init__(self, x: float, y: float, speed: float | None = None, type: str | None = None):
        self.x = x
        self.y = y
        self.type = type
        stats = MONSTER_STATS.get(type, {})
        # speed accepts an explicit override (save.py's load path always
        # passes the exact persisted speed) that wins over a type's table
        # speed, which wins over the untyped flat-constant default.
        self.speed = speed if speed is not None else stats.get("speed", MONSTER_SPEED)
        self.max_health = stats.get("max_health", MONSTER_MAX_HEALTH)
        self.path: list[tuple[int, int]] = []
        self.health = self.max_health
        self.attack = stats.get("attack", MONSTER_ATTACK)
        self.defense = stats.get("defense", MONSTER_DEFENSE)
        self.life_steal = stats.get("life_steal", False)
        self.burn_ticks_remaining = 0
        self.burn_damage_per_tick = 0
        self.burn_tick_timer = 0.0
        self.frozen_remaining = 0.0

        # Paper Mario Animation & Combat states
        self.facing_left = False
        self.display_facing_left = False
        self.flip_progress = 1.0
        self.anim_timer = 0.0
        self.is_moving = False
        self.attack_timer = 0.0
        self.hit_timer = 0.0
        self.combat_target: tuple[float, float] | None = None

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    @property
    def is_frozen(self) -> bool:
        return self.frozen_remaining > 0

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def trigger_attack(self, target_x: float, target_y: float) -> None:
        """Trigger a monster pounce/bite attack towards target."""
        self.attack_timer = 0.35
        self.combat_target = (target_x, target_y)
        if target_x < self.x:
            self.facing_left = True
            self.display_facing_left = True
        elif target_x > self.x:
            self.facing_left = False
            self.display_facing_left = False

    def trigger_hit(self) -> None:
        """Trigger a damage reaction squash & hurt flash."""
        self.hit_timer = 0.25

    def apply_freeze(self, duration: float) -> None:
        self.frozen_remaining = duration  # overwrite, not add - refresh, never stack

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

    def _tick_freeze(self, dt: float) -> None:
        if self.frozen_remaining > 0:
            self.frozen_remaining = max(0.0, self.frozen_remaining - dt)

    def update(self, dt: float) -> None:
        self._tick_burn(dt)
        self._tick_freeze(dt)
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hit_timer = max(0.0, self.hit_timer - dt)

        if self.is_frozen:
            self.is_moving = False
            return  # movement skipped entirely while frozen, not halved

        old_x = self.x
        self.x, self.y, self.path = step_toward_path(self.x, self.y, self.path, self.speed, dt)
        dx = self.x - old_x
        if abs(dx) > 0.01:
            new_facing = (dx < 0.0)
            if new_facing != self.facing_left:
                self.facing_left = new_facing
                self.flip_progress = 0.0

        if self.flip_progress < 1.0:
            self.flip_progress = min(1.0, self.flip_progress + dt * 8.0)
            if self.flip_progress >= 0.5:
                self.display_facing_left = self.facing_left
        else:
            self.display_facing_left = self.facing_left

        if not self.has_arrived:
            self.is_moving = True
            self.anim_timer += dt
        else:
            self.is_moving = False



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


def _path_toward(start: tuple[int, int], target: tuple[int, int], grid, buildings) -> list[tuple[int, int]] | None:
    """Monsters walk in from outside territory, so unlike NPCs they treat
    every in-bounds tile as walkable (fog/unclaimed included) — except Wall
    tiles, which block like they do for NPCs (ticket 07)."""
    return find_path(
        lambda x, y: grid.in_bounds(x, y) and not is_wall_blocked(buildings, x, y),
        grid.width,
        grid.height,
        start,
        target,
    )


def spawn_monster(tile: tuple[int, int], grid, buildings=(), monster_type: str | None = None) -> Monster:
    """Create a Monster at `tile` and path it toward the nearest claimed tile."""
    monster = Monster(*tile_center(*tile), type=monster_type)
    target = nearest_claimed_tile(grid, tile)
    if target is not None:
        path = _path_toward(tile, target, grid, buildings)
        if path:
            monster.set_path(path)
    return monster


def retarget_monster(monster: Monster, world) -> None:
    """Call once a monster's path is empty (fresh from spawn_monster's
    initial fallback-free path, or because it just walked its previous
    target's path to completion) - picks a new target and paths to it, so
    monsters keep actively closing in instead of freezing in place once
    they reach wherever they were first sent. Prefers the nearest living
    NPC (this is the actual "chase" behavior); falls back to the nearest
    claimed tile if the colony has no NPCs left, so monsters still
    advance on the territory itself rather than idling forever."""
    start = tile_at(monster.x, monster.y)

    target = None
    if world.npcs:
        nearest_npc = min(world.npcs, key=lambda npc: math.hypot(npc.x - monster.x, npc.y - monster.y))
        target = tile_at(nearest_npc.x, nearest_npc.y)
    if target is None:
        target = nearest_claimed_tile(world.grid, start)
    if target is None or target == start:
        return

    path = _path_toward(start, target, world.grid, world.buildings)
    if path:
        monster.set_path(path)
