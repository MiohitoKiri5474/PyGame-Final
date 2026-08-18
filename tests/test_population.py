from build_task import Building
from constants import BASE_POPULATION_CAP, DAY_SECONDS, NIGHT_SECONDS, ROLES
from coords import tile_at
from day_night import DAY, DayNightCycle
from population import maybe_spawn_npc
from world import World


def _house():
    return Building(type="House", x=0, y=0, block=0, attack=0)


def test_no_spawn_when_not_transitioned():
    world = World(npc_count=0)
    assert maybe_spawn_npc(world, round_number=3, transitioned=False) is None
    assert world.npcs == []


def test_no_spawn_on_round_not_a_multiple_of_three():
    world = World(npc_count=0)
    for round_number in (1, 2, 4, 5, 7, 8):
        assert maybe_spawn_npc(world, round_number, transitioned=True) is None
    assert world.npcs == []


def test_spawns_on_round_3_6_9():
    for round_number in (3, 6, 9):
        world = World(npc_count=0)
        npc = maybe_spawn_npc(world, round_number, transitioned=True)
        assert npc is not None
        assert world.npcs == [npc]


def test_spawn_suppressed_at_population_cap():
    world = World(npc_count=BASE_POPULATION_CAP)
    assert maybe_spawn_npc(world, round_number=3, transitioned=True) is None
    assert len(world.npcs) == BASE_POPULATION_CAP


def test_spawn_allowed_once_a_house_raises_the_cap():
    # Default colony is exactly at the base cap (STARTING_NPC_COUNT ==
    # BASE_POPULATION_CAP == 3), so growth only materializes once a House
    # has been built - this is the realistic path the game actually hits.
    world = World(npc_count=BASE_POPULATION_CAP)
    world.buildings.append(_house())

    npc = maybe_spawn_npc(world, round_number=3, transitioned=True)

    assert npc is not None
    assert len(world.npcs) == BASE_POPULATION_CAP + 1

    # Back at cap after the new arrival - suppressed again on the next
    # qualifying round until another House is built.
    assert maybe_spawn_npc(world, round_number=6, transitioned=True) is None
    assert len(world.npcs) == BASE_POPULATION_CAP + 1


def test_spawned_npc_gets_a_valid_role():
    world = World(npc_count=0)
    npc = maybe_spawn_npc(world, round_number=3, transitioned=True)
    assert npc.role in ROLES


def test_spawned_npc_role_round_robins_like_the_starting_colony():
    world = World(npc_count=0)
    for _ in range(6):
        world.buildings.append(_house())

    roles = [maybe_spawn_npc(world, round_number, transitioned=True).role for round_number in (3, 6, 9)]

    assert roles == [ROLES[0], ROLES[1], ROLES[2]]


def test_spawned_npc_role_continues_the_default_worlds_round_robin():
    # Default World() already assigned ROLES[0..2] to its 3 starting NPCs
    # (world.py's own round-robin) - a 4th NPC should continue that
    # sequence from ROLES[0], not restart some independent counter.
    world = World()
    world.buildings.append(_house())

    npc = maybe_spawn_npc(world, round_number=3, transitioned=True)

    assert npc.role == ROLES[0]


def test_spawn_avoids_a_wall_built_on_the_colony_center_tile():
    # Buildings allow free placement with no adjacency rule, so a Wall can
    # end up sitting exactly on the colony center - the default spawn tile.
    # A spawn placed there would be permanently unable to path anywhere
    # (task.py's pathfinding treats the NPC's own Wall-occupied start tile
    # as impassable), so it must fall back to a nearby unblocked tile.
    world = World(npc_count=0)
    world.buildings.append(_house())
    cx, cy = world.grid.width // 2, world.grid.height // 2
    world.buildings.append(Building(type="Wall", x=cx, y=cy, block=1, attack=0))

    npc = maybe_spawn_npc(world, round_number=3, transitioned=True)

    assert npc is not None
    spawn_tile = tile_at(npc.x, npc.y)
    assert spawn_tile != (cx, cy)
    assert world.grid.get(*spawn_tile).claimed


def test_direction_gate_prevents_double_spawn_when_round_repeats_across_transitions():
    # round_number is the SAME value across two consecutive transitions
    # (night->day into round 3, then day->night out of round 3 again shows
    # round_number == 3). A caller that doesn't gate on direction would
    # spawn twice for one qualifying round; this exercises the exact
    # composition game.py uses: `transitioned and cycle.phase == DAY`.
    world = World(npc_count=0)
    world.buildings.append(_house())
    cycle = DayNightCycle()
    spawned = []

    def tick(dt):
        transitioned = cycle.update(dt)
        npc = maybe_spawn_npc(world, cycle.round_number, transitioned and cycle.phase == DAY)
        if npc is not None:
            spawned.append(npc)

    tick(DAY_SECONDS)  # day1 -> night1 (round stays 1)
    tick(NIGHT_SECONDS)  # night1 -> day2 (round=2)
    tick(DAY_SECONDS)  # day2 -> night2 (round stays 2)
    tick(NIGHT_SECONDS)  # night2 -> day3 (round=3) -> should spawn
    tick(DAY_SECONDS)  # day3 -> night3 (round stays 3) -> must NOT spawn again

    assert cycle.round_number == 3
    assert len(spawned) == 1
