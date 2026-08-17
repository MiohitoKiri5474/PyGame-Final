import pytest

from constants import RESOURCE_WEIGHTS
from grid import Grid
from task import TASK_TYPES, Task
from world import World


def test_new_grid_claims_smaller_radius_than_it_reveals():
    grid = Grid(seed=1)
    cx, cy = grid.width // 2, grid.height // 2

    # just outside claim radius but inside reveal radius: revealed, not claimed
    from constants import START_CLAIM_RADIUS, START_REVEAL_RADIUS

    assert START_REVEAL_RADIUS > START_CLAIM_RADIUS
    frontier = grid.get(cx + START_CLAIM_RADIUS + 1, cy)
    assert frontier.revealed
    assert not frontier.claimed


def test_expand_claim_radius_defaults_to_reveal_radius_when_omitted():
    grid = Grid(seed=1)
    grid.expand(5, 5, claim_radius=2)
    assert grid.get(5, 7).claimed
    assert grid.get(5, 7).revealed


def test_expand_reveal_radius_can_exceed_claim_radius():
    grid = Grid(seed=1)
    grid.expand(5, 5, claim_radius=1, reveal_radius=3)
    assert grid.get(5, 6).claimed  # within claim radius
    assert not grid.get(5, 8).claimed  # outside claim radius
    assert grid.get(5, 8).revealed  # but within reveal radius


# --- Material taxonomy (ticket 14) ---


def test_resource_weights_table_covers_wild_resource_and_five_materials():
    assert set(RESOURCE_WEIGHTS) == {
        None,
        "crop",
        "wood",
        "marble",
        "bricks",
        "berries",
        "raw_stone",
    }
    assert sum(RESOURCE_WEIGHTS.values()) == pytest.approx(1.0)


def test_weighted_generation_produces_every_resource_type_over_enough_tiles():
    # Grid always generates GRID_WIDTH*GRID_HEIGHT tiles regardless of seed, so
    # a handful of fixed seeds gives thousands of rolls - enough that even the
    # rarest 0.015 weight is certain to land at least once, deterministically.
    seen = set()
    for seed in range(10):
        for row in Grid(seed=seed).tiles:
            for tile in row:
                seen.add(tile.resource)
    assert seen == set(RESOURCE_WEIGHTS)


def test_weighted_generation_still_leaves_empty_tiles():
    grid = Grid(seed=1)
    assert any(tile.resource is None for row in grid.tiles for tile in row)


@pytest.mark.parametrize("resource", ["crop", "wood", "marble", "bricks", "berries", "raw_stone"])
def test_gather_credits_inventory_for_each_material_with_no_gather_task_changes(resource):
    # gather_task.py's on_complete is already generic (world.inventory.add(tile.resource, ...));
    # this proves every new material flows through it correctly with zero edits to that file.
    world = World(npc_count=0)
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.grid.get(cx, cy).resource = resource

    gather = TASK_TYPES["Gather"]
    task = Task("Gather", (cx, cy))
    assert gather.on_complete(world, task) is True

    assert world.inventory.get(resource) == 1
    assert world.grid.get(cx, cy).resource is None
