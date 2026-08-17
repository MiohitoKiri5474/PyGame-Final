from coords import tile_center
from npc import NPC


def test_new_npc_has_no_path_and_has_arrived():
    npc = NPC(x=10.0, y=10.0)
    assert npc.has_arrived
    assert npc.path == []


def test_set_path_clears_arrived_state():
    npc = NPC(x=0.0, y=0.0)
    npc.set_path([(0, 0), (1, 0)])
    assert not npc.has_arrived


def test_update_moves_toward_next_waypoint():
    start_x, start_y = tile_center(0, 0)
    npc = NPC(x=start_x, y=start_y, speed=100.0)
    npc.set_path([(2, 0)])
    npc.update(0.1)
    assert npc.x > start_x
    assert npc.y == start_y


def test_update_reaches_and_pops_waypoint_exactly_at_target():
    target = tile_center(1, 0)
    npc = NPC(x=target[0] - 5, y=target[1], speed=100.0)
    npc.set_path([(1, 0)])
    npc.update(1.0)  # far more than enough distance to cover 5px at speed 100
    assert npc.has_arrived
    assert (npc.x, npc.y) == target


def test_update_walks_full_path_to_completion():
    npc = NPC(x=0.0, y=0.0, speed=1000.0)  # fast enough to finish in a few ticks
    npc.set_path([(0, 0), (1, 0), (2, 0)])
    for _ in range(50):
        if npc.has_arrived:
            break
        npc.update(1 / 60)
    assert npc.has_arrived
    assert (npc.x, npc.y) == tile_center(2, 0)


def test_update_does_nothing_when_no_path():
    npc = NPC(x=5.0, y=5.0)
    npc.update(1.0)
    assert (npc.x, npc.y) == (5.0, 5.0)
