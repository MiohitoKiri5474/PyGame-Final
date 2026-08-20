from build_task import Building
from coords import tile_center
from destroy_task import _can_queue, _can_perform, _on_complete
from npc import NPC
from task import Task, update_npc_tasks
from world import World


def test_can_queue_accepts_tile_with_building():
    world = World(npc_count=0)
    world.grid.get(5, 5).claimed = True
    world.buildings.append(Building("Wall", 5, 5, 100, 0))

    assert _can_queue(world, (5, 5)) is True


def test_can_queue_rejects_tile_without_building():
    world = World(npc_count=0)
    world.grid.get(5, 5).claimed = True
    # no building

    assert _can_queue(world, (5, 5)) is False


def test_can_queue_rejects_out_of_bounds_tile():
    world = World(npc_count=0)
    assert _can_queue(world, (-1, 0)) is False
    assert _can_queue(world, (999, 999)) is False


def test_can_queue_rejects_already_queued_destroy():
    world = World(npc_count=0)
    world.grid.get(5, 5).claimed = True
    world.buildings.append(Building("Tower", 5, 5, 10, 15))
    world.tasks.add("Destroy", (5, 5))

    assert _can_queue(world, (5, 5)) is False


def test_can_perform_requires_building_presence():
    world = World(npc_count=0)
    task = Task("Destroy", (5, 5))

    assert _can_perform(world, task) is False

    world.buildings.append(Building("Wall", 5, 5, 100, 0))
    assert _can_perform(world, task) is True


def test_on_complete_removes_building():
    world = World(npc_count=0)
    world.buildings.append(Building("Wall", 5, 5, 100, 0))
    world.buildings.append(Building("Tower", 6, 6, 10, 15))
    task = Task("Destroy", (5, 5))

    assert _on_complete(world, task) is True
    assert len(world.buildings) == 1
    assert world.buildings[0].x == 6
    assert world.buildings[0].y == 6


def test_full_destroy_task_lifecycle_with_npc():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).claimed = True
    world.grid.get(cx + 1, cy).claimed = True

    # Place a building at (cx + 1, cy)
    building = Building("Wall", cx + 1, cy, 100, 0)
    world.buildings.append(building)

    npc = NPC(*tile_center(cx, cy))
    world.npcs.append(npc)
    world.tasks.add("Destroy", (cx + 1, cy))

    for _ in range(300):
        update_npc_tasks(world, 1 / 60)
        if not world.buildings:
            break

    assert len(world.buildings) == 0
    assert npc.task is None
    assert world.tasks.tasks == []


def test_destroy_2x2_house_from_any_corner_removes_building():
    world = World(npc_count=0)
    for x in range(5, 7):
        for y in range(5, 7):
            world.grid.get(x, y).claimed = True

    # Place 2x2 House at (5, 5)
    house = Building("House", 5, 5, 0, 0)
    world.buildings.append(house)

    # Any of the 4 occupied tiles can queue Destroy
    assert _can_queue(world, (5, 5)) is True
    assert _can_queue(world, (6, 5)) is True
    assert _can_queue(world, (5, 6)) is True
    assert _can_queue(world, (6, 6)) is True

    # Queue Destroy on bottom-right corner (6, 6)
    world.tasks.add("Destroy", (6, 6))

    # Other corners cannot double-queue Destroy on the same house
    assert _can_queue(world, (5, 5)) is False

    task = Task("Destroy", (6, 6))
    assert _on_complete(world, task) is True
    assert len(world.buildings) == 0
