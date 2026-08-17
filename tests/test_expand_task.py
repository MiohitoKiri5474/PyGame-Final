import expand_task  # noqa: F401  # ensure "Expand" is registered
from task import TASK_TYPES, update_npc_tasks
from world import World
from npc import NPC
from coords import tile_center
from constants import EXPAND_CLAIM_RADIUS, EXPAND_REVEAL_RADIUS, START_CLAIM_RADIUS


def test_can_queue_rejects_already_claimed_tile():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    assert world.grid.get(cx, cy).claimed

    assert not TASK_TYPES["Expand"].can_queue(world, (cx, cy))


def test_can_queue_accepts_unclaimed_frontier_tile():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    frontier = (cx + START_CLAIM_RADIUS + 1, cy)
    assert not world.grid.get(*frontier).claimed

    assert TASK_TYPES["Expand"].can_queue(world, frontier)


def test_can_queue_rejects_tile_already_queued():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    frontier = (cx + START_CLAIM_RADIUS + 1, cy)
    world.tasks.add("Expand", frontier)

    assert not TASK_TYPES["Expand"].can_queue(world, frontier)


def test_can_queue_rejects_out_of_bounds_tile():
    world = World(npc_count=0)
    assert not TASK_TYPES["Expand"].can_queue(world, (-1, -1))


def test_full_expand_task_lifecycle_claims_and_reveals_tiles():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    frontier = (cx + START_CLAIM_RADIUS + 1, cy)
    assert not world.grid.get(*frontier).claimed

    npc = NPC(*tile_center(cx, cy))
    world.npcs.append(npc)
    world.tasks.add("Expand", frontier)

    for _ in range(600):  # generous tick budget: walk + work_seconds
        update_npc_tasks(world, 1 / 60)
        if not world.tasks.tasks:
            break

    assert world.tasks.tasks == []
    assert npc.task is None
    assert world.grid.get(*frontier).claimed
    assert world.grid.get(frontier[0] + EXPAND_CLAIM_RADIUS, frontier[1]).claimed
    assert world.grid.get(frontier[0] + EXPAND_REVEAL_RADIUS, frontier[1]).revealed
