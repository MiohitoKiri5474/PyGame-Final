"""Lightweight onboarding guidance: a single HUD line suggesting the next
thing to try, computed fresh from world state every frame - no progress
tracking, no new game system, nothing persisted. Stops suggesting once the
player has clearly gotten past the basics (defenses up).

Registers as a hud_lines() provider via extensions.py - game.py already
splices those into the HUD, no changes needed there."""

from __future__ import annotations

from typing import TYPE_CHECKING

from extensions import register_hud_line

if TYPE_CHECKING:
    from world import World

_DEFENSE_BUILDING_TYPES = ("Wall", "Tower")


def _has_defense_building(world: "World") -> bool:
    return any(b.type in _DEFENSE_BUILDING_TYPES for b in world.buildings)


def _onboarding_hint(world: "World") -> str:
    # The starting map always ships with some pre-claimed land around spawn
    # (Grid claims START_CLAIM_RADIUS on creation), so gathering - not
    # expanding - is genuinely the first reachable milestone.
    if not world.inventory.items():
        return "Tip: select Gather and click a resource tile to start stockpiling materials."
    if not world.buildings:
        return "Tip: select a Build task to raise a Wall or Tower before night falls."
    if not _has_defense_building(world):
        return "Tip: monsters attack at night - a Wall or Tower helps your NPCs hold the line."
    return ""


register_hud_line(_onboarding_hint)
