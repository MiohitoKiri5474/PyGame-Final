from combat import resolve_combat


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
