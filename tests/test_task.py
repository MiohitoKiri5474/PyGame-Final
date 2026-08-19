import task as task_module
from task import TaskQueue, TaskType, update_npc_tasks
from npc import NPC
from world import World
from constants import ROLE_FARMER


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


def test_on_complete_returning_false_keeps_task_queued_and_frees_npc(monkeypatch):
    # If a task cannot complete (e.g. materials missing), it stays queued,
    # but the NPC is freed so it can work on other available tasks instead of staying stuck.
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
    assert task.assigned_npc is None  # unassigned so NPC is not stuck
    assert npc.task is None


def test_npc_skips_blocked_task_and_claims_available_one(monkeypatch):
    can_perform_a = False

    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {
            "BlockedTask": TaskType(
                work_seconds=0.01,
                can_queue=lambda w, t: True,
                on_complete=lambda w, t: True,
                can_perform=lambda w, t: can_perform_a,
            ),
            "AvailableTask": TaskType(
                work_seconds=0.01,
                can_queue=lambda w, t: True,
                on_complete=lambda w, t: True,
            ),
        },
    )

    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).claimed = True
    world.grid.get(cx + 1, cy).claimed = True

    from coords import tile_center

    npc = NPC(*tile_center(cx, cy), priority=["BlockedTask", "AvailableTask"])
    world.npcs.append(npc)

    world.tasks.add("BlockedTask", (cx, cy))
    world.tasks.add("AvailableTask", (cx + 1, cy))

    update_npc_tasks(world, 1 / 60)

    assert npc.task is not None
    assert npc.task.type == "AvailableTask"


def test_npc_aborts_task_if_it_becomes_blocked_in_progress(monkeypatch):
    can_perform = True

    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {
            "DynamicTask": TaskType(
                work_seconds=5.0,
                can_queue=lambda w, t: True,
                on_complete=lambda w, t: True,
                can_perform=lambda w, t: can_perform,
            ),
            "FallbackTask": TaskType(
                work_seconds=1.0,
                can_queue=lambda w, t: True,
                on_complete=lambda w, t: True,
            ),
        },
    )

    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).claimed = True
    world.grid.get(cx + 1, cy).claimed = True

    from coords import tile_center

    npc = NPC(*tile_center(cx, cy), priority=["DynamicTask", "FallbackTask"])
    world.npcs.append(npc)

    t1 = world.tasks.add("DynamicTask", (cx, cy))
    t2 = world.tasks.add("FallbackTask", (cx + 1, cy))

    update_npc_tasks(world, 1 / 60)
    assert npc.task is t1

    # Invalidate dynamic task (e.g. resources consumed)
    can_perform = False
    update_npc_tasks(world, 1 / 60)

    # NPC should have dropped DynamicTask and claimed FallbackTask
    assert t1.assigned_npc is None
    assert npc.task is t2

    # It's still in the queue this same tick (purge already ran before the
    # per-NPC loop unassigned it) - one more tick sweeps it away for good,
    # rather than it lingering forever as a zombie entry.
    assert t1 in world.tasks.tasks
    update_npc_tasks(world, 1 / 60)
    assert t1 not in world.tasks.tasks


def test_unassigned_stale_task_is_purged_without_ever_being_claimed(monkeypatch):
    # Nothing else ever touches an unassigned task's validity - claim_for
    # just skips over it every scan. Without the purge it would sit in the
    # queue forever once it goes stale before anyone claims it (e.g. two
    # overlapping Expand targets, ticket 03).
    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {
            "DeadOnArrival": TaskType(
                work_seconds=5.0,
                can_queue=lambda w, t: True,
                on_complete=lambda w, t: True,
                can_perform=lambda w, t: False,
            ),
        },
    )
    world = World(npc_count=0)
    task = world.tasks.add("DeadOnArrival", (0, 0))

    update_npc_tasks(world, 1 / 60)
    assert task not in world.tasks.tasks


def test_purge_leaves_still_valid_unassigned_tasks_alone(monkeypatch):
    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {
            "StillGood": TaskType(
                work_seconds=5.0,
                can_queue=lambda w, t: True,
                on_complete=lambda w, t: True,
                can_perform=lambda w, t: True,
            ),
            "NoCanPerform": TaskType(
                work_seconds=5.0,
                can_queue=lambda w, t: True,
                on_complete=lambda w, t: True,
            ),
        },
    )
    world = World(npc_count=0)
    t1 = world.tasks.add("StillGood", (0, 0))
    t2 = world.tasks.add("NoCanPerform", (1, 1))  # no can_perform at all - always considered valid

    update_npc_tasks(world, 1 / 60)
    assert t1 in world.tasks.tasks
    assert t2 in world.tasks.tasks


def test_npc_skips_unreachable_task_and_claims_reachable_task(monkeypatch):
    from build_task import Building
    from coords import tile_center

    world = World(npc_count=0)
    start, wall_tile, blocked_target, open_target = (0, 0), (1, 0), (2, 0), (0, 1)
    for x, y in (start, wall_tile, blocked_target, open_target):
        world.grid.get(x, y).claimed = True
    world.buildings.append(Building("Wall", wall_tile[0], wall_tile[1], 100, 0))

    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {"FakeTask": TaskType(work_seconds=0.01, can_queue=lambda w, t: True, on_complete=lambda w, t: True)},
    )

    npc = NPC(*tile_center(*start))
    world.npcs.append(npc)
    t_blocked = world.tasks.add("FakeTask", blocked_target)
    t_open = world.tasks.add("FakeTask", open_target)

    update_npc_tasks(world, 1 / 60)

    assert npc.task is t_open
    assert t_blocked.assigned_npc is None
    assert t_open.assigned_npc is npc


def test_npc_pathing_reports_no_path_when_a_wall_blocks_the_only_route(monkeypatch):
    # ticket 07: Wall tiles block NPC pathing the same way they block monsters.
    from build_task import Building
    from coords import tile_center

    world = World(npc_count=0)
    start, wall_tile, target = (0, 0), (1, 0), (2, 0)
    for x, y in (start, wall_tile, target):
        world.grid.get(x, y).claimed = True
    world.buildings.append(Building("Wall", wall_tile[0], wall_tile[1], 100, 0))

    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {"FakeTask": TaskType(work_seconds=0.01, can_queue=lambda w, t: True, on_complete=lambda w, t: True)},
    )

    npc = NPC(*tile_center(*start))
    world.npcs.append(npc)
    task = world.tasks.add("FakeTask", target)

    update_npc_tasks(world, 1 / 60)

    assert npc.task is None
    assert task.assigned_npc is None


def test_farmer_work_multiplier_finishes_task_faster(monkeypatch):
    # ticket 12: Farmer's 0.6x work_multiplier means the required progress
    # is task_type.work_seconds * 0.6, not the flat work_seconds.
    monkeypatch.setattr(
        task_module,
        "TASK_TYPES",
        {"FakeTask": TaskType(work_seconds=1.0, can_queue=lambda w, t: True, on_complete=lambda w, t: True)},
    )

    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).claimed = True

    from coords import tile_center

    npc = NPC(*tile_center(cx, cy), role=ROLE_FARMER)
    world.npcs.append(npc)
    world.tasks.add("FakeTask", (cx, cy))

    # 0.7s of work: below the flat 1.0s requirement, but above 1.0 * 0.6
    for _ in range(42):  # 42 * (1/60) = 0.7s
        update_npc_tasks(world, 1 / 60)

    assert npc.task is None  # finished already, thanks to the 0.6x multiplier
    assert world.tasks.tasks == []


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
