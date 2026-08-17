from world import World
from npc import NPC
import hud_display

def test_inventory_hud_line_empty():
    world = World(npc_count=0)
    assert hud_display._inventory_hud_line(world) == "Inventory: empty"

def test_inventory_hud_line_with_items():
    world = World(npc_count=0)
    world.inventory.add("wood", 5)
    world.inventory.add("crop", 3)
    # Sorted alphabetically
    assert hud_display._inventory_hud_line(world) == "Inventory: crop x3, wood x5"

def test_npc_tasks_hud_line_no_npcs():
    world = World(npc_count=0)
    assert hud_display._npc_tasks_hud_line(world) == "NPCs: none"

def test_npc_tasks_hud_line_with_tasks():
    world = World(npc_count=0)
    npc1 = NPC(0, 0, id=0)
    npc2 = NPC(0, 0, id=1)

    # npc1 is idle

    # npc2 has a task
    task = world.tasks.add("Gather", (0, 0))
    npc2.task = task

    world.npcs.extend([npc1, npc2])

    assert hud_display._npc_tasks_hud_line(world) == "NPC 0: idle | NPC 1: Gather"


def test_npc_tasks_hud_line_label_stays_with_npc_after_list_splice():
    # world.npcs can be spliced in place (combat.py removes dead NPCs), so
    # the label must track npc.id, not list position.
    world = World(npc_count=0)
    npc0 = NPC(0, 0, id=0)
    npc1 = NPC(0, 0, id=1)
    world.npcs.extend([npc0, npc1])

    world.npcs[:] = [npc1]  # npc0 "died" and was spliced out

    assert hud_display._npc_tasks_hud_line(world) == "NPC 1: idle"
