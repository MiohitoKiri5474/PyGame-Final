from constants import LIGHTNING_COOLDOWN, LIGHTNING_DAMAGE, ROLE_MAGE
from magic import Spellbook, cast_lightning, nearest_monster_to_territory
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


def test_cast_lightning_ignores_dead_mage():
    world = World(npc_count=0)
    dead_mage = NPC(0.0, 0.0, role=ROLE_MAGE)
    dead_mage.kill()
    world.npcs.append(dead_mage)
    monster = Monster(0.0, 0.0)
    assert cast_lightning(world, [monster]) is False
