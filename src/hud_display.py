from __future__ import annotations
from typing import TYPE_CHECKING
from extensions import register_hud_line

if TYPE_CHECKING:
    from world import World

def _inventory_hud_line(world: "World") -> str:
    items = sorted(world.inventory.items())
    if not items:
        return "Inventory: empty"
    
    parts = [f"{res} x{count}" for res, count in items]
    return f"Inventory: {', '.join(parts)}"

def _npc_tasks_hud_line(world: "World") -> str:
    if not world.npcs:
        return "NPCs: none"
        
    parts = []
    for npc in world.npcs:
        task_name = npc.task.type if npc.task else "idle"
        parts.append(f"NPC {npc.id}: {task_name}")

    return " | ".join(parts)

register_hud_line(_inventory_hud_line)
register_hud_line(_npc_tasks_hud_line)
