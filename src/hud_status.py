"""HUD panels for inventory totals and per-NPC task status (ticket 10).
Registers as hud_lines() providers via extensions.py - game.py already
splices those into the HUD, no changes needed there."""

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


def _npc_tasks_line(world: "World") -> str:
    if not world.npcs:
        return "NPCs: (none)"
    parts = ", ".join(
        f"NPC{i}: {npc.task.type if npc.task else 'idle'}" for i, npc in enumerate(world.npcs, start=1)
    )
    return f"NPCs: {parts}"


register_hud_line(_inventory_line)
register_hud_line(_npc_tasks_line)
