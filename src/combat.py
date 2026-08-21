import math

from constants import COMBAT_ATTACK_INTERVAL, COMBAT_MIN_DAMAGE, TOWER_RANGE
from coords import tile_center


def _within(ax: float, ay: float, bx: float, by: float, max_range: float) -> bool:
    return math.hypot(ax - bx, ay - by) <= max_range


def resolve_combat(npcs: list, monsters: list, buildings=(), on_damage=None, dt: float = 0.0) -> None:
    """Proximity-based auto-engage: every NPC/monster pair within the NPC's
    own combat_range (role-based - melee-adjacent by default, ranged for
    Mages) trades stat-based damage (no manual targeting). Towers also
    auto-attack any monster within TOWER_RANGE regardless of adjacency, using
    the same damage formula, one-directional (monsters can't damage a Tower
    back - buildings have no health in this step); Walls never attack, purely
    a path obstruction. Dead entities are removed from both lists in place.

    Each attacker only actually lands a hit once every COMBAT_ATTACK_INTERVAL
    seconds (attack_cooldown, ticked down here while in range) - previously
    this ran every single call with no throttling at all, dealing a full hit
    every frame (~60/sec) to anything in range, which killed things faster
    than a player could see or react to."""
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
                npc.attack_cooldown = max(0.0, getattr(npc, "attack_cooldown", 0.0) - dt)
                if npc.attack_cooldown <= 0.0:
                    npc_dmg = max(COMBAT_MIN_DAMAGE, npc.attack - monster.defense)
                    monster.health -= npc_dmg
                    npc.attack_cooldown = COMBAT_ATTACK_INTERVAL
                    if on_damage:
                        on_damage(npc, monster, npc_dmg)
                    if hasattr(npc, "trigger_attack"):
                        npc.trigger_attack(monster.x, monster.y)
                    if hasattr(monster, "trigger_hit"):
                        monster.trigger_hit()

                monster.attack_cooldown = max(0.0, getattr(monster, "attack_cooldown", 0.0) - dt)
                if monster.attack_cooldown <= 0.0 and not monster.is_dead:
                    monster_dmg = max(COMBAT_MIN_DAMAGE, monster.attack - npc.defense)
                    npc.health -= monster_dmg
                    monster.attack_cooldown = COMBAT_ATTACK_INTERVAL
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
        building.attack_cooldown = max(0.0, getattr(building, "attack_cooldown", 0.0) - dt)
        if building.attack_cooldown > 0.0:
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
            building.attack_cooldown = COMBAT_ATTACK_INTERVAL
            if on_damage:
                on_damage(building, target_monster, tower_dmg)
            if hasattr(target_monster, "trigger_hit"):
                target_monster.trigger_hit()

    npcs[:] = [npc for npc in npcs if not npc.is_dead]
    monsters[:] = [monster for monster in monsters if not monster.is_dead]
