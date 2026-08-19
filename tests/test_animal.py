from animal import Animal
from constants import TILE_SIZE


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
