from build_task import Building
from constants import FARMLAND_COST, FARMLAND_GROW_SECONDS, FARMLAND_YIELD
from farmland_task import (
    _can_queue_build_farmland,
    _can_perform_harvest,
    _on_complete_build_farmland,
    _can_queue_harvest,
    _on_complete_harvest,
    _tick_farmland_growth,
)
from task import Task
from world import World


def _funded_world() -> World:
    world = World(npc_count=0)
    for res, amount in FARMLAND_COST.items():
        world.inventory.add(res, amount)
    return world


def test_build_farmland_can_queue_same_rule_as_other_buildings():
    world = World(npc_count=0)
    world.grid.get(10, 10).claimed = True
    world.grid.get(10, 10).resource = None
    assert _can_queue_build_farmland(world, (10, 10))


def test_build_farmland_creates_not_ready_with_zero_growth_timer():
    world = _funded_world()
    task = Task("BuildFarmland", (10, 10))
    assert _on_complete_build_farmland(world, task) is True

    farmland = world.buildings[0]
    assert farmland.type == "Farmland"
    assert farmland.ready is False
    assert farmland.growth_timer == 0.0
    for res in FARMLAND_COST:
        assert world.inventory.get(res) == 0


def test_growth_tick_advances_timer_and_flips_ready_at_threshold():
    world = World(npc_count=0)
    farmland = Building(type="Farmland", x=5, y=5, block=0, attack=0)
    world.buildings.append(farmland)

    _tick_farmland_growth(world, FARMLAND_GROW_SECONDS - 1.0)
    assert farmland.ready is False

    _tick_farmland_growth(world, 1.0)
    assert farmland.ready is True


def test_growth_tick_ignores_non_farmland_buildings():
    world = World(npc_count=0)
    wall = Building(type="Wall", x=5, y=5, block=100, attack=0)
    world.buildings.append(wall)

    _tick_farmland_growth(world, FARMLAND_GROW_SECONDS * 10)
    assert wall.ready is False  # untouched, still the dataclass default


def test_harvest_not_queueable_before_ready():
    world = World(npc_count=0)
    world.buildings.append(Building(type="Farmland", x=5, y=5, block=0, attack=0, ready=False))
    assert not _can_queue_harvest(world, (5, 5))


def test_harvest_queueable_once_ready():
    world = World(npc_count=0)
    world.buildings.append(Building(type="Farmland", x=5, y=5, block=0, attack=0, ready=True))
    assert _can_queue_harvest(world, (5, 5))


def test_harvest_not_queueable_twice_on_same_tile():
    world = World(npc_count=0)
    world.buildings.append(Building(type="Farmland", x=5, y=5, block=0, attack=0, ready=True))
    world.tasks.add("HarvestFarmland", (5, 5))
    assert not _can_queue_harvest(world, (5, 5))


def test_harvest_credits_yield_and_restarts_growth_cycle():
    world = World(npc_count=0)
    farmland = Building(type="Farmland", x=5, y=5, block=0, attack=0, growth_timer=FARMLAND_GROW_SECONDS, ready=True)
    world.buildings.append(farmland)
    task = Task("HarvestFarmland", (5, 5))

    assert _on_complete_harvest(world, task) is True
    assert world.inventory.get("crop") == FARMLAND_YIELD
    assert farmland.ready is False
    assert farmland.growth_timer == 0.0


def test_harvest_cycle_repeats_after_restart():
    world = World(npc_count=0)
    farmland = Building(type="Farmland", x=5, y=5, block=0, attack=0, ready=True)
    world.buildings.append(farmland)
    _on_complete_harvest(world, Task("HarvestFarmland", (5, 5)))
    assert world.inventory.get("crop") == FARMLAND_YIELD

    _tick_farmland_growth(world, FARMLAND_GROW_SECONDS)
    assert farmland.ready is True
    _on_complete_harvest(world, Task("HarvestFarmland", (5, 5)))
    assert world.inventory.get("crop") == FARMLAND_YIELD * 2


def test_harvest_on_complete_is_a_no_op_when_farmland_already_gone():
    # e.g. destroyed while a Harvest task was queued/in-flight - completion
    # must clear the task (return True) rather than leaving it stuck forever
    world = World(npc_count=0)
    task = Task("HarvestFarmland", (5, 5))
    assert _on_complete_harvest(world, task) is True
    assert world.inventory.get("crop") == 0


def test_can_perform_harvest_false_when_no_farmland_at_target():
    world = World(npc_count=0)
    assert not _can_perform_harvest(world, Task("HarvestFarmland", (5, 5)))


def test_can_perform_harvest_false_when_farmland_not_ready():
    world = World(npc_count=0)
    world.buildings.append(Building(type="Farmland", x=5, y=5, block=0, attack=0, ready=False))
    assert not _can_perform_harvest(world, Task("HarvestFarmland", (5, 5)))


def test_can_perform_harvest_true_when_farmland_ready():
    world = World(npc_count=0)
    world.buildings.append(Building(type="Farmland", x=5, y=5, block=0, attack=0, ready=True))
    assert _can_perform_harvest(world, Task("HarvestFarmland", (5, 5)))


def test_stale_harvest_task_cannot_credit_a_rebuilt_unready_farmland():
    # destroy+rebuild-on-the-same-tile race: a stale queued HarvestFarmland
    # task must not be able to claim/complete against a brand-new, not-yet-
    # ready Farmland that happens to share the old one's coordinates
    world = World(npc_count=0)
    stale_task = Task("HarvestFarmland", (5, 5))  # queued while the old Farmland was ready
    # old Farmland destroyed, a new one built on the same tile - not ready
    world.buildings.append(Building(type="Farmland", x=5, y=5, block=0, attack=0, ready=False))

    assert not _can_perform_harvest(world, stale_task)  # must never be claimable/workable
