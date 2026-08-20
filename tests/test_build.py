from blocking import is_wall_blocked
from build_task import (
    Building,
    _can_queue,
    _can_queue_house,
    building_occupies_tile,
    building_tiles,
    _on_complete_wall,
    _on_complete_house,
    _blocked_builds_hud_line,
    _can_perform_wall,
    _can_perform_tower,
    _can_perform_house,
    population_cap,
)
from coords import tile_at, tile_center
from constants import BASE_POPULATION_CAP, HOUSE_COST, WALL_COST, TOWER_COST
from npc import NPC
from pathfinding import find_path
from task import Task, update_npc_tasks
from world import World


def test_can_queue_valid_tile():
    world = World(npc_count=0)
    world.grid.get(10, 10).claimed = True
    world.grid.get(10, 10).resource = None
    assert _can_queue(world, (10, 10))


def test_can_queue_rejects_unclaimed():
    world = World(npc_count=0)
    world.grid.get(10, 10).claimed = False
    world.grid.get(10, 10).resource = None
    assert not _can_queue(world, (10, 10))


def test_can_queue_rejects_resource():
    world = World(npc_count=0)
    world.grid.get(10, 10).claimed = True
    world.grid.get(10, 10).resource = "crop"
    assert not _can_queue(world, (10, 10))


def test_can_queue_rejects_occupied():
    world = World(npc_count=0)
    world.grid.get(10, 10).claimed = True
    world.grid.get(10, 10).resource = None
    world.buildings.append(Building("Wall", 10, 10, 100, 0))
    assert not _can_queue(world, (10, 10))


def test_can_perform_checks_materials():
    world = World(npc_count=0)
    task_wall = Task("BuildWall", (10, 10))
    task_tower = Task("BuildTower", (10, 11))

    assert not _can_perform_wall(world, task_wall)
    assert not _can_perform_tower(world, task_tower)

    for res, amount in WALL_COST.items():
        world.inventory.add(res, amount)
    assert _can_perform_wall(world, task_wall)
    assert not _can_perform_tower(world, task_tower)

    for res, amount in TOWER_COST.items():
        world.inventory.add(res, amount)
    assert _can_perform_tower(world, task_tower)


def test_npc_skips_unaffordable_build_task_and_gathers_instead():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).claimed = True
    world.grid.get(cx + 1, cy).claimed = True
    world.grid.get(cx + 2, cy).claimed = True
    world.grid.get(cx + 2, cy).resource = "crop"

    # Queue BuildWall first (higher priority), then Gather
    world.tasks.add("BuildWall", (cx + 1, cy))
    world.tasks.add("Gather", (cx + 2, cy))

    npc = NPC(*tile_center(cx, cy), priority=["BuildWall", "Gather"])
    world.npcs.append(npc)

    # Initial tick: inventory has 0 crops. NPC skips BuildWall and claims Gather
    update_npc_tasks(world, 1 / 60)
    assert npc.task is not None
    assert npc.task.type == "Gather"


def test_on_complete_sufficient_funds():
    world = World(npc_count=0)
    task = Task("BuildWall", (10, 10))

    # Give enough resources
    for res, amount in WALL_COST.items():
        world.inventory.add(res, amount)

    assert _on_complete_wall(world, task) is True
    assert len(world.buildings) == 1
    assert world.buildings[0].type == "Wall"
    assert world.buildings[0].x == 10
    assert world.buildings[0].y == 10
    for res in WALL_COST:
        assert world.inventory.get(res) == 0


def test_building_wall_displaces_npc_to_side_of_wall():
    world = World(npc_count=0)
    for x in range(9, 12):
        for y in range(9, 12):
            world.grid.get(x, y).claimed = True

    npc = NPC(*tile_center(10, 10))
    world.npcs.append(npc)

    for res, amount in WALL_COST.items():
        world.inventory.add(res, amount)
    task = Task("BuildWall", (10, 10), assigned_npc=npc)

    assert _on_complete_wall(world, task) is True

    npc_tile = tile_at(npc.x, npc.y)
    assert npc_tile != (10, 10)  # NPC moved off the wall tile
    assert not is_wall_blocked(world.buildings, *npc_tile)  # NPC is on a valid non-wall tile
    assert world.grid.get(*npc_tile).claimed  # NPC is on claimed land

    # Pathfinding from the displaced position succeeds
    path = find_path(
        lambda x, y: world.grid.get(x, y).claimed and not is_wall_blocked(world.buildings, x, y),
        world.grid.width,
        world.grid.height,
        npc_tile,
        (9, 9),
    )
    assert path is not None


