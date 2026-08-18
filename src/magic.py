from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from constants import (
    COLOR_FIRE_FLASH,
    COLOR_FREEZE_FLASH,
    COLOR_LIGHTNING_FLASH,
    FIRE_BURN_DAMAGE_PER_TICK,
    FIRE_BURN_TICKS,
    FIRE_COOLDOWN,
    FIRE_DAMAGE,
    FREEZE_COOLDOWN,
    FREEZE_DURATION,
    LIGHTNING_COOLDOWN,
    LIGHTNING_DAMAGE,
    MAGIC_FLASH_DURATION,
    ROLE_MAGE,
)
from coords import tile_at
from extensions import register_hud_line, register_tick
from monster import nearest_claimed_tile
from skills import aoe_radius, magic_damage_multiplier

if TYPE_CHECKING:
    from world import World
    from monster import Monster


class Spellbook:
    """Colony-wide spell cooldowns - one shared timer per spell, not
    per-Mage. Lives on World (not Game) so extensions.register_tick, which
    only receives (world, dt), can tick it down."""

    def __init__(self, cooldowns: dict[str, float] | None = None):
        self.cooldowns: dict[str, float] = dict(cooldowns) if cooldowns else {}
        # A list, not a single slot: Freeze hits every monster in its 3x3 box
        # at once, so one shared flash would only ever show the last one.
        # Each entry: {"position", "timer", "duration", "color"}. Ephemeral
        # render state, deliberately not persisted through save.py.
        self.flashes: list[dict] = []

    def remaining(self, spell: str) -> float:
        return self.cooldowns.get(spell, 0.0)

    def is_ready(self, spell: str) -> bool:
        return self.remaining(spell) <= 0.0

    def start_cooldown(self, spell: str, seconds: float) -> None:
        self.cooldowns[spell] = seconds

    def trigger_flash(
        self, position: tuple[float, float], duration: float, color: tuple[int, int, int]
    ) -> None:
        self.flashes.append({"position": position, "timer": duration, "duration": duration, "color": color})

    def tick(self, dt: float) -> None:
        for spell in list(self.cooldowns):
            self.cooldowns[spell] = max(0.0, self.cooldowns[spell] - dt)
        for flash in self.flashes:
            flash["timer"] = max(0.0, flash["timer"] - dt)
        self.flashes = [f for f in self.flashes if f["timer"] > 0]


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


def _can_cast(world: "World", spell: str) -> bool:
    """Castable whenever off-cooldown and a living Mage exists, regardless
    of that Mage's position - shared by every spell's cast function."""
    return world.spellbook.is_ready(spell) and _has_living_mage(world)


def _cast_single_target_spell(
    world: "World",
    monsters: list["Monster"],
    spell: str,
    damage: int,
    cooldown: float,
    color: tuple[int, int, int],
    on_hit: Callable[["Monster"], None] | None = None,
) -> bool:
    """Shared scaffolding for single-target spells: ready/Mage check,
    nearest-target lookup, damage, cooldown, flash. Auto-targets the nearest
    monster to territory. Silent no-op (no wasted cooldown) if not castable
    or no monster exists. `on_hit` applies any effect beyond flat damage
    (e.g. Fire's burn)."""
    if not _can_cast(world, spell):
        return False
    target = nearest_monster_to_territory(world, monsters)
    if target is None:
        return False

    target.health -= int(damage * magic_damage_multiplier(world))
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
    to reach them). The burn's damage-per-tick is scaled by the same Magic
    Attack multiplier as the direct hit (ticket 23) - without this, Fire's
    total damage (hit + DoT) would gain proportionally less per skill level
    than Lightning/Freeze's single scaled hit, since burn is a real chunk of
    Fire's total output."""
    # round(), not int(): FIRE_BURN_DAMAGE_PER_TICK is small (5) relative to
    # the +15%/level step, so truncating (5.75 -> 5) would silently erase the
    # level-1 bump entirely. The direct-hit damage elsewhere in this module
    # is large enough that int() vs round() doesn't matter in practice.
    burn_damage_per_tick = max(1, round(FIRE_BURN_DAMAGE_PER_TICK * magic_damage_multiplier(world)))
    return _cast_single_target_spell(
        world, monsters, "Fire", FIRE_DAMAGE, FIRE_COOLDOWN, COLOR_FIRE_FLASH,
        on_hit=lambda target: target.apply_burn(burn_damage_per_tick, FIRE_BURN_TICKS),
    )


def cast_freeze(world: "World", monsters: list["Monster"]) -> bool:
    """AoE, not single-target, so this doesn't reuse
    _cast_single_target_spell - targeting selects every monster within a
    3x3 tile box (FREEZE_RADIUS on each axis) around the nearest threat's
    tile, not just that one monster. apply_freeze() on each affected monster
    already refreshes rather than stacks (Monster.apply_freeze overwrites,
    never adds), so re-hitting an already-frozen monster is safe by
    construction."""
    if not _can_cast(world, "Freeze"):
        return False
    center = nearest_monster_to_territory(world, monsters)
    if center is None:
        return False

    cx, cy = tile_at(center.x, center.y)
    radius = aoe_radius(world)  # FREEZE_RADIUS + AoE Attack skill bonus (ticket 23)
    for monster in monsters:
        mx, my = tile_at(monster.x, monster.y)
        if abs(mx - cx) <= radius and abs(my - cy) <= radius:
            monster.apply_freeze(FREEZE_DURATION)
            world.spellbook.trigger_flash((monster.x, monster.y), MAGIC_FLASH_DURATION, COLOR_FREEZE_FLASH)

    world.spellbook.start_cooldown("Freeze", FREEZE_COOLDOWN)
    return True


def _tick_magic(world: "World", dt: float) -> None:
    world.spellbook.tick(dt)


def _magic_hud_line(world: "World") -> str:
    parts = []
    for spell, hotkey in (("Fire", "F1"), ("Lightning", "F2"), ("Freeze", "F3")):
        remaining = world.spellbook.remaining(spell)
        status = "ready" if remaining <= 0 else f"{remaining:.0f}s"
        parts.append(f"{spell}: {status} [{hotkey}]")
    return "  ".join(parts)


register_tick(_tick_magic)
register_hud_line(_magic_hud_line)
