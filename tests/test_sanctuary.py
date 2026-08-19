import pygame
from combat import resolve_combat
from constants import (
    HUNGER_DECAY_RATE,
    NPC_MAX_HEALTH,
    NPC_MAX_HUNGER,
    ROLE_FARMER,
    ROLE_KNIGHT,
    ROLE_MAGE,
    SANCTUARY_HEAL_RATE,
)
from monster import Monster
from npc import NPC
from sanctuary_ui import SanctuaryUI
from task import update_npc_tasks
from world import World


def test_resting_npc_regenerates_health_over_time():
    npc = NPC(16.0, 16.0, role=ROLE_KNIGHT)
    npc.health = 40.0
    npc.is_resting = True

    dt = 2.0
    npc.update(dt)

    expected_health = 40.0 + SANCTUARY_HEAL_RATE * dt
    assert abs(npc.health - expected_health) < 1e-3
    assert npc.is_resting is True


def test_resting_npc_health_capped_at_max_health():
    npc = NPC(16.0, 16.0, role=ROLE_MAGE)
    npc.health = npc.max_health - 2.0
    npc.is_resting = True

    npc.update(1.0)
    assert npc.health == npc.max_health


def test_resting_npc_hunger_continues_to_decay():
    npc = NPC(16.0, 16.0, role=ROLE_FARMER)
    npc.hunger = 80.0
    npc.is_resting = True

    dt = 5.0
    npc.update(dt)

    expected_hunger = 80.0 - HUNGER_DECAY_RATE * dt
    assert abs(npc.hunger - expected_hunger) < 1e-3


def test_resting_npc_starvation_kills_at_zero_hunger():
    npc = NPC(16.0, 16.0, role=ROLE_KNIGHT)
    npc.hunger = 0.1
    npc.is_resting = True

    npc.update(1.0)
    assert npc.is_dead is True
    assert npc.alive is False


def test_resting_npc_excluded_from_combat():
    npc = NPC(16.0, 16.0, role=ROLE_KNIGHT)
    npc.health = 50.0
    npc.is_resting = True

    monster = Monster(16.0, 16.0, type="Goblin")
    monster_hp_start = monster.health

    resolve_combat([npc], [monster], [])

    # Neither NPC nor Monster should take combat damage since NPC is resting in sanctuary
    assert npc.health == 50.0
    assert monster.health == monster_hp_start


def test_resting_npc_eats_from_colony_inventory_when_hungry():
    world = World(npc_count=1)
    npc = world.npcs[0]
    npc.hunger = 20.0
    npc.is_resting = True
    world.inventory.add("crop", 5)

    update_npc_tasks(world, 0.1)

    assert npc.hunger > 20.0
    assert world.inventory.get("crop") == 4


def test_sanctuary_ui_deploy_click():
    pygame.init()
    ui = SanctuaryUI()
    world = World(npc_count=2)
    world.npcs[0].is_resting = True

    # Click on the deploy button of the first slot
    slot_y = ui.PANEL_Y + 42
    btn_x = ui.PANEL_X + ui.PANEL_WIDTH - 50
    btn_y = slot_y + 50

    clicked_npc = ui.handle_click((btn_x, btn_y), world)
    assert clicked_npc is world.npcs[0]

    # Click outside sanctuary
    assert ui.handle_click((10, 10), world) is None
