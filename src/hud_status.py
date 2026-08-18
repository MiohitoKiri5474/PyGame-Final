"""HUD panel for inventory totals (ticket 10). Registers as a hud_lines()
provider via extensions.py - game.py already splices those into the HUD,
no changes needed there.

Per-NPC task status used to live here too as a line that grew with the
roster - moved to npc_status_ui.py's on-demand panel (N key) instead."""

from __future__ import annotations

from typing import TYPE_CHECKING

from extensions import register_hud_line

if TYPE_CHECKING:
    from world import World


def _inventory_line(world: "World") -> str:
    items = world.inventory.items()
    if not items:
        return "Inventory: (empty)"
    parts = ", ".join(f"{resource} {count}" for resource, count in sorted(items.items()))
    return f"Inventory: {parts}"


register_hud_line(_inventory_line)
