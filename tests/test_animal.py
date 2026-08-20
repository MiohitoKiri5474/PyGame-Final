import math

from animal import Animal
from constants import TILE_SIZE
from npc import NPC


def test_new_animal_is_not_hostile():
    animal = Animal(0.0, 0.0, species="Wolf", speed=90.0, dangerous=True, health=35)
    assert animal.is_hostile is False


def test_non_dangerous_species_stays_non_hostile_after_taking_damage():
    animal = Animal(0.0, 0.0, species="WildBoar", speed=70.0, dangerous=False, health=30)
    animal.take_damage(10)
    assert animal.is_hostile is False


def test_dangerous_species_becomes_hostile_only_after_taking_damage():
    animal = Animal(0.0, 0.0, species="Bear", speed=50.0, dangerous=True, health=60)
    assert animal.is_hostile is False
    animal.take_damage(10)
    assert animal.is_hostile is True


def test_take_damage_reduces_health():
    animal = Animal(0.0, 0.0, species="Horse", speed=140.0, dangerous=False, health=40)
    animal.take_damage(15)
    assert animal.health == 25


def test_is_dead_when_health_reaches_zero():
    animal = Animal(0.0, 0.0, species="Fish", speed=60.0, dangerous=False, health=10)
    assert not animal.is_dead
    animal.take_damage(10)
    assert animal.is_dead


def test_update_wanders_to_a_new_tile_over_time():
    animal = Animal(16.0, 16.0, species="FlyingSquirrel", speed=1000.0, dangerous=False, health=10)
    animal.wander_timer = 0.0
    start = (animal.x, animal.y)
    for _ in range(60):
        animal.update(1 / 60, grid_width=10, grid_height=10)
    assert (animal.x, animal.y) != start



def test_update_never_wanders_out_of_grid_bounds():
    # animal starts in the top-left corner tile - half its possible wander
    # directions would leave the grid if not bounds-checked
    animal = Animal(16.0, 16.0, species="Fish", speed=1000.0, dangerous=False, health=10)
    for _ in range(300):
        animal.update(1 / 60, grid_width=2, grid_height=2)
        assert 0 <= animal.x < 2 * TILE_SIZE
        assert 0 <= animal.y < 2 * TILE_SIZE


def test_tamed_animal_holds_position_when_not_following_or_idle_walking():
    animal = Animal(16.0, 16.0, species="Horse", speed=140.0, dangerous=False, health=40)
    animal.is_tamed = True
    for _ in range(60):
        animal.update(1 / 60, grid_width=50, grid_height=50)
    assert (animal.x, animal.y) == (16.0, 16.0)


def test_following_animal_closes_in_on_its_tamer():
    npc = NPC(500.0, 16.0)
    animal = Animal(16.0, 16.0, species="Horse", speed=140.0, dangerous=False, health=40)
    animal.is_tamed = True
    animal.is_following = True
    animal.tamer_npc_id = npc.id

    start_dist = abs(animal.x - npc.x)
    for _ in range(120):
        npc.update(1 / 60)
        animal.update(1 / 60, grid_width=50, grid_height=50, npcs=[npc])
    end_dist = abs(animal.x - npc.x)
    assert end_dist < start_dist


def test_following_animal_does_not_fully_overlap_a_stationary_tamer():
    # If the tamer stops moving, prev_x/prev_y converges on its own live
    # position tick after tick - without a minimum follow distance the pet
    # would keep closing the gap all the way to a dead stop on top of it.
    npc = NPC(500.0, 16.0)
    animal = Animal(16.0, 16.0, species="Horse", speed=140.0, dangerous=False, health=40)
    animal.is_tamed = True
    animal.is_following = True
    animal.tamer_npc_id = npc.id

    for _ in range(300):  # npc never gets a path - stays put the whole time
        npc.update(1 / 60)
        animal.update(1 / 60, grid_width=50, grid_height=50, npcs=[npc])

    from constants import PET_FOLLOW_MIN_DISTANCE
    dist = math.hypot(animal.x - npc.x, animal.y - npc.y)
    assert dist > PET_FOLLOW_MIN_DISTANCE * 0.5  # nowhere near fully overlapping


