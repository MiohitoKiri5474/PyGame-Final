import math

from constants import COMBAT_MIN_DAMAGE, TOWER_RANGE
from coords import tile_center


def _within(ax: float, ay: float, bx: float, by: float, max_range: float) -> bool:
    return math.hypot(ax - bx, ay - by) <= max_range


def resolve_combat(npcs: list, monsters: list, buildings=()) -> None:
    """Proximity-based auto-engage: every NPC/monster pair within the NPC's
    own combat_range (role-based - melee-adjacent by default, ranged for
    Mages) trades stat-based damage this tick (no manual targeting). Towers also
    auto-attack any monster within TOWER_RANGE regardless of adjacency, using
    the same damage formula, one-directional (monsters can't damage a Tower
    back - buildings have no health in this step); Walls never attack, purely
    a path obstruction. Dead entities are removed from both lists in place."""
    for npc in npcs:
        for monster in monsters:
            if monster.is_dead:
                # A monster killed earlier in this same resolve_combat() call
                # (e.g. by a different NPC paired against it a few
                # iterations ago) must not keep fighting: without this, a
                # life-steal monster reduced to lethal health by one NPC
                # could heal itself back above zero off a second NPC's
                # damage later in this same tick, "resurrecting" mid-tick.
                continue
            if _within(npc.x, npc.y, monster.x, monster.y, npc.combat_range):
                monster.health -= max(COMBAT_MIN_DAMAGE, npc.attack - monster.defense)
                monster_dmg = max(COMBAT_MIN_DAMAGE, monster.attack - npc.defense)
                npc.health -= monster_dmg
                if monster.life_steal:
                    monster.health = min(monster.max_health, monster.health + monster_dmg)

    for building in buildings:
        if building.type != "Tower":
            continue
        bx, by = tile_center(building.x, building.y)
        for monster in monsters:
            if _within(bx, by, monster.x, monster.y, TOWER_RANGE):
                monster.health -= max(COMBAT_MIN_DAMAGE, building.attack - monster.defense)

    npcs[:] = [npc for npc in npcs if not npc.is_dead]
    monsters[:] = [monster for monster in monsters if not monster.is_dead]
