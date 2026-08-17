from combat import resolve_combat
from coords import tile_center


class _Building:
    def __init__(self, type_: str, x: int, y: int, attack: int):
        self.type = type_
        self.x = x
        self.y = y
        self.attack = attack


class _Entity:
    def __init__(self, x: float, y: float, health: int, attack: int, defense: int):
        self.x = x
        self.y = y
        self.health = health
        self.attack = attack
        self.defense = defense

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


def test_wall_never_attacks_regardless_of_proximity():
    wall = _Building("Wall", x=0, y=0, attack=0)
    mx, my = tile_center(0, 0)  # same tile as the wall - as close as it gets
    monster = _Entity(mx, my, health=40, attack=10, defense=2)
    resolve_combat([], [monster], [wall])
    assert monster.health == 40
