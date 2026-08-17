import task as task_module
from task import TaskQueue, update_npc_tasks
from npc import NPC
from world import World


def test_claim_for_picks_highest_priority_available_type():
    queue = TaskQueue()
    queue.add("A", (0, 0))
    queue.add("B", (1, 1))
    npc = NPC(x=0.0, y=0.0, priority=["B", "A"])
    claimed = queue.claim_for(npc)
    assert claimed.type == "B"
    assert claimed.assigned_npc is npc


def test_claim_for_skips_already_assigned_tasks():
    queue = TaskQueue()
    t = queue.add("A", (0, 0))
    t.assigned_npc = object()
    npc = NPC(x=0.0, y=0.0, priority=["A"])
    assert queue.claim_for(npc) is None


def test_claim_for_returns_none_when_no_matching_type_queued():
    queue = TaskQueue()
    queue.add("A", (0, 0))
    npc = NPC(x=0.0, y=0.0, priority=["B"])
    assert queue.claim_for(npc) is None


def test_claim_for_uses_registration_order_when_npc_has_no_priority(monkeypatch):
    monkeypatch.setattr(task_module, "TASK_TYPES", {"X": None, "Y": None})
    queue = TaskQueue()
    queue.add("Y", (0, 0))
    queue.add("X", (1, 1))
    npc = NPC(x=0.0, y=0.0)
    claimed = queue.claim_for(npc)
    assert claimed.type == "X"


def test_remove_drops_task_from_queue():
    queue = TaskQueue()
    t = queue.add("A", (0, 0))
    queue.remove(t)
    assert t not in queue.tasks


def test_remove_targets_by_identity_not_by_value_equality():
    # two unassigned tasks with the same type/target are value-equal
    # (Task is a plain dataclass), so removing "second" must not delete
    # "first" instead just because they compare equal and first sits
    # earlier in the list.
    queue = TaskQueue()
    first = queue.add("A", (0, 0))
    second = queue.add("A", (0, 0))
    assert first == second  # sanity: same type+target+unassigned -> equal

    queue.remove(second)
    assert len(queue.tasks) == 1
    assert queue.tasks[0] is first  # identity check: == would pass even on the wrong object


def test_full_gather_task_lifecycle_credits_inventory_and_clears_tile():
    world = World(npc_count=0)  # no auto-spawned NPCs; we place one precisely
    cx, cy = world.grid.width // 2, world.grid.height // 2
    resource_tile = world.grid.get(cx + 1, cy)
    resource_tile.resource = "crop"
    resource_tile.claimed = True

    from coords import tile_center

    npc = NPC(*tile_center(cx, cy))
    world.npcs.append(npc)
    world.tasks.add("Gather", (cx + 1, cy))

    for _ in range(600):  # generous tick budget: walk + work_seconds
        update_npc_tasks(world, 1 / 60)
        if world.inventory.get("crop") > 0:
            break

    assert world.inventory.get("crop") == 1
    assert resource_tile.resource is None
    assert npc.task is None
    assert world.tasks.tasks == []


def test_task_can_target_an_unclaimed_frontier_tile(monkeypatch):
    # generalization needed by ticket 03 (Expand Territory): the tile a task
    # targets need not be claimed yet - that's the whole point of Expand.
    from task import TaskType

    completed = []

    def _on_complete(world, task):
        completed.append(task.target)
        return True

    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {
            "FakeExpand": TaskType(
                work_seconds=0.01,
                can_queue=lambda world, tile: True,
                on_complete=_on_complete,
            )
        },
    )

    from constants import START_CLAIM_RADIUS

    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    frontier = (cx + START_CLAIM_RADIUS + 1, cy)
    assert not world.grid.get(*frontier).claimed  # precondition: genuinely unclaimed

    from coords import tile_center

    npc = NPC(*tile_center(cx, cy))
    world.npcs.append(npc)
    world.tasks.add("FakeExpand", frontier)

    for _ in range(120):
        update_npc_tasks(world, 1 / 60)
        if completed:
            break

    assert completed == [frontier]


def test_on_complete_returning_false_keeps_task_queued_and_npc_assigned(monkeypatch):
    # ticket 04 (Build): insufficient funds -> stays queued, reported, not
    # silently dropped. on_complete signals this by returning False.
    from task import TaskType

    attempts = []

    def _on_complete(world, task):
        attempts.append(1)
        return False

    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {"FakeBuild": TaskType(work_seconds=0.01, can_queue=lambda w, t: True, on_complete=_on_complete)},
    )

    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).claimed = True

    from coords import tile_center

    npc = NPC(*tile_center(cx, cy))
    world.npcs.append(npc)
    task = world.tasks.add("FakeBuild", (cx, cy))

    for _ in range(5):
        update_npc_tasks(world, 1 / 60)

    assert len(attempts) >= 1
    assert task in world.tasks.tasks  # still queued, not silently dropped
    assert npc.task is task  # NPC keeps waiting on it rather than abandoning


def test_idle_npc_does_not_reclaim_a_task_already_in_progress():
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).claimed = True
    world.grid.get(cx, cy).resource = "crop"

    from coords import tile_center

    npc_a = NPC(*tile_center(cx, cy))
    npc_b = NPC(*tile_center(cx, cy))
    world.npcs.extend([npc_a, npc_b])
    world.tasks.add("Gather", (cx, cy))

    update_npc_tasks(world, 1 / 60)
    update_npc_tasks(world, 1 / 60)

    assigned = [n for n in (npc_a, npc_b) if n.task is not None]
    assert len(assigned) == 1