def test_following_animal_trails_tamers_previous_position_not_live_one():
    npc = NPC(100.0, 100.0)
    animal = Animal(100.0, 100.0, species="Horse", speed=1000.0, dangerous=False, health=40)
    animal.is_tamed = True
    animal.is_following = True
    animal.tamer_npc_id = npc.id

    npc.x = 200.0  # NPC's own movement machinery not exercised here - just jump it
    animal.update(1 / 60, grid_width=50, grid_height=50, npcs=[npc])
    # npc.prev_x is still 100.0 (only npc.update() advances it) - animal should
    # have moved toward that, not toward the NPC's already-jumped live x=200.0
    assert animal.x == 100.0


def test_following_animal_falls_back_to_idle_when_tamer_is_gone():
    npc = NPC(100.0, 100.0)
    animal = Animal(100.0, 100.0, species="Horse", speed=140.0, dangerous=False, health=40)
    animal.is_tamed = True
    animal.is_following = True
    animal.tamer_npc_id = npc.id
    animal.pen_tile = (5, 5)

    animal.update(1 / 60, grid_width=50, grid_height=50, npcs=[])  # tamer not found
    assert not animal.is_following
    assert animal.idle_target is not None


def test_targeted_animal_does_not_start_a_new_wander_hop():
    animal = Animal(16.0, 16.0, species="FlyingSquirrel", speed=1000.0, dangerous=False, health=10)
    animal.is_targeted = True
    start = (animal.x, animal.y)
    for _ in range(30):
        animal.update(1 / 60, grid_width=10, grid_height=10)
    assert (animal.x, animal.y) == start


def test_targeted_animal_still_finishes_a_hop_already_in_progress():
    animal = Animal(16.0, 16.0, species="FlyingSquirrel", speed=1000.0, dangerous=False, health=10)
    animal.set_path([(1, 0)])  # already mid-hop when targeting starts
    animal.is_targeted = True
    animal.update(1.0, grid_width=10, grid_height=10)  # one full second easily covers the single tile hop
    assert (animal.x, animal.y) != (16.0, 16.0)  # let the in-flight hop land
    assert animal.path == []  # but doesn't queue another one after


def test_idle_target_walk_clears_on_arrival():
    animal = Animal(0.0, 0.0, species="Horse", speed=1000.0, dangerous=False, health=40)
    animal.is_tamed = True
    animal.idle_target = (32.0, 0.0)
    animal.update(1.0, grid_width=50, grid_height=50)  # one full second easily covers 32px at speed 1000
    assert animal.idle_target is None
    assert (animal.x, animal.y) == (32.0, 0.0)


def test_mounted_animal_snaps_to_rider_ignoring_follow_min_distance():
    # Mounting must overlap the rider exactly - the opposite of the
    # PET_FOLLOW_MIN_DISTANCE gate a merely-following pet respects.
    npc = NPC(500.0, 200.0)
    animal = Animal(16.0, 16.0, species="Horse", speed=140.0, dangerous=False, health=40)
    animal.is_tamed = True
    animal.is_following = True
    animal.is_mounted = True
    animal.tamer_npc_id = npc.id

    animal.update(1 / 60, grid_width=50, grid_height=50, npcs=[npc])
    assert (animal.x, animal.y) == (npc.x, npc.y)


def test_mounted_animal_auto_dismounts_when_rider_dies():
    npc = NPC(16.0, 16.0)
    animal = Animal(16.0, 16.0, species="Horse", speed=140.0, dangerous=False, health=40)
    animal.is_tamed = True
    animal.is_following = True
    animal.is_mounted = True
    animal.tamer_npc_id = npc.id
    animal.pen_tile = (5, 5)

    npc.kill()
    animal.update(1 / 60, grid_width=50, grid_height=50, npcs=[npc])

    assert animal.is_mounted is False
    assert animal.is_following is False
    assert animal.idle_target is not None
