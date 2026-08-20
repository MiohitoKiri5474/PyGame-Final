"""Lightweight onboarding guidance: a single HUD line suggesting the next
thing to try, computed fresh from world state every frame - no progress
tracking, no new game system, nothing persisted. Starts with early-game
milestones, moves on to slightly later ones once those are met, and ends
on an always-true evergreen reminder so the hint box has something to say
for the whole game rather than going blank once the basics are done.

Registers as a hud_lines() provider via extensions.py - game.py already
splices those into the HUD, no changes needed there."""

from __future__ import annotations

from typing import TYPE_CHECKING

from extensions import register_hud_line

if TYPE_CHECKING:
    from world import World

_DEFENSE_BUILDING_TYPES = ("Wall", "Tower")

# Kept short on purpose: the hint box is a narrow ~130px column, and at the
# HUD's actual font/size most sentences over ~45 characters wrap past the
# box's row cap and get cut off with a trailing "..." mid-sentence.
_EVERGREEN_TIP = "Tip: watch the countdown - monsters spawn at night."


def _has_defense_building(world: "World") -> bool:
    return any(b.type in _DEFENSE_BUILDING_TYPES for b in world.buildings)


def _onboarding_hint(world: "World") -> str:
    # The starting map always ships with some pre-claimed land around spawn
    # (Grid claims START_CLAIM_RADIUS on creation), so gathering - not
    # expanding - is genuinely the first reachable milestone.
    if not world.inventory.items():
        return "Tip: select Gather, then click a resource tile."
    if not world.buildings:
        return "Tip: build a Wall or Tower before night falls."
    if not _has_defense_building(world):
        return "Tip: a Wall or Tower defends NPCs at night."
    if not any(b.type == "Farmland" for b in world.buildings):
        return "Tip: build a Farmland for steady crops."
    if not any(getattr(a, "is_tamed", False) for a in world.animals):
        return "Tip: Tame a wild animal for meat or a companion."
    if all(npc.priority is None for npc in world.npcs):
        return "Tip: press [P] to set each NPC's task priority."
    if sum(world.skills.values()) == 0:
        return "Tip: press [K] to spend skill points."
    return _EVERGREEN_TIP


register_hud_line(_onboarding_hint)
