from build_task import Building
from onboarding_hints import _onboarding_hint
from world import World


def test_suggests_gather_on_a_brand_new_game():
    # The starting map always ships with pre-claimed land around spawn, so
    # a fresh World's first reachable milestone is gathering, not expanding.
    world = World(npc_count=0)

    assert "Gather" in _onboarding_hint(world)


def test_suggests_building_once_resources_are_gathered_but_nothing_built():
    world = World(npc_count=0)
    world.inventory.add("wood", 5)

    assert "Build" in _onboarding_hint(world)


def test_suggests_defenses_once_a_non_defense_building_exists():
    world = World(npc_count=0)
    world.inventory.add("wood", 5)
    world.buildings.append(Building(type="House", x=10, y=10, block=0, attack=0))

    hint = _onboarding_hint(world)
    assert "Wall" in hint or "Tower" in hint


def test_falls_silent_once_a_defense_building_exists():
    world = World(npc_count=0)
    world.inventory.add("wood", 5)
    world.buildings.append(Building(type="Wall", x=10, y=10, block=5, attack=0))

    assert _onboarding_hint(world) == ""
