from combat import resolve_combat
from constants import COMBAT_MIN_DAMAGE, COMBAT_RANGE
from coords import tile_center


class _Building:
    def __init__(self, type_: str, x: int, y: int, attack: int):
        self.type = type_
        self.x = x
        self.y = y
        self.attack = attack


class _Entity:
    def __init__(
        self, x: float, y: float, health: int, attack: int, defense: int,
        combat_range: float = COMBAT_RANGE, life_steal: bool = False, max_health: int | None = None,
    ):
        self.x = x
        self.y = y
        self.health = health
        self.attack = attack
        self.defense = defense
        self.combat_range = combat_range  # only read when used as the NPC side of a pair
        self.life_steal = life_steal  # only read when used as the monster side of a pair
        self.max_health = max_health if max_health is not None else health

    @property
    def is_dead(self) -> bool:
        return self.health <= 0


def test_adjacent_pair_trades_stat_based_damage():
    npc = _Entity(0, 0, health=100, attack=12, defense=4)
    monster = _Entity(10, 0, health=40, attack=10, defense=2)  # within COMBAT_RANGE
    resolve_combat([npc], [monster])
    assert monster.health == 40 - (12 - 2)
    assert npc.health == 100 - (10 - 4)


def test_damage_floors_at_minimum_when_defense_exceeds_attack():
    npc = _Entity(0, 0, health=100, attack=1, defense=50)
    monster = _Entity(0, 0, health=40, attack=1, defense=50)
    resolve_combat([npc], [monster])
    assert monster.health == 39
    assert npc.health == 99


def test_pair_out_of_range_does_not_fight():
    npc = _Entity(0, 0, health=100, attack=12, defense=4)
    monster = _Entity(1000, 1000, health=40, attack=10, defense=2)
    resolve_combat([npc], [monster])
    assert monster.health == 40
    assert npc.health == 100


def test_monster_at_zero_health_is_removed_but_npc_survives():
    npc = _Entity(0, 0, health=100, attack=100, defense=1000)
    monster = _Entity(10, 0, health=5, attack=1, defense=0)
    npcs, monsters = [npc], [monster]
    resolve_combat(npcs, monsters)
    assert monsters == []
    assert npcs == [npc]


def test_npc_at_zero_health_is_removed():
    npc = _Entity(0, 0, health=5, attack=1, defense=0)
    monster = _Entity(10, 0, health=100, attack=100, defense=1000)
    npcs, monsters = [npc], [monster]
    resolve_combat(npcs, monsters)
    assert npcs == []
    assert monsters == [monster]


def test_tower_attacks_monster_within_range_without_adjacency():
    tower = _Building("Tower", x=0, y=0, attack=15)
    mx, my = tile_center(3, 0)  # 3 tiles out: beyond COMBAT_RANGE, inside TOWER_RANGE
    monster = _Entity(mx, my, health=40, attack=10, defense=2)
    resolve_combat([], [monster], [tower])
    assert monster.health == 40 - (15 - 2)


def test_tower_does_not_attack_monster_outside_its_range():
    tower = _Building("Tower", x=0, y=0, attack=15)
    mx, my = tile_center(10, 0)  # well beyond TOWER_RANGE
    monster = _Entity(mx, my, health=40, attack=10, defense=2)
    resolve_combat([], [monster], [tower])
    assert monster.health == 40


def test_npc_uses_its_own_combat_range_not_the_flat_constant():
    # ticket 12: Mages fight from range; a monster beyond COMBAT_RANGE but
    # within the NPC's own (larger) combat_range should still trade damage.
    mage_range = COMBAT_RANGE * 3
    npc = _Entity(0, 0, health=100, attack=12, defense=4, combat_range=mage_range)
    mx, my = tile_center(2, 0)  # beyond flat COMBAT_RANGE, inside mage_range
    monster = _Entity(mx, my, health=40, attack=10, defense=2)
    resolve_combat([npc], [monster])
    assert monster.health == 40 - (12 - 2)
    assert npc.health == 100 - (10 - 4)


def test_wall_never_attacks_regardless_of_proximity():
    wall = _Building("Wall", x=0, y=0, attack=0)
    mx, my = tile_center(0, 0)  # same tile as the wall - as close as it gets
    monster = _Entity(mx, my, health=40, attack=10, defense=2)
    resolve_combat([], [monster], [wall])
    assert monster.health == 40


