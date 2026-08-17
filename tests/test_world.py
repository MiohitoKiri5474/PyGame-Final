from collections import Counter

from constants import ROLE_FARMER, ROLE_KNIGHT, ROLE_MAGE
from world import World


def test_default_start_is_exactly_one_of_each_role():
    world = World()
    roles = Counter(npc.role for npc in world.npcs)
    assert roles == Counter({ROLE_FARMER: 1, ROLE_KNIGHT: 1, ROLE_MAGE: 1})


def test_zero_npcs_produces_empty_list():
    world = World(npc_count=0)
    assert world.npcs == []
