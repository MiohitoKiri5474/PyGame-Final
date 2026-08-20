from build_task import Building
from constants import START_CLAIM_RADIUS
from tile_actions import applicable_tasks, build_task_types, building_label, is_build_task
from world import World

# World()'s Grid auto-claims a START_CLAIM_RADIUS blob around its own center
# at construction, so tests that care about "claimed" vs "unclaimed" work
# just outside that radius rather than assuming a blank slate.


def _empty_claimed_tile(world: World) -> tuple[int, int]:
    cx, cy = world.grid.width // 2, world.grid.height // 2
    tile = world.grid.get(cx, cy)
    tile.resource = None  # center is already claimed by construction; strip any rolled resource
    return cx, cy


def test_resource_tile_offers_only_gather():
    world = World(npc_count=0)
    x, y = _empty_claimed_tile(world)
    world.grid.get(x, y).resource = "crop"

    assert applicable_tasks(world, (x, y)) == ["Gather"]


def test_frontier_tile_offers_only_expand():
    world = World(npc_count=0)
    world.animals = []
    cx, cy = world.grid.width // 2, world.grid.height // 2
    frontier = (cx + START_CLAIM_RADIUS + 1, cy)  # unclaimed, adjacent to the claimed blob
    world.grid.get(*frontier).terrain = "plain"
    world.grid.get(*frontier).resource = None

    assert applicable_tasks(world, frontier) == ["Expand"]


def test_unreachable_unclaimed_tile_offers_nothing():
    world = World(npc_count=0)
    world.animals = []
    assert applicable_tasks(world, (0, 0)) == []


def test_building_tile_offers_only_destroy():
    world = World(npc_count=0)
    x, y = _empty_claimed_tile(world)
    world.buildings.append(Building("Wall", x, y, 100, 0))

    assert applicable_tasks(world, (x, y)) == ["Destroy"]


def test_empty_claimed_tile_offers_nothing_build_is_not_inferred():
    world = World(npc_count=0)
    x, y = _empty_claimed_tile(world)

    assert applicable_tasks(world, (x, y)) == []


def test_mature_farmland_offers_destroy_and_harvest():
    world = World(npc_count=0)
    x, y = _empty_claimed_tile(world)
    world.buildings.append(Building("Farmland", x, y, 0, 0, ready=True))

    assert applicable_tasks(world, (x, y)) == ["Destroy", "HarvestFarmland"]


def test_growing_farmland_offers_only_destroy():
    world = World(npc_count=0)
    x, y = _empty_claimed_tile(world)
    world.buildings.append(Building("Farmland", x, y, 0, 0, ready=False))

    assert applicable_tasks(world, (x, y)) == ["Destroy"]


def test_out_of_bounds_tile_offers_nothing():
    world = World(npc_count=0)
    assert applicable_tasks(world, (-1, -1)) == []


def test_build_task_types_are_excluded_from_inference():
    world = World(npc_count=0)
    x, y = _empty_claimed_tile(world)
    for name in build_task_types():
        assert name not in applicable_tasks(world, (x, y))


def test_is_build_task():
    assert is_build_task("BuildWall")
    assert not is_build_task("Gather")


def test_building_label_strips_build_prefix():
    assert building_label("BuildAnimalPen") == "AnimalPen"
    assert building_label("Gather") == "Gather"
