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


def test_can_queue_rejects_unclaimed_tile_not_adjacent_to_claimed_land():
    # A target with no path in from claimed territory would permanently
    # deadlock the queue (claim_for always retries the unreachable
    # head-of-queue task, starving every Expand task behind it) - reject it
    # at queue time instead.
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    isolated = (cx + START_CLAIM_RADIUS + 5, cy)
    assert not world.grid.get(*isolated).claimed

    assert not TASK_TYPES["Expand"].can_queue(world, isolated)


def test_can_perform_true_for_still_unclaimed_target():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    frontier = (cx + START_CLAIM_RADIUS + 1, cy)
    task = world.tasks.add("Expand", frontier)

    assert TASK_TYPES["Expand"].can_perform(world, task)


def test_can_perform_false_once_a_different_expand_already_claimed_the_target():
    # Claim radii overlap by design - a queued-but-not-yet-worked Expand's
    # target can end up already claimed as a side effect of a different,
    # earlier Expand finishing nearby. That task is now genuinely dead work.
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    near = (cx + START_CLAIM_RADIUS + 1, cy)
    far = (cx + START_CLAIM_RADIUS + 1 + EXPAND_CLAIM_RADIUS, cy)
    task = world.tasks.add("Expand", far)

    world.grid.expand(*near, EXPAND_CLAIM_RADIUS, EXPAND_REVEAL_RADIUS)  # swallows `far` too
    assert world.grid.get(*far).claimed

    assert not TASK_TYPES["Expand"].can_perform(world, task)


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
