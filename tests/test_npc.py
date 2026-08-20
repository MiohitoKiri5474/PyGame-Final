import sys
import os
import pytest

# Allow imports from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from coords import tile_center
from npc import NPC
from constants import (
    NPC_MAX_HUNGER,
    NPC_MAX_HEALTH,
    NPC_ATTACK,
    NPC_DEFENSE,
    COMBAT_RANGE,
    HUNGER_DECAY_RATE,
    HUNGER_EAT_THRESHOLD,
    HUNGER_RESTORE_PER_CROP,
    ROLE_FARMER,
    ROLE_KNIGHT,
    ROLE_MAGE,
    ROLE_STATS,
    MAGE_COMBAT_RANGE,
)
from world import World
from task import update_npc_tasks


# ------------------------------------------------------------------
# Pathfinding & Movement (tickets 01 & 02)
# ------------------------------------------------------------------

def test_new_npc_has_no_path_and_has_arrived():
    npc = NPC(x=10.0, y=10.0)
    assert npc.has_arrived
    assert npc.path == []


def test_set_path_clears_arrived_state():
    npc = NPC(x=0.0, y=0.0)
    npc.set_path([(0, 0), (1, 0)])
    assert not npc.has_arrived


def test_update_moves_toward_next_waypoint():
    start_x, start_y = tile_center(0, 0)
    npc = NPC(x=start_x, y=start_y, speed=100.0)
    npc.set_path([(2, 0)])
    npc.update(0.1)
    assert npc.x > start_x
    assert npc.y == start_y


def test_update_reaches_and_pops_waypoint_exactly_at_target():
    target = tile_center(1, 0)
    npc = NPC(x=target[0] - 5, y=target[1], speed=100.0)
    npc.set_path([(1, 0)])
    npc.update(1.0)  # far more than enough distance to cover 5px at speed 100
    assert npc.has_arrived
    assert (npc.x, npc.y) == target


def test_update_walks_full_path_to_completion():
    npc = NPC(x=0.0, y=0.0, speed=1000.0)  # fast enough to finish in a few ticks
    npc.set_path([(0, 0), (1, 0), (2, 0)])
    for _ in range(50):
        if npc.has_arrived:
            break
        npc.update(1 / 60)
    assert npc.has_arrived
    assert (npc.x, npc.y) == tile_center(2, 0)


def test_update_does_nothing_when_no_path():
    npc = NPC(x=5.0, y=5.0)
    npc.update(1.0)
    assert (npc.x, npc.y) == (5.0, 5.0)


def test_path_targeting_current_tile_arrives_on_first_update():
    x, y = tile_center(3, 4)
    npc = NPC(x=x, y=y)
    npc.set_path([(3, 4)])
    assert not npc.has_arrived
    npc.update(1 / 60)
    assert npc.has_arrived
    assert (npc.x, npc.y) == (x, y)


def test_new_npc_has_no_task_and_default_priority():
    npc = NPC(x=0.0, y=0.0)
    assert npc.task is None
    assert npc.task_progress == 0.0
    assert npc.priority is None


# ------------------------------------------------------------------
# Hunger decay (ticket 08)
# ------------------------------------------------------------------

def _fresh_npc() -> NPC:
    """Return a new NPC at the origin with full stats.
    Resets the class-level id counter so tests are independent."""
    NPC._next_id = 0
    return NPC(0.0, 0.0)


class TestHungerDecay:
    """Hunger decreases over time at the expected rate."""

    def test_hunger_decreases_after_one_tick(self):
        npc = _fresh_npc()
        dt = 1.0  # 1 second
        npc.update(dt)
        expected = NPC_MAX_HUNGER - HUNGER_DECAY_RATE * dt
        assert npc.hunger == pytest.approx(expected, abs=1e-9)

    def test_hunger_decreases_over_multiple_ticks(self):
        npc = _fresh_npc()
        ticks = 10
        dt = 0.5
        for _ in range(ticks):
            npc.update(dt)
        elapsed = ticks * dt  # 5 seconds
        expected = NPC_MAX_HUNGER - HUNGER_DECAY_RATE * elapsed
        assert npc.hunger == pytest.approx(expected, abs=1e-6)

    def test_hunger_does_not_go_negative(self):
        npc = _fresh_npc()
        # Simulate way past full drain
        npc.update(9999.0)
        assert npc.hunger == 0.0


# ------------------------------------------------------------------
# Starvation death (ticket 08)
# ------------------------------------------------------------------

class TestStarvationDeath:
    """NPC is killed when hunger reaches 0."""

    def test_npc_dies_when_hunger_reaches_zero(self):
        npc = _fresh_npc()
        # Exactly enough time to drain hunger to 0
        drain_time = NPC_MAX_HUNGER / HUNGER_DECAY_RATE
        npc.update(drain_time)
        assert npc.hunger == 0.0
        assert npc.alive is False

    def test_npc_alive_while_hunger_above_zero(self):
        npc = _fresh_npc()
        # Drain most but not all hunger
        npc.update(1.0)
        assert npc.hunger > 0.0
        assert npc.alive is True

    def test_npc_dies_gradually_over_many_ticks(self):
        npc = _fresh_npc()
        dt = 1.0 / 60  # 60 fps tick
        drain_time = NPC_MAX_HUNGER / HUNGER_DECAY_RATE
        total_ticks = int(drain_time / dt) + 120  # go well past drain
        for _ in range(total_ticks):
            npc.update(dt)
        assert npc.hunger == 0.0
        assert npc.alive is False


# ------------------------------------------------------------------
# Eating & Food Consumption
# ------------------------------------------------------------------

