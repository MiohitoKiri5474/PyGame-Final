"""Magic system: spellbook cooldown management, targeting, and spell casting.

Pygame-free module — all rendering is in render_magic.py.

Spells:
  - Lightning (F2): instant burst damage, single target, 20s cooldown
  - Fire (F1): instant damage + 3s burn DoT, single target, 15s cooldown
  - Freeze (F3): AoE 3×3, freezes monsters for 4s, 25s cooldown
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from constants import (
    LIGHTNING_DAMAGE,
    LIGHTNING_COOLDOWN,
    FIRE_DAMAGE,
    FIRE_COOLDOWN,
    FIRE_BURN_DPS,
    FIRE_BURN_DURATION,
    FREEZE_COOLDOWN,
    FREEZE_DURATION,
    FREEZE_RADIUS,
    TILE_SIZE,
    ROLE_MAGE,
)
from coords import tile_at

if TYPE_CHECKING:
    from monster import Monster
    from world import World


class Spellbook:
    """Tracks cooldown timers for all spells."""

    def __init__(self):
        self.cooldowns: dict[str, float] = {}

    def tick(self, dt: float) -> None:
        for name in list(self.cooldowns):
            self.cooldowns[name] = max(0.0, self.cooldowns[name] - dt)
            if self.cooldowns[name] <= 0.0:
                del self.cooldowns[name]

    def is_ready(self, spell_name: str) -> bool:
        return self.cooldowns.get(spell_name, 0.0) <= 0.0

    def start_cooldown(self, spell_name: str, duration: float) -> None:
        self.cooldowns[spell_name] = duration

    def remaining(self, spell_name: str) -> float:
        return self.cooldowns.get(spell_name, 0.0)


def has_living_mage(npcs: list) -> bool:
    """Return True if at least one alive Mage exists in the colony."""
    return any(npc.role == ROLE_MAGE and not npc.is_dead for npc in npcs)


def nearest_monster_to_territory(world: "World", monsters: list["Monster"]) -> "Monster | None":
    """Return the monster closest (Manhattan distance) to any claimed tile."""
    if not monsters:
        return None

    # Build a set of claimed tile coords for fast lookup
    claimed = []
    grid = world.grid
    for y in range(grid.height):
        for x in range(grid.width):
            if grid.get(x, y).claimed:
                claimed.append((x, y))

    if not claimed:
        return None

    best_monster = None
    best_dist = float("inf")

    for monster in monsters:
        if monster.is_dead:
            continue
        mx, my = tile_at(monster.x, monster.y)
        for cx, cy in claimed:
            dist = abs(mx - cx) + abs(my - cy)
            if dist < best_dist:
                best_dist = dist
                best_monster = monster

    return best_monster


# ── Lightning ──────────────────────────────────────────────────

def cast_lightning(
    spellbook: Spellbook, world: "World", monsters: list["Monster"]
) -> "Monster | None":
    """Cast Lightning on the nearest monster to territory.
    Returns the target monster if cast succeeded, None otherwise."""
    if not has_living_mage(world.npcs):
        return None
    if not spellbook.is_ready("lightning"):
        return None

    target = nearest_monster_to_territory(world, monsters)
    if target is None:
        return None

    target.health -= LIGHTNING_DAMAGE
    spellbook.start_cooldown("lightning", LIGHTNING_COOLDOWN)
    return target


# ── Fire ───────────────────────────────────────────────────────

def cast_fire(
    spellbook: Spellbook, world: "World", monsters: list["Monster"]
) -> "Monster | None":
    """Cast Fire: instant damage + burn DoT on the nearest monster.
    Returns the target if cast succeeded, None otherwise."""
    if not has_living_mage(world.npcs):
        return None
    if not spellbook.is_ready("fire"):
        return None

    target = nearest_monster_to_territory(world, monsters)
    if target is None:
        return None

    target.health -= FIRE_DAMAGE
    target.burn_remaining = FIRE_BURN_DURATION
    target.burn_dps = FIRE_BURN_DPS
    spellbook.start_cooldown("fire", FIRE_COOLDOWN)
    return target


# ── Freeze ─────────────────────────────────────────────────────

def cast_freeze(
    spellbook: Spellbook, world: "World", monsters: list["Monster"]
) -> list["Monster"]:
    """Cast Freeze: AoE 3×3 around the nearest monster to territory.
    Freezes all monsters in range for FREEZE_DURATION seconds.
    Returns list of affected monsters (empty if cast failed)."""
    if not has_living_mage(world.npcs):
        return []
    if not spellbook.is_ready("freeze"):
        return []

    target = nearest_monster_to_territory(world, monsters)
    if target is None:
        return []

    center_tx, center_ty = tile_at(target.x, target.y)
    affected = []

    for monster in monsters:
        if monster.is_dead:
            continue
        mx, my = tile_at(monster.x, monster.y)
        if abs(mx - center_tx) <= FREEZE_RADIUS and abs(my - center_ty) <= FREEZE_RADIUS:
            # Refresh, don't stack
            monster.frozen_timer = FREEZE_DURATION
            affected.append(monster)

    spellbook.start_cooldown("freeze", FREEZE_COOLDOWN)
    return affected
