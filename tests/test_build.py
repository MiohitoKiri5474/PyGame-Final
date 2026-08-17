from blocking import is_wall_blocked
from build_task import Building, _can_queue, _on_complete_wall, _blocked_builds_hud_line, _can_perform_wall, _can_perform_tower
from coords import tile_at, tile_center
from constants import WALL_COST, TOWER_COST
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
