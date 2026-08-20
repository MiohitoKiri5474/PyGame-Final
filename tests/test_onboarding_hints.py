from animal import Animal
from build_task import Building
from coords import tile_center
from npc import NPC
from onboarding_hints import _EVERGREEN_TIP, _onboarding_hint
from world import World


def _past_early_milestones(world: "World") -> None:
    """Advances world state past the first three onboarding checks
    (gather/build/defense), so later tests can isolate the milestones
    that come after them without repeating this setup each time."""
    world.inventory.add("wood", 5)
    world.buildings.append(Building(type="Wall", x=10, y=10, block=5, attack=0))


def test_suggests_gather_on_a_brand_new_game():
    # The starting map always ships with pre-claimed land around spawn, so
    # a fresh World's first reachable milestone is gathering, not expanding.
    world = World(npc_count=0)

    assert "Gather" in _onboarding_hint(world)


def test_suggests_building_once_resources_are_gathered_but_nothing_built():
    world = World(npc_count=0)
    world.inventory.add("wood", 5)

    assert "build" in _onboarding_hint(world)


def test_suggests_defenses_once_a_non_defense_building_exists():
    world = World(npc_count=0)
    world.inventory.add("wood", 5)
    world.buildings.append(Building(type="House", x=10, y=10, block=0, attack=0))

    hint = _onboarding_hint(world)
    assert "Wall" in hint or "Tower" in hint


def test_suggests_farmland_once_a_defense_building_exists():
    world = World(npc_count=0, animal_count=0)
    _past_early_milestones(world)

    assert "Farmland" in _onboarding_hint(world)


def test_suggests_taming_once_farmland_exists():
    world = World(npc_count=0, animal_count=0)
    _past_early_milestones(world)
    world.buildings.append(Building(type="Farmland", x=8, y=8, block=0, attack=0))

    assert "Tame" in _onboarding_hint(world)


def test_suggests_priority_table_once_an_animal_is_tamed():
    world = World(npc_count=1, animal_count=0)
    _past_early_milestones(world)
    world.buildings.append(Building(type="Farmland", x=8, y=8, block=0, attack=0))
    tamed = Animal(*tile_center(5, 5), species="Horse", speed=105.0, dangerous=False, health=40)
    tamed.is_tamed = True
    world.animals.append(tamed)

    assert "priority" in _onboarding_hint(world)


def test_suggests_skill_spending_once_priority_is_customized():
    world = World(npc_count=1, animal_count=0)
    _past_early_milestones(world)
    world.buildings.append(Building(type="Farmland", x=8, y=8, block=0, attack=0))
    tamed = Animal(*tile_center(5, 5), species="Horse", speed=105.0, dangerous=False, health=40)
    tamed.is_tamed = True
    world.animals.append(tamed)
    world.npcs[0].priority = ["Gather"]

    assert "skill" in _onboarding_hint(world)


def test_falls_back_to_the_evergreen_tip_once_every_milestone_is_met():
    # Never goes silent - once there's nothing left to suggest, it keeps
    # showing something rather than leaving the tip box empty for the rest
    # of the game.
    world = World(npc_count=1, animal_count=0)
    _past_early_milestones(world)
    world.buildings.append(Building(type="Farmland", x=8, y=8, block=0, attack=0))
    tamed = Animal(*tile_center(5, 5), species="Horse", speed=105.0, dangerous=False, health=40)
    tamed.is_tamed = True
    world.animals.append(tamed)
    world.npcs[0].priority = ["Gather"]
    world.skills[next(iter(world.skills))] = 1

    assert _onboarding_hint(world) == _EVERGREEN_TIP
