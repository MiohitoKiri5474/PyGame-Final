"""Unit tests for NPC hunger & starvation (ticket 08).

These are pure-Python tests — no pygame import required.
Run with:  python -m pytest tests/test_npc.py -v
"""

import sys
import os

# Allow imports from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from npc import NPC
from constants import NPC_MAX_HUNGER, NPC_MAX_HEALTH, HUNGER_DECAY_RATE


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _fresh_npc() -> NPC:
    """Return a new NPC at the origin with full stats.
    Resets the class-level id counter so tests are independent."""
    NPC._next_id = 0
    return NPC(0.0, 0.0)


# ------------------------------------------------------------------
# Hunger decay
# ------------------------------------------------------------------

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
# Starvation death
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

    def test_unique_ids(self):
        NPC._next_id = 0
        a = NPC(0, 0)
        b = NPC(0, 0)
        assert a.id != b.id


# Required for pytest.approx — import at top level
import pytest
