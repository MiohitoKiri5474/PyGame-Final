from build_task import Building, _can_queue, _on_complete_wall
from task import Task
from world import World
from constants import WALL_COST

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
