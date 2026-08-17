from __future__ import annotations

from typing import TYPE_CHECKING

from constants import LIGHTNING_COOLDOWN, LIGHTNING_DAMAGE, MAGIC_FLASH_DURATION, ROLE_MAGE
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

    def remaining(self, spell: str) -> float:
        return self.cooldowns.get(spell, 0.0)

    def is_ready(self, spell: str) -> bool:
        return self.remaining(spell) <= 0.0

    def start_cooldown(self, spell: str, seconds: float) -> None:
        self.cooldowns[spell] = seconds

    def trigger_flash(self, position: tuple[float, float], duration: float) -> None:
        self.flash_position = position
        self.flash_timer = duration

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


def cast_lightning(world: "World", monsters: list["Monster"]) -> bool:
    """Colony-wide cast: castable whenever off-cooldown and a living Mage
    exists, regardless of that Mage's position - auto-targets the nearest
    monster to territory. Silent no-op (no wasted cooldown) otherwise."""
    if not world.spellbook.is_ready("Lightning"):
        return False
    if not _has_living_mage(world):
        return False
    target = nearest_monster_to_territory(world, monsters)
    if target is None:
        return False

    target.health -= LIGHTNING_DAMAGE
    world.spellbook.start_cooldown("Lightning", LIGHTNING_COOLDOWN)
    world.spellbook.trigger_flash((target.x, target.y), MAGIC_FLASH_DURATION)
    return True


def _tick_magic(world: "World", dt: float) -> None:
    world.spellbook.tick(dt)


def _magic_hud_line(world: "World") -> str:
    remaining = world.spellbook.remaining("Lightning")
    if remaining <= 0:
        return "Lightning: ready [W]"
    return f"Lightning: {remaining:.0f}s [W]"


register_tick(_tick_magic)
register_hud_line(_magic_hud_line)
