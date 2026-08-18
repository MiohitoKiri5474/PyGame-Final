"""Food spoilage system (ticket 27).

- Ticks spoilage ledger on Inventory.
- Discards expired food batches.
- Displays HUD alert when food spoils.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from extensions import register_hud_line, register_tick

if TYPE_CHECKING:
    from world import World


def _tick_spoilage(world: "World", dt: float) -> None:
    if not hasattr(world, "inventory"):
        return

    if hasattr(world, "spoilage_alert_timer") and world.spoilage_alert_timer > 0:
        world.spoilage_alert_timer = max(0.0, world.spoilage_alert_timer - dt)

    spoiled = world.inventory.tick_spoilage(dt)
    if spoiled:
        items_str = ", ".join(f"{amt} {res}" for res, amt in spoiled.items())
        world.spoilage_alert = f"Food spoiled: {items_str}"
        world.spoilage_alert_timer = 5.0


def _spoilage_hud_line(world: "World") -> str:
    if getattr(world, "spoilage_alert_timer", 0.0) > 0:
        return getattr(world, "spoilage_alert", "")
    return ""



register_tick(_tick_spoilage)
register_hud_line(_spoilage_hud_line)
