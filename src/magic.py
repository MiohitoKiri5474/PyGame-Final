from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from constants import (
    COLOR_FIRE_FLASH,
    COLOR_LIGHTNING_FLASH,
    FIRE_BURN_DAMAGE_PER_TICK,
    FIRE_BURN_TICKS,
    FIRE_COOLDOWN,
    FIRE_DAMAGE,
    LIGHTNING_COOLDOWN,
    LIGHTNING_DAMAGE,
    MAGIC_FLASH_DURATION,
    ROLE_MAGE,
)
from coords import tile_at
from extensions import register_hud_line, register_tick
from monster import nearest_claimed_tile

if TYPE_CHECKING:
    from world import World
    from monster import Monster


class Spellbook:
    """Colony-wide spell cooldowns - one shared timer per spell, not
    per-Mage. Lives on World (not Game) so extensions.register_tick, which
    only receives (world, dt), can tick it down."""

    def __init__(self, cooldowns: dict[str, float] | None = None):
        self.cooldowns: dict[str, float] = dict(cooldowns) if cooldowns else {}
        self.flash_position: tuple[float, float] | None = None
        self.flash_timer: float = 0.0
        self.flash_color: tuple[int, int, int] | None = None

    def remaining(self, spell: str) -> float:
        return self.cooldowns.get(spell, 0.0)

    def is_ready(self, spell: str) -> bool:
        return self.remaining(spell) <= 0.0

    def start_cooldown(self, spell: str, seconds: float) -> None:
        self.cooldowns[spell] = seconds

    def trigger_flash(
        self, position: tuple[float, float], duration: float, color: tuple[int, int, int]
    ) -> None:
        self.flash_position = position
        self.flash_timer = duration
        self.flash_color = color

    def tick(self, dt: float) -> None:
        for spell in list(self.cooldowns):
            self.cooldowns[spell] = max(0.0, self.cooldowns[spell] - dt)
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)


def nearest_monster_to_territory(world: "World", monsters: list["Monster"]) -> "Monster | None":
    best, best_dist = None, None
    for monster in monsters:
        tile = tile_at(monster.x, monster.y)
        target = nearest_claimed_tile(world.grid, tile)
        if target is None:
            continue
        dist = abs(tile[0] - target[0]) + abs(tile[1] - target[1])
        if best_dist is None or dist < best_dist:
            best, best_dist = monster, dist
    return best


def _has_living_mage(world: "World") -> bool:
    return any(npc.role == ROLE_MAGE and not npc.is_dead for npc in world.npcs)


def _cast_single_target_spell(
    world: "World",
    monsters: list["Monster"],
    spell: str,
    damage: int,
    cooldown: float,
    color: tuple[int, int, int],
    on_hit: Callable[["Monster"], None] | None = None,
) -> bool:
    """Shared scaffolding for single-target spells: ready-check, living-Mage
    check, nearest-target lookup, damage, cooldown, flash. Castable whenever
    off-cooldown and a living Mage exists, regardless of that Mage's
    position - auto-targets the nearest monster to territory. Silent no-op
    (no wasted cooldown) otherwise. `on_hit` applies any effect beyond flat
    damage (e.g. Fire's burn)."""
    if not world.spellbook.is_ready(spell):
        return False
    if not _has_living_mage(world):
        return False
    target = nearest_monster_to_territory(world, monsters)
    if target is None:
        return False

    target.health -= damage
    if on_hit is not None:
        on_hit(target)
    world.spellbook.start_cooldown(spell, cooldown)
    world.spellbook.trigger_flash((target.x, target.y), MAGIC_FLASH_DURATION, color)
    return True


def cast_lightning(world: "World", monsters: list["Monster"]) -> bool:
    return _cast_single_target_spell(
        world, monsters, "Lightning", LIGHTNING_DAMAGE, LIGHTNING_COOLDOWN, COLOR_LIGHTNING_FLASH
    )


def cast_fire(world: "World", monsters: list["Monster"]) -> bool:
    """Immediate damage plus a burn DoT applied directly on the target
    Monster (ticked in Monster.update itself, not via
    extensions.register_tick: monsters live on Game, not World, so the
    register_tick hook - which only ever receives (world, dt) - has no way
    to reach them)."""
    return _cast_single_target_spell(
        world, monsters, "Fire", FIRE_DAMAGE, FIRE_COOLDOWN, COLOR_FIRE_FLASH,
        on_hit=lambda target: target.apply_burn(FIRE_BURN_DAMAGE_PER_TICK, FIRE_BURN_TICKS),
    )


def _tick_magic(world: "World", dt: float) -> None:
    world.spellbook.tick(dt)


def _magic_hud_line(world: "World") -> str:
    parts = []
    for spell, hotkey in (("Lightning", "W"), ("Fire", "Q")):
        remaining = world.spellbook.remaining(spell)
        status = "ready" if remaining <= 0 else f"{remaining:.0f}s"
        parts.append(f"{spell}: {status} [{hotkey}]")
    return "  ".join(parts)


register_tick(_tick_magic)
register_hud_line(_magic_hud_line)