def test_on_complete_insufficient_funds():
    world = World(npc_count=0)
    task = Task("BuildWall", (10, 10))

    # Ensure inventory has 0 resources
    for res, amount in WALL_COST.items():
        assert world.inventory.get(res) < amount

    assert _on_complete_wall(world, task) is False
    assert len(world.buildings) == 0
    for res in WALL_COST:
        assert world.inventory.get(res) == 0


def test_blocked_builds_hud_line_empty_when_nothing_queued():
    world = World(npc_count=0)
    assert _blocked_builds_hud_line(world) == ""


def test_blocked_builds_hud_line_reports_unaffordable_queued_build():
    world = World(npc_count=0)
    world.tasks.add("BuildWall", (10, 10))  # inventory starts empty, unaffordable

    assert _blocked_builds_hud_line(world) == "Build blocked (insufficient resources): BuildWall"


def test_blocked_builds_hud_line_empty_once_affordable():
    world = World(npc_count=0)
    world.tasks.add("BuildWall", (10, 10))
    for res, amount in WALL_COST.items():
        world.inventory.add(res, amount)

    assert _blocked_builds_hud_line(world) == ""


def test_house_can_queue_requires_full_2x2_claimed_empty_area():
    world = World(npc_count=0)
    # Claim all 4 tiles for 2x2 house at (10, 10)
    for dx in range(2):
        for dy in range(2):
            world.grid.get(10 + dx, 10 + dy).claimed = True
            world.grid.get(10 + dx, 10 + dy).resource = None

    assert _can_queue_house(world, (10, 10))

    # If any single tile in the 2x2 area is unclaimed, reject
    world.grid.get(11, 11).claimed = False
    assert not _can_queue_house(world, (10, 10))
    world.grid.get(11, 11).claimed = True

    # If any single tile has a resource, reject
    world.grid.get(10, 11).resource = "wood"
    assert not _can_queue_house(world, (10, 10))
    world.grid.get(10, 11).resource = None

    # If building exists on any of the 4 tiles, reject
    world.buildings.append(Building("Wall", 11, 10, 100, 0))
    assert not _can_queue_house(world, (10, 10))


def test_house_occupies_all_4_tiles_and_blocks_other_buildings():
    world = World(npc_count=0)
    for x in range(10, 14):
        for y in range(10, 14):
            world.grid.get(x, y).claimed = True
            world.grid.get(x, y).resource = None

    house = Building("House", 10, 10, 0, 0)
    world.buildings.append(house)

    assert building_occupies_tile(house, 10, 10)
    assert building_occupies_tile(house, 11, 10)
    assert building_occupies_tile(house, 10, 11)
    assert building_occupies_tile(house, 11, 11)
    assert not building_occupies_tile(house, 12, 10)

    # 1x1 buildings cannot be placed on any of the 4 house tiles
    assert not _can_queue(world, (10, 10))
    assert not _can_queue(world, (11, 10))
    assert not _can_queue(world, (10, 11))
    assert not _can_queue(world, (11, 11))

    # But can be placed adjacent at (12, 10)
    assert _can_queue(world, (12, 10))


def test_house_can_perform_checks_materials():
    world = World(npc_count=0)
    task = Task("BuildHouse", (10, 10))
    assert not _can_perform_house(world, task)
    for res, amount in HOUSE_COST.items():
        world.inventory.add(res, amount)
    assert _can_perform_house(world, task)


def test_house_on_complete_builds_and_spends():
    world = World(npc_count=0)
    task = Task("BuildHouse", (10, 10))
    for res, amount in HOUSE_COST.items():
        world.inventory.add(res, amount)

    assert _on_complete_house(world, task) is True
    assert len(world.buildings) == 1
    assert world.buildings[0].type == "House"
    assert world.buildings[0].x == 10
    assert world.buildings[0].y == 10
    for res in HOUSE_COST:
        assert world.inventory.get(res) == 0


def test_population_cap_is_base_with_no_houses():
    world = World(npc_count=0)
    assert population_cap(world) == BASE_POPULATION_CAP


def test_population_cap_increases_per_house():
    world = World(npc_count=0)
    world.buildings.append(Building("House", 1, 1, 0, 0))
    assert population_cap(world) == BASE_POPULATION_CAP + 1
    world.buildings.append(Building("House", 5, 5, 0, 0))
    assert population_cap(world) == BASE_POPULATION_CAP + 2


def test_population_cap_ignores_other_building_types():
    world = World(npc_count=0)
    world.buildings.append(Building("Wall", 1, 1, 100, 0))
    world.buildings.append(Building("Tower", 2, 2, 10, 15))
    assert population_cap(world) == BASE_POPULATION_CAP