class TestNPCEat:
    """NPC eats food to restore hunger."""

    def test_eat_restores_hunger_up_to_max(self):
        npc = _fresh_npc()
        npc.hunger = 40.0
        npc.eat(HUNGER_RESTORE_PER_CROP)
        assert npc.hunger == 90.0

        # Capped at max hunger
        npc.eat(HUNGER_RESTORE_PER_CROP)
        assert npc.hunger == NPC_MAX_HUNGER

    def test_dead_npc_cannot_eat(self):
        npc = _fresh_npc()
        npc.kill()
        npc.eat(50.0)
        assert npc.hunger == NPC_MAX_HUNGER  # untouched


class TestColonyFoodConsumption:
    """Hungry NPCs automatically consume food from the colony inventory."""

    def test_hungry_npc_eats_from_inventory(self):
        world = World(npc_count=0)
        npc = _fresh_npc()
        npc.hunger = HUNGER_EAT_THRESHOLD - 5.0  # hungry
        world.npcs.append(npc)
        world.inventory.add("crop", 2)

        update_npc_tasks(world, 0.1)

        assert world.inventory.get("crop") == 1
        assert npc.hunger > HUNGER_EAT_THRESHOLD

    def test_not_hungry_npc_does_not_eat(self):
        world = World(npc_count=0)
        npc = _fresh_npc()
        npc.hunger = HUNGER_EAT_THRESHOLD + 20.0
        world.npcs.append(npc)
        world.inventory.add("crop", 2)

        update_npc_tasks(world, 0.1)

        assert world.inventory.get("crop") == 2
        assert npc.hunger <= HUNGER_EAT_THRESHOLD + 20.0

    def test_hungry_npc_without_food_keeps_decaying(self):
        world = World(npc_count=0)
        npc = _fresh_npc()
        npc.hunger = HUNGER_EAT_THRESHOLD - 5.0
        world.npcs.append(npc)
        # inventory has 0 crops

        update_npc_tasks(world, 1.0)

        assert world.inventory.get("crop") == 0
        assert npc.hunger < HUNGER_EAT_THRESHOLD - 5.0


# ------------------------------------------------------------------
# Shared death path (kill)
# ------------------------------------------------------------------

class TestKillMethod:
    """kill() marks NPC as dead — shared by starvation and future combat."""

    def test_kill_sets_alive_false(self):
        npc = _fresh_npc()
        assert npc.alive is True
        npc.kill()
        assert npc.alive is False

    def test_dead_npc_stops_updating(self):
        npc = _fresh_npc()
        npc.kill()
        hunger_at_death = npc.hunger
        npc.update(10.0)
        # Hunger should not change after death
        assert npc.hunger == hunger_at_death

    def test_health_preserved_on_starvation(self):
        """Starvation death doesn't touch the health bar."""
        npc = _fresh_npc()
        npc.update(9999.0)  # starve
        assert npc.alive is False
        assert npc.health == NPC_MAX_HEALTH


# ------------------------------------------------------------------
# Initial state
# ------------------------------------------------------------------

class TestNPCInit:
    """NPC starts with correct default values."""

    def test_initial_hunger_full(self):
        npc = _fresh_npc()
        assert npc.hunger == NPC_MAX_HUNGER

    def test_initial_health_full(self):
        npc = _fresh_npc()
        assert npc.health == NPC_MAX_HEALTH

    def test_initial_alive(self):
        npc = _fresh_npc()
        assert npc.alive is True

    def test_base_speed_matches_initial_speed(self):
        # base_speed must be set explicitly here, not lazily re-derived
        # later from a possibly-already-buffed npc.speed (that was the
        # source of a save/load speed-compounding bug).
        npc = NPC(0.0, 0.0, speed=123.0)
        assert npc.base_speed == 123.0
        assert npc.speed == 123.0

    def test_unique_ids(self):
        NPC._next_id = 0
        a = NPC(0, 0)
        b = NPC(0, 0)
        assert a.id != b.id


# ------------------------------------------------------------------
# Role System (ticket 12)
# ------------------------------------------------------------------

class TestRoleStats:
    """NPC stats come from its role, or flat defaults when role is None."""

    def test_no_role_uses_flat_defaults(self):
        npc = NPC(0.0, 0.0)
        assert npc.role is None
        assert npc.attack == NPC_ATTACK
        assert npc.defense == NPC_DEFENSE
        assert npc.max_health == NPC_MAX_HEALTH
        assert npc.health == NPC_MAX_HEALTH
        assert npc.combat_range == COMBAT_RANGE
        assert npc.work_multiplier == 1.0

    def test_farmer_stats_and_work_multiplier(self):
        npc = NPC(0.0, 0.0, role=ROLE_FARMER)
        stats = ROLE_STATS[ROLE_FARMER]
        assert npc.attack == stats["attack"]
        assert npc.defense == stats["defense"]
        assert npc.max_health == stats["max_health"]
        assert npc.health == stats["max_health"]
        assert npc.work_multiplier == 0.6

    def test_knight_stats(self):
        npc = NPC(0.0, 0.0, role=ROLE_KNIGHT)
        stats = ROLE_STATS[ROLE_KNIGHT]
        assert npc.attack == stats["attack"]
        assert npc.defense == stats["defense"]
        assert npc.max_health == stats["max_health"]
        assert npc.work_multiplier == 1.0

    def test_mage_has_ranged_combat_range(self):
        npc = NPC(0.0, 0.0, role=ROLE_MAGE)
        assert npc.combat_range == MAGE_COMBAT_RANGE
        assert npc.combat_range > COMBAT_RANGE
