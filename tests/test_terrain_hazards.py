import pytest

from constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    START_CLAIM_RADIUS,
    TERRAIN_PLAIN,
    TERRAIN_RIVER,
    TERRAIN_MOUNTAIN,
    TERRAIN_MUD,
    TERRAIN_SCORCHED,
    RIVER_SPEED_MULTIPLIER,
    MUD_IMMOBILIZE_DURATION,
    SCORCHED_BURN_DPS,
)
from coords import tile_center
from grid import Grid, Tile
from monster import _path_toward
from npc import NPC
from pathfinding import find_path
from save import _dump_grid, _load_grid


def test_terrain_generation_places_diverse_terrains_and_safe_colony_start():
    grid = Grid(seed=42)
    start_x, start_y = GRID_WIDTH // 2, GRID_HEIGHT // 2

    # Colony start must be 100% plain
    for dy in range(-START_CLAIM_RADIUS, START_CLAIM_RADIUS + 1):
        for dx in range(-START_CLAIM_RADIUS, START_CLAIM_RADIUS + 1):
            tile = grid.get(start_x + dx, start_y + dy)
            assert tile.terrain == TERRAIN_PLAIN

    # Across the entire grid, all 5 terrains must be generated
    terrain_counts = {t: 0 for t in (TERRAIN_PLAIN, TERRAIN_RIVER, TERRAIN_MOUNTAIN, TERRAIN_MUD, TERRAIN_SCORCHED)}
    for row in grid.tiles:
        for t in row:
            terrain_counts[t.terrain] += 1

    assert terrain_counts[TERRAIN_PLAIN] > 0
    assert terrain_counts[TERRAIN_RIVER] > 0
    assert terrain_counts[TERRAIN_MOUNTAIN] > 0
    assert terrain_counts[TERRAIN_MUD] > 0
    assert terrain_counts[TERRAIN_SCORCHED] > 0


def test_river_slows_npc_speed():
    grid = Grid()
    # Place river tiles along (5, 5), (6, 5), (7, 5), (8, 5)
    for x in range(5, 9):
        grid.get(x, 5).terrain = TERRAIN_RIVER
    cx, cy = tile_center(5, 5)
    npc = NPC(cx, cy, speed=100.0)

    # Path to destination 3 tiles away (96px)
    npc.set_path([(8, 5)])
    npc.update(0.5, grid=grid)

    assert npc.is_in_river is True
    # In 0.5s at 50px/s, NPC should have moved 25px instead of 50px
    dx = npc.x - cx
    assert pytest.approx(dx, 0.1) == 100.0 * RIVER_SPEED_MULTIPLIER * 0.5


def test_mountain_is_impassable_for_pathfinding():
    grid = Grid()
    # Clear an open 5x5 test area to plain
    for y in range(10, 15):
        for x in range(10, 15):
            grid.get(x, y).terrain = TERRAIN_PLAIN

    # Place a wall of mountains between (10, 12) and (14, 12) except at (14, 12)
    for x in range(10, 14):
        grid.get(x, 12).terrain = TERRAIN_MOUNTAIN

    # Monster pathfinding from (11, 11) to (11, 13) should detour around the mountain through (14, 12)
    path = _path_toward((11, 11), (11, 13), grid, buildings=())
    assert path is not None
    # Path must never step on mountain tiles
    for px, py in path:
        assert grid.get(px, py).terrain != TERRAIN_MOUNTAIN


def test_mud_immobilizes_npc_for_five_seconds():
    grid = Grid()
    grid.get(5, 5).terrain = TERRAIN_PLAIN
    grid.get(6, 5).terrain = TERRAIN_MUD

    cx, cy = tile_center(5, 5)
    npc = NPC(cx, cy, speed=120.0)
    npc.set_path([(6, 5), (7, 5)])

    # Step into (6, 5) mud
    target_cx, target_cy = tile_center(6, 5)
    npc.x, npc.y = target_cx, target_cy
    npc.update(0.1, grid=grid)

    assert npc.immobilized_timer > 0.0
    assert pytest.approx(npc.immobilized_timer, 0.2) == MUD_IMMOBILIZE_DURATION - 0.1

    # While immobilized, NPC cannot move
    curr_x = npc.x
    npc.update(2.0, grid=grid)
    assert npc.x == curr_x
    assert pytest.approx(npc.immobilized_timer, 0.2) == MUD_IMMOBILIZE_DURATION - 2.1

    # After 5.0 seconds total, immobilization wears off and NPC resumes moving
    npc.update(3.0, grid=grid)
    assert npc.immobilized_timer == 0.0
    npc.update(0.5, grid=grid)
    assert npc.x > curr_x


def test_scorched_earth_burns_npc_health_and_sets_burning_flag():
    grid = Grid()
    grid.get(5, 5).terrain = TERRAIN_SCORCHED
    cx, cy = tile_center(5, 5)
    npc = NPC(cx, cy)
    initial_health = npc.health

    # Standing on scorched earth triggers burning and damages health
    npc.update(2.0, grid=grid)
    assert npc.is_burning is True
    assert pytest.approx(npc.health, 0.1) == initial_health - (SCORCHED_BURN_DPS * 2.0)

    # Move to plain clears burning
    grid.get(5, 5).terrain = TERRAIN_PLAIN
    npc.update(0.1, grid=grid)
    assert npc.is_burning is False

    # Excessive burn kills NPC
    grid.get(5, 5).terrain = TERRAIN_SCORCHED
    npc.update(100.0, grid=grid)
    assert npc.is_dead is True
    assert npc.alive is False


def test_terrain_save_load_round_trip():
    grid = Grid(seed=99)
    dumped = _dump_grid(grid)
    loaded = _load_grid(dumped)

    assert loaded.width == grid.width
    assert loaded.height == grid.height
    for y in range(grid.height):
        for x in range(grid.width):
            orig_tile = grid.get(x, y)
            loaded_tile = loaded.get(x, y)
            assert loaded_tile.terrain == orig_tile.terrain
            assert loaded_tile.resource == orig_tile.resource
            assert loaded_tile.revealed == orig_tile.revealed
            assert loaded_tile.claimed == orig_tile.claimed


def test_expand_cannot_target_mountain_tile():
    from world import World
    from expand_task import _can_queue
    world = World(npc_count=1)
    # Set tile (35, 22) (which is adjacent to claimed area) to mountain
    world.grid.get(35, 22).claimed = False
    world.grid.get(35, 22).revealed = True
    world.grid.get(35, 22).terrain = TERRAIN_MOUNTAIN

    assert _can_queue(world, (35, 22)) is False

    # A plain tile can be queued
    world.grid.get(35, 22).terrain = TERRAIN_PLAIN
    assert _can_queue(world, (35, 22)) is True


def test_mountain_has_no_resources_and_cannot_be_gathered():
    from world import World
    from gather_task import _can_queue, _can_perform
    from grid import _roll_resource
    import random

    # 1. Mountains never roll resources
    rng = random.Random(42)
    for _ in range(50):
        assert _roll_resource(rng, terrain=TERRAIN_MOUNTAIN) is None

    # 2. Gather tasks cannot be queued or performed on mountain tiles
    world = World(npc_count=1)
    mountain_tile = (30, 22)
    world.grid.get(*mountain_tile).terrain = TERRAIN_MOUNTAIN
    world.grid.get(*mountain_tile).resource = 'raw_stone'
    world.grid.get(*mountain_tile).claimed = True

    assert _can_queue(world, mountain_tile) is False
