import math

from constants import COMBAT_MIN_DAMAGE, TOWER_RANGE
from coords import tile_center


def _within(ax: float, ay: float, bx: float, by: float, max_range: float) -> bool:
    return math.hypot(ax - bx, ay - by) <= max_range


def resolve_combat(npcs: list, monsters: list, buildings=(), on_damage=None) -> None:
    """Proximity-based auto-engage: every NPC/monster pair within the NPC's
    own combat_range (role-based - melee-adjacent by default, ranged for
    Mages) trades stat-based damage this tick (no manual targeting). Towers also
    auto-attack any monster within TOWER_RANGE regardless of adjacency, using
    the same damage formula, one-directional (monsters can't damage a Tower
    back - buildings have no health in this step); Walls never attack, purely
    a path obstruction. Dead entities are removed from both lists in place."""
    for npc in npcs:
        if getattr(npc, "is_resting", False):
            continue
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
                # NPC Attack on cooldown check
                npc_ready = getattr(npc, "attack_cooldown", 0.0) <= 0.0
                if npc_ready:
                    npc_dmg = max(COMBAT_MIN_DAMAGE, npc.attack - monster.defense)
                    monster.health -= npc_dmg
                    if getattr(npc, "role", None) == "Mage":
                        npc.attack_cooldown = 1.2
                    elif getattr(npc, "role", None) == "Knight":
                        npc.attack_cooldown = 0.8
                    else:
                        npc.attack_cooldown = 1.0

                    if on_damage:
                        on_damage(npc, monster, npc_dmg)
                    if hasattr(npc, "trigger_attack"):
                        npc.trigger_attack(monster.x, monster.y)
                    if hasattr(monster, "trigger_hit"):
                        monster.trigger_hit()

                # Monster Attack on cooldown check
                monster_ready = getattr(monster, "attack_cooldown", 0.0) <= 0.0
                if monster_ready and not monster.is_dead:
                    monster_dmg = max(COMBAT_MIN_DAMAGE, monster.attack - npc.defense)
                    npc.health -= monster_dmg
                    mtype = getattr(monster, "type", None)
                    if mtype == "Werewolf":
                        monster.attack_cooldown = 0.9
                    elif mtype == "Vampire":
                        monster.attack_cooldown = 1.0
                    elif mtype == "Zombie":
                        monster.attack_cooldown = 1.3
                    else:
                        monster.attack_cooldown = 1.0

                    if on_damage:
                        on_damage(monster, npc, monster_dmg)
                    if hasattr(monster, "trigger_attack"):
                        monster.trigger_attack(npc.x, npc.y)
                    if hasattr(npc, "trigger_hit"):
                        npc.trigger_hit()

                    if monster.life_steal:
                        monster.health = min(monster.max_health, monster.health + monster_dmg)

                # Mage tactical micro-kiting: step back slightly when enemies get too close
                if getattr(npc, "role", None) == "Mage":
                    dx = npc.x - monster.x
                    dy = npc.y - monster.y
                    dist = math.hypot(dx, dy)
                    if 0.1 < dist < 45.0:
                        npc.x += (dx / dist) * 6.0
                        npc.y += (dy / dist) * 6.0

    for building in buildings:
        if building.type != "Tower":
            continue
        tower_ready = getattr(building, "attack_cooldown", 0.0) <= 0.0
        if not tower_ready:
            continue

        bx, by = tile_center(building.x, building.y)
        # Single-target priority: lock onto the nearest living monster in range
        target_monster = None
        min_dist = float("inf")
        for monster in monsters:
            if monster.is_dead:
                continue
            d = math.hypot(bx - monster.x, by - monster.y)
            if d <= TOWER_RANGE and d < min_dist:
                min_dist = d
                target_monster = monster

        if target_monster is not None:
            tower_dmg = max(COMBAT_MIN_DAMAGE, building.attack - target_monster.defense)
            target_monster.health -= tower_dmg
            building.attack_cooldown = 1.4  # Reload cooldown per arrow
            if on_damage:
                on_damage(building, target_monster, tower_dmg)
            if hasattr(target_monster, "trigger_hit"):
                target_monster.trigger_hit()

    npcs[:] = [npc for npc in npcs if not npc.is_dead]
    monsters[:] = [monster for monster in monsters if not monster.is_dead]