def test_life_steal_monster_heals_by_damage_dealt_to_npc():
    npc = _Entity(0, 0, health=100, attack=1, defense=0)
    monster = _Entity(0, 0, health=20, attack=10, defense=1, life_steal=True, max_health=40)
    resolve_combat([npc], [monster])
    dealt_to_npc = 10 - 0  # monster.attack - npc.defense
    dealt_to_monster = max(COMBAT_MIN_DAMAGE, 1 - 1)  # npc.attack - monster.defense, floored
    assert npc.health == 100 - dealt_to_npc
    assert monster.health == 20 - dealt_to_monster + dealt_to_npc  # took damage, healed by what it dealt


def test_life_steal_heal_is_capped_at_max_health():
    npc = _Entity(0, 0, health=100, attack=1, defense=0)
    monster = _Entity(0, 0, health=38, attack=10, defense=1, life_steal=True, max_health=40)
    resolve_combat([npc], [monster])
    assert monster.health == 40  # would overheal to 47+ without the cap


def test_non_life_steal_monster_is_not_healed_by_its_own_damage():
    npc = _Entity(0, 0, health=100, attack=1, defense=0)
    monster = _Entity(0, 0, health=20, attack=10, defense=1, life_steal=False, max_health=40)
    resolve_combat([npc], [monster])
    dealt_to_monster = max(COMBAT_MIN_DAMAGE, 1 - 1)
    assert monster.health == 20 - dealt_to_monster  # only took damage, no heal


def test_life_steal_monster_killed_by_one_npc_cannot_resurrect_off_a_second():
    # A Vampire fighting two NPCs in the same resolve_combat() call: the
    # first NPC's hit is lethal. Without a dead-check inside the loop, the
    # monster would still "fight" the second NPC and life-steal itself back
    # above zero - resurrecting mid-tick. It must stay dead.
    lethal_npc = _Entity(0, 0, health=100, attack=100, defense=0)
    second_npc = _Entity(0, 0, health=100, attack=9, defense=0)
    monster = _Entity(0, 0, health=5, attack=9, defense=0, life_steal=True, max_health=40)
    resolve_combat([lethal_npc, second_npc], [monster])
    assert monster.is_dead
    assert monster.health <= 0


def test_tower_attacks_only_single_closest_target():
    tower = _Building("Tower", x=0, y=0, attack=15)
    mx1, my1 = tile_center(1, 0)  # Close monster (40px)
    mx2, my2 = tile_center(3, 0)  # Far monster in range (120px)
    m1 = _Entity(mx1, my1, health=40, attack=10, defense=2)
    m2 = _Entity(mx2, my2, health=40, attack=10, defense=2)

    resolve_combat([], [m1, m2], [tower])
    # Closer monster took damage, further monster was untouched
    assert m1.health == 40 - (15 - 2)
    assert m2.health == 40


def test_mage_kites_back_when_monster_is_adjacent():
    class _Mage(_Entity):
        def __init__(self, x, y):
            super().__init__(x, y, health=95, attack=22, defense=4, combat_range=120)
            self.role = "Mage"

    mage = _Mage(50.0, 50.0)
    # Monster immediately adjacent (30px away)
    monster = _Entity(50.0, 80.0, health=75, attack=14, defense=2)

    resolve_combat([mage], [monster])
    # Mage nudged backward away from monster
    assert mage.y < 50.0


def test_npc_and_monster_attack_cooldown_delays_consecutive_hits():
    class _Fighter(_Entity):
        def __init__(self, x, y, role=None, mtype=None):
            super().__init__(x, y, health=100, attack=10, defense=0)
            self.role = role
            self.type = mtype
            self.attack_cooldown = 0.0

    knight = _Fighter(0, 0, role="Knight")
    zombie = _Fighter(10, 0, mtype="Zombie")

    # First hit: both are ready, trade 10 damage each
    resolve_combat([knight], [zombie])
    assert knight.health == 90
    assert zombie.health == 90
    assert knight.attack_cooldown == 0.8
    assert zombie.attack_cooldown == 1.3

    # Immediate second resolve without cooldown expiring: no new damage dealt
    resolve_combat([knight], [zombie])
    assert knight.health == 90
    assert zombie.health == 90


def test_tower_attack_cooldown_delays_consecutive_shots():
    tower = _Building("Tower", x=0, y=0, attack=15)
    tower.attack_cooldown = 0.0
    mx, my = tile_center(2, 0)
    monster = _Entity(mx, my, health=100, attack=0, defense=0)

    # First shot hits
    resolve_combat([], [monster], [tower])
    assert monster.health == 85
    assert tower.attack_cooldown == 1.4

    # Second immediate tick while on cooldown does not hit
    resolve_combat([], [monster], [tower])
    assert monster.health == 85
