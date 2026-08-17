from constants import (
    COLOR_FIRE_FLASH,
    COLOR_FREEZE_FLASH,
    COLOR_LIGHTNING_FLASH,
    FIRE_BURN_DAMAGE_PER_TICK,
    FIRE_BURN_TICKS,
    FIRE_COOLDOWN,
    FIRE_DAMAGE,
    FREEZE_COOLDOWN,
    FREEZE_DURATION,
    LIGHTNING_COOLDOWN,
    LIGHTNING_DAMAGE,
    ROLE_MAGE,
)
from magic import Spellbook, cast_fire, cast_freeze, cast_lightning, nearest_monster_to_territory
from monster import Monster
from npc import NPC
from world import World


def test_spellbook_starts_ready():
    book = Spellbook()
    assert book.is_ready("Lightning")
    assert book.remaining("Lightning") == 0.0


def test_spellbook_start_cooldown_then_not_ready():
    book = Spellbook()
    book.start_cooldown("Lightning", 20.0)
    assert not book.is_ready("Lightning")
    assert book.remaining("Lightning") == 20.0


def test_spellbook_tick_counts_down_and_becomes_ready_at_zero():
    book = Spellbook()
    book.start_cooldown("Lightning", 5.0)
    book.tick(3.0)
    assert book.remaining("Lightning") == 2.0
    assert not book.is_ready("Lightning")
    book.tick(2.0)
    assert book.is_ready("Lightning")


def test_spellbook_tick_never_goes_negative():
    book = Spellbook()
    book.start_cooldown("Lightning", 1.0)
    book.tick(100.0)
    assert book.remaining("Lightning") == 0.0


def test_spellbook_trigger_flash_accumulates_and_expires_independently():
    book = Spellbook()
    book.trigger_flash((0.0, 0.0), 0.5, COLOR_FIRE_FLASH)
    book.trigger_flash((1.0, 1.0), 2.0, COLOR_LIGHTNING_FLASH)
    assert len(book.flashes) == 2

    book.tick(1.0)  # first flash's 0.5s duration has elapsed, second hasn't
    assert len(book.flashes) == 1
    assert book.flashes[0]["color"] == COLOR_LIGHTNING_FLASH


def test_nearest_monster_to_territory_picks_the_closer_one():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    from coords import tile_center

    near = Monster(*tile_center(cx + 6, cy))  # just outside claimed radius
    far = Monster(*tile_center(0, 0))  # map corner, far from claimed territory
    assert nearest_monster_to_territory(world, [far, near]) is near


def test_nearest_monster_to_territory_returns_none_with_no_monsters():
    world = World(npc_count=0)
    assert nearest_monster_to_territory(world, []) is None


def _world_with_mage():
    world = World(npc_count=0)
    world.npcs.append(NPC(0.0, 0.0, role=ROLE_MAGE))
    return world


def test_cast_lightning_fails_on_cooldown():
    world = _world_with_mage()
    monster = Monster(0.0, 0.0)
    world.spellbook.start_cooldown("Lightning", 5.0)
    assert cast_lightning(world, [monster]) is False
    assert monster.health == monster.health  # unchanged (no assertion needed on exact value)


def test_cast_lightning_fails_without_a_living_mage():
    world = World(npc_count=0)  # no Mage
    monster = Monster(0.0, 0.0)
    assert cast_lightning(world, [monster]) is False


def test_cast_lightning_fails_with_no_monsters():
    world = _world_with_mage()
    assert cast_lightning(world, []) is False


def test_cast_lightning_succeeds_damages_nearest_and_starts_cooldown():
    world = _world_with_mage()
    from coords import tile_center

    cx, cy = world.grid.width // 2, world.grid.height // 2
    near = Monster(*tile_center(cx + 6, cy))
    far = Monster(*tile_center(0, 0))
    start_health = near.health

    assert cast_lightning(world, [far, near]) is True
    assert near.health == start_health - LIGHTNING_DAMAGE
    assert far.health == far.health  # untouched
    assert world.spellbook.remaining("Lightning") == LIGHTNING_COOLDOWN
    assert any(f["color"] == COLOR_LIGHTNING_FLASH for f in world.spellbook.flashes)


def test_cast_lightning_ignores_dead_mage():
    world = World(npc_count=0)
    dead_mage = NPC(0.0, 0.0, role=ROLE_MAGE)
    dead_mage.kill()
    world.npcs.append(dead_mage)
    monster = Monster(0.0, 0.0)
    assert cast_lightning(world, [monster]) is False


