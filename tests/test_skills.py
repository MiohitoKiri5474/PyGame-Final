from constants import (
    AOE_RADIUS_BONUS_PER_LEVEL,
    DEFENSE_BONUS_PER_LEVEL,
    FREEZE_RADIUS,
    HEALTH_BONUS_PER_LEVEL,
    KNIGHT_CRIT_CHANCE,
    ROLE_KNIGHT,
    SKILL_AOE_ATTACK,
    SKILL_DEFENSE_ABILITY,
    SKILL_GATHER_SPEED,
    SKILL_HUNTING_ACCURACY,
    SKILL_MAGIC_ATTACK,
    SKILL_NAMES,
    SKILL_TAMING_ABILITY,
)
from npc import NPC
from skills import (
    aoe_radius,
    defense_bonus_defense,
    defense_bonus_health,
    gather_speed_multiplier,
    hunting_crit_chance,
    magic_damage_multiplier,
    new_skill_levels,
    spend_point,
    taming_success_bonus,
)
from world import World


def test_new_skill_levels_starts_all_zero():
    levels = new_skill_levels()
    assert levels == {name: 0 for name in SKILL_NAMES}


def test_spend_point_increments_level_and_decrements_points():
    world = World(npc_count=0)
    remaining, ok = spend_point(world, 3, SKILL_GATHER_SPEED)
    assert ok is True
    assert remaining == 2
    assert world.skills[SKILL_GATHER_SPEED] == 1


def test_spend_point_blocked_at_zero_available():
    world = World(npc_count=0)
    remaining, ok = spend_point(world, 0, SKILL_GATHER_SPEED)
    assert ok is False
    assert remaining == 0
    assert world.skills[SKILL_GATHER_SPEED] == 0


def test_spend_point_rejects_unknown_skill_name():
    world = World(npc_count=0)
    remaining, ok = spend_point(world, 3, "Not A Skill")
    assert ok is False
    assert remaining == 3


def test_gather_speed_multiplier_at_levels_0_1_2():
    world = World(npc_count=0)
    assert gather_speed_multiplier(world) == 1.0
    spend_point(world, 5, SKILL_GATHER_SPEED)
    assert gather_speed_multiplier(world) == 0.9
    spend_point(world, 5, SKILL_GATHER_SPEED)
    assert gather_speed_multiplier(world) == 0.8


def test_magic_damage_multiplier_at_levels_0_1_2():
    world = World(npc_count=0)
    assert magic_damage_multiplier(world) == 1.0
    spend_point(world, 5, SKILL_MAGIC_ATTACK)
    assert magic_damage_multiplier(world) == 1.15
    spend_point(world, 5, SKILL_MAGIC_ATTACK)
    assert round(magic_damage_multiplier(world), 2) == 1.30


def test_aoe_radius_at_levels_0_1_2():
    world = World(npc_count=0)
    assert aoe_radius(world) == FREEZE_RADIUS
    spend_point(world, 5, SKILL_AOE_ATTACK)
    assert aoe_radius(world) == FREEZE_RADIUS + AOE_RADIUS_BONUS_PER_LEVEL
    spend_point(world, 5, SKILL_AOE_ATTACK)
    assert aoe_radius(world) == FREEZE_RADIUS + 2 * AOE_RADIUS_BONUS_PER_LEVEL


def test_hunting_crit_chance_at_levels_0_1_2():
    world = World(npc_count=0)
    assert hunting_crit_chance(world) == KNIGHT_CRIT_CHANCE
    spend_point(world, 5, SKILL_HUNTING_ACCURACY)
    assert round(hunting_crit_chance(world), 2) == KNIGHT_CRIT_CHANCE + 0.10
    spend_point(world, 5, SKILL_HUNTING_ACCURACY)
    assert round(hunting_crit_chance(world), 2) == KNIGHT_CRIT_CHANCE + 0.20


def test_taming_success_bonus_at_levels_0_1_2():
    world = World(npc_count=0)
    assert taming_success_bonus(world) == 0.0
    spend_point(world, 5, SKILL_TAMING_ABILITY)
    assert round(taming_success_bonus(world), 2) == 0.10
    spend_point(world, 5, SKILL_TAMING_ABILITY)
    assert round(taming_success_bonus(world), 2) == 0.20


def test_defense_bonus_values_at_levels_0_1_2():
    world = World(npc_count=0)
    assert defense_bonus_defense(world) == 0
    assert defense_bonus_health(world) == 0
    spend_point(world, 5, SKILL_DEFENSE_ABILITY)
    assert defense_bonus_defense(world) == DEFENSE_BONUS_PER_LEVEL
    assert defense_bonus_health(world) == HEALTH_BONUS_PER_LEVEL
    spend_point(world, 5, SKILL_DEFENSE_ABILITY)
    assert defense_bonus_defense(world) == 2 * DEFENSE_BONUS_PER_LEVEL
    assert defense_bonus_health(world) == 2 * HEALTH_BONUS_PER_LEVEL


def test_spending_defense_point_retroactively_buffs_all_current_npcs():
    world = World(npc_count=0)
    npc = NPC(0.0, 0.0, role=ROLE_KNIGHT)
    base_defense = npc.defense
    base_max_health = npc.max_health
    base_health = npc.health
    world.npcs.append(npc)

    spend_point(world, 5, SKILL_DEFENSE_ABILITY)

    assert npc.defense == base_defense + DEFENSE_BONUS_PER_LEVEL
    assert npc.max_health == base_max_health + HEALTH_BONUS_PER_LEVEL
    assert npc.health == base_health + HEALTH_BONUS_PER_LEVEL


def test_spending_defense_point_does_not_affect_dead_npcs():
    world = World(npc_count=0)
    npc = NPC(0.0, 0.0, role=ROLE_KNIGHT)
    npc.kill()
    base_defense = npc.defense
    world.npcs.append(npc)

    spend_point(world, 5, SKILL_DEFENSE_ABILITY)

    assert npc.defense == base_defense  # dead NPCs are not retroactively buffed
