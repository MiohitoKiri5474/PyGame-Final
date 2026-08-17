import math

from constants import COMBAT_MIN_DAMAGE, COMBAT_RANGE


def _in_range(a, b) -> bool:
    return math.hypot(a.x - b.x, a.y - b.y) <= COMBAT_RANGE


def resolve_combat(npcs: list, monsters: list) -> None:
    """Proximity-based auto-engage: every NPC/monster pair within COMBAT_RANGE
    trades stat-based damage this tick (no manual targeting). Dead entities
    are removed from both lists in place."""
    for npc in npcs:
        for monster in monsters:
            if _in_range(npc, monster):
                monster.health -= max(COMBAT_MIN_DAMAGE, npc.attack - monster.defense)
                npc.health -= max(COMBAT_MIN_DAMAGE, monster.attack - npc.defense)

    npcs[:] = [npc for npc in npcs if not npc.is_dead]
    monsters[:] = [monster for monster in monsters if not monster.is_dead]
