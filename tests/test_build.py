from build_task import Building, _can_queue, _on_complete_wall, _blocked_builds_hud_line, _can_perform_wall, _can_perform_tower
from task import Task, update_npc_tasks
from npc import NPC
from coords import tile_center
from world import World
from constants import WALL_COST, TOWER_COST


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

    world.inventory.add("crop", WALL_COST["crop"])
    assert _can_perform_wall(world, task_wall)
    assert not _can_perform_tower(world, task_tower)

    world.inventory.add("crop", TOWER_COST["crop"] - WALL_COST["crop"])
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

    initial_crop = world.inventory.get("crop")

    assert _on_complete_wall(world, task) is True
    assert len(world.buildings) == 1
    assert world.buildings[0].type == "Wall"
    assert world.buildings[0].x == 10
    assert world.buildings[0].y == 10
    assert world.inventory.get("crop") == initial_crop - WALL_COST["crop"]


def test_on_complete_insufficient_funds():
    world = World(npc_count=0)
    task = Task("BuildWall", (10, 10))

    # Ensure inventory has 0 resources
    initial_crop = world.inventory.get("crop")
    assert initial_crop < WALL_COST["crop"]

    assert _on_complete_wall(world, task) is False
    assert len(world.buildings) == 0
    assert world.inventory.get("crop") == initial_crop


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
