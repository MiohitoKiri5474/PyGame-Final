import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from constants import (
    LIGHTNING_DAMAGE,
    LIGHTNING_COOLDOWN,
    FIRE_DAMAGE,
    FIRE_COOLDOWN,
    FIRE_BURN_DPS,
    FIRE_BURN_DURATION,
    FREEZE_COOLDOWN,
    FREEZE_DURATION,
    ROLE_MAGE,
    ROLE_FARMER,
    ROLE_KNIGHT,
)
from coords import tile_center
from magic import (
    Spellbook,
    has_living_mage,
    nearest_monster_to_territory,
    cast_lightning,
    cast_fire,
    cast_freeze,
)
from monster import Monster
from npc import NPC
from world import World


def _make_world_with_mage() -> World:
    world = World(npc_count=0)
    # Claim center tile (10, 10)
    world.grid.get(10, 10).claimed = True
    world.grid.get(10, 10).revealed = True
    # Add living Mage
    mage = NPC(*tile_center(10, 10), role=ROLE_MAGE)
    world.npcs.append(mage)
    return world


class TestSpellbook:
    def test_spellbook_initial_state(self):
        sb = Spellbook()
        assert sb.is_ready("lightning")
        assert sb.is_ready("fire")
        assert sb.is_ready("freeze")
        assert sb.remaining("lightning") == 0.0

    def test_cooldown_ticks_down(self):
        sb = Spellbook()
        sb.start_cooldown("lightning", 10.0)
        assert not sb.is_ready("lightning")
        assert sb.remaining("lightning") == 10.0

        sb.tick(4.0)
        assert sb.remaining("lightning") == pytest.approx(6.0)
        assert not sb.is_ready("lightning")

        sb.tick(6.0)
        assert sb.is_ready("lightning")
        assert sb.remaining("lightning") == 0.0


class TestMageRequirement:
    def test_has_living_mage_true_when_alive_mage_present(self):
        world = _make_world_with_mage()
        assert has_living_mage(world.npcs)

    def test_has_living_mage_false_when_only_farmer(self):
        world = World(npc_count=0)
        world.npcs.append(NPC(0, 0, role=ROLE_FARMER))
        assert not has_living_mage(world.npcs)

    def test_has_living_mage_false_when_mage_is_dead(self):
        world = _make_world_with_mage()
        world.npcs[0].kill()
        assert not has_living_mage(world.npcs)


class TestTargeting:
    def test_nearest_monster_to_territory_picks_closest(self):
        world = World(npc_count=0)
        world.grid.get(10, 10).claimed = True

        m_close = Monster(*tile_center(12, 10))  # dist 2
        m_far = Monster(*tile_center(20, 20))    # dist 20

        target = nearest_monster_to_territory(world, [m_far, m_close])
        assert target is m_close

    def test_nearest_monster_skips_dead_monsters(self):
        world = World(npc_count=0)
        world.grid.get(10, 10).claimed = True

        m_dead = Monster(*tile_center(11, 10))
        m_dead.health = 0
        m_alive = Monster(*tile_center(15, 10))

        target = nearest_monster_to_territory(world, [m_dead, m_alive])
        assert target is m_alive


class TestLightningSpell:
    def test_cast_lightning_damages_nearest_monster_and_starts_cooldown(self):
        world = _make_world_with_mage()
        monster = Monster(*tile_center(12, 10))
        initial_hp = monster.health

        target = cast_lightning(world.spellbook, world, [monster])
        assert target is monster
        assert monster.health == initial_hp - LIGHTNING_DAMAGE
        assert not world.spellbook.is_ready("lightning")
        assert world.spellbook.remaining("lightning") == pytest.approx(LIGHTNING_COOLDOWN)

    def test_cast_lightning_noop_on_cooldown(self):
        world = _make_world_with_mage()
        world.spellbook.start_cooldown("lightning", 5.0)
        monster = Monster(*tile_center(12, 10))

        target = cast_lightning(world.spellbook, world, [monster])
        assert target is None
        assert monster.health == monster.max_health

    def test_cast_lightning_noop_without_mage(self):
        world = World(npc_count=0)
        world.npcs.append(NPC(0, 0, role=ROLE_KNIGHT))
        monster = Monster(*tile_center(12, 10))

        target = cast_lightning(world.spellbook, world, [monster])
        assert target is None


class TestFireSpell:
    def test_cast_fire_applies_instant_damage_and_burn_dot(self):
        world = _make_world_with_mage()
        monster = Monster(*tile_center(12, 10))
        initial_hp = monster.health

        target = cast_fire(world.spellbook, world, [monster])
        assert target is monster
        assert monster.health == initial_hp - FIRE_DAMAGE
        assert monster.burn_remaining == pytest.approx(FIRE_BURN_DURATION)
        assert monster.burn_dps == pytest.approx(FIRE_BURN_DPS)
        assert not world.spellbook.is_ready("fire")

    def test_burn_dot_ticks_and_expires(self):
        monster = Monster(0, 0)
        monster.health = 50
        monster.burn_remaining = 3.0
        monster.burn_dps = 5.0

        monster.update(1.0)
        assert monster.health == pytest.approx(45.0)
        assert monster.burn_remaining == pytest.approx(2.0)

        monster.update(2.0)
        assert monster.health == pytest.approx(35.0)
        assert monster.burn_remaining == 0.0

        # No more burn damage after expiry
        monster.update(1.0)
        assert monster.health == pytest.approx(35.0)

    def test_monster_death_mid_burn(self):
        monster = Monster(0, 0)
        monster.health = 2
        monster.burn_remaining = 3.0
        monster.burn_dps = 5.0

        monster.update(1.0)
        assert monster.is_dead


class TestFreezeSpell:
    def test_cast_freeze_aoe_freezes_in_range_and_excludes_outside(self):
        world = _make_world_with_mage()
        # Center target at (12, 10)
        m_center = Monster(*tile_center(12, 10))
        m_adjacent = Monster(*tile_center(13, 11))  # In 3x3
        m_outside = Monster(*tile_center(15, 10))   # Outside 3x3

        affected = cast_freeze(world.spellbook, world, [m_outside, m_adjacent, m_center])
        assert m_center in affected
        assert m_adjacent in affected
        assert m_outside not in affected
        assert m_center.frozen_timer == pytest.approx(FREEZE_DURATION)
        assert m_adjacent.frozen_timer == pytest.approx(FREEZE_DURATION)
        assert m_outside.frozen_timer == 0.0
        assert not world.spellbook.is_ready("freeze")

    def test_frozen_monster_skips_movement(self):
        monster = Monster(0.0, 0.0, speed=100.0)
        monster.set_path([(5, 0)])
        monster.frozen_timer = 2.0

        monster.update(1.0)
        assert (monster.x, monster.y) == (0.0, 0.0)  # Did not move!
        assert monster.frozen_timer == pytest.approx(1.0)

        # Update remaining freeze + extra time
        monster.update(1.0)
        assert monster.frozen_timer == 0.0

        # Now moves
        monster.update(0.1)
        assert monster.x > 0.0

    def test_freeze_refreshes_on_rehit(self):
        world = _make_world_with_mage()
        monster = Monster(*tile_center(12, 10))
        monster.frozen_timer = 1.0

        world.spellbook.start_cooldown("freeze", 0.0)  # Ready
        cast_freeze(world.spellbook, world, [monster])
        # Refreshes to full duration, not 1.0 + 4.0
        assert monster.frozen_timer == pytest.approx(FREEZE_DURATION)