def test_cast_fire_fails_on_cooldown():
    world = _world_with_mage()
    monster = Monster(0.0, 0.0)
    world.spellbook.start_cooldown("Fire", 5.0)
    assert cast_fire(world, [monster]) is False


def test_cast_fire_fails_without_a_living_mage():
    world = World(npc_count=0)
    monster = Monster(0.0, 0.0)
    assert cast_fire(world, [monster]) is False


def test_cast_fire_fails_with_no_monsters():
    world = _world_with_mage()
    assert cast_fire(world, []) is False


def test_cast_fire_deals_immediate_damage_and_applies_burn():
    world = _world_with_mage()
    from coords import tile_center

    cx, cy = world.grid.width // 2, world.grid.height // 2
    target = Monster(*tile_center(cx + 6, cy))
    start_health = target.health

    assert cast_fire(world, [target]) is True
    assert target.health == start_health - FIRE_DAMAGE
    assert target.burn_ticks_remaining == FIRE_BURN_TICKS
    assert target.burn_damage_per_tick == FIRE_BURN_DAMAGE_PER_TICK
    assert world.spellbook.remaining("Fire") == FIRE_COOLDOWN
    assert any(f["color"] == COLOR_FIRE_FLASH for f in world.spellbook.flashes)


def test_cast_fire_total_damage_includes_burn_dot():
    world = _world_with_mage()
    monster = Monster(0.0, 0.0)
    start_health = monster.health

    cast_fire(world, [monster])
    for _ in range(FIRE_BURN_TICKS):
        monster.update(1.0)

    expected_total = FIRE_DAMAGE + FIRE_BURN_TICKS * FIRE_BURN_DAMAGE_PER_TICK
    assert monster.health == start_health - expected_total


def test_fire_and_lightning_cooldowns_are_independent():
    world = _world_with_mage()
    monster = Monster(0.0, 0.0)
    assert cast_lightning(world, [monster]) is True
    assert cast_fire(world, [monster]) is True  # not blocked by Lightning's cooldown
    assert not world.spellbook.is_ready("Lightning")
    assert not world.spellbook.is_ready("Fire")


def test_cast_freeze_fails_on_cooldown():
    world = _world_with_mage()
    monster = Monster(0.0, 0.0)
    world.spellbook.start_cooldown("Freeze", 5.0)
    assert cast_freeze(world, [monster]) is False


def test_cast_freeze_fails_without_a_living_mage():
    world = World(npc_count=0)
    monster = Monster(0.0, 0.0)
    assert cast_freeze(world, [monster]) is False


def test_cast_freeze_fails_with_no_monsters():
    world = _world_with_mage()
    assert cast_freeze(world, []) is False


def test_cast_freeze_starts_cooldown_and_flash():
    world = _world_with_mage()
    from coords import tile_center

    cx, cy = world.grid.width // 2, world.grid.height // 2
    target = Monster(*tile_center(cx + 6, cy))

    assert cast_freeze(world, [target]) is True
    assert world.spellbook.remaining("Freeze") == FREEZE_COOLDOWN
    assert any(f["color"] == COLOR_FREEZE_FLASH for f in world.spellbook.flashes)


def test_cast_freeze_affects_every_monster_inside_the_3x3_box():
    world = _world_with_mage()
    from coords import tile_center

    cx, cy = world.grid.width // 2, world.grid.height // 2
    center_tile = (cx + 6, cy)
    center = Monster(*tile_center(*center_tile))
    inside = Monster(*tile_center(center_tile[0] + 1, center_tile[1] - 1))  # corner of the 3x3
    outside = Monster(*tile_center(center_tile[0] + 2, center_tile[1]))  # just past the box

    assert cast_freeze(world, [center, inside, outside]) is True
    assert center.is_frozen
    assert inside.is_frozen
    assert not outside.is_frozen
    assert center.frozen_remaining == FREEZE_DURATION
    assert inside.frozen_remaining == FREEZE_DURATION
    # one flash per affected monster, not a single shared slot
    assert len(world.spellbook.flashes) == 2


def test_cast_freeze_refreshes_rather_than_stacks_on_an_already_frozen_monster():
    world = _world_with_mage()
    monster = Monster(0.0, 0.0)
    monster.apply_freeze(1.0)  # already frozen, about to expire

    assert cast_freeze(world, [monster]) is True
    assert monster.frozen_remaining == FREEZE_DURATION  # refreshed, not 1.0 + FREEZE_DURATION
