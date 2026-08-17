import sys
import os
import random
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from combat import resolve_combat
from constants import (
    MONSTER_WEREWOLF,
    MONSTER_VAMPIRE,
    MONSTER_ZOMBIE,
    MONSTER_STATS,
)
from monster import Monster, spawn_monster
from nest import NestManager
from npc import NPC
from grid import Grid


class TestMonsterVarietyStats:
    def test_werewolf_stats(self):
        m = Monster(0, 0, type=MONSTER_WEREWOLF)
        expected = MONSTER_STATS[MONSTER_WEREWOLF]
        assert m.speed == expected["speed"]
        assert m.health == expected["max_health"]
        assert m.attack == expected["attack"]
        assert m.defense == expected["defense"]
        assert not m.life_steal

    def test_vampire_stats(self):
        m = Monster(0, 0, type=MONSTER_VAMPIRE)
        expected = MONSTER_STATS[MONSTER_VAMPIRE]
        assert m.speed == expected["speed"]
        assert m.health == expected["max_health"]
        assert m.attack == expected["attack"]
        assert m.defense == expected["defense"]
        assert m.life_steal

    def test_zombie_stats(self):
        m = Monster(0, 0, type=MONSTER_ZOMBIE)
        expected = MONSTER_STATS[MONSTER_ZOMBIE]
        assert m.speed == expected["speed"]
        assert m.health == expected["max_health"]
        assert m.attack == expected["attack"]
        assert m.defense == expected["defense"]
        assert not m.life_steal


class TestNestManagerMonsterTypeSpawning:
    def test_pick_monster_type_returns_valid_type(self):
        nm = NestManager(60, 45)
        for _ in range(20):
            t = nm.pick_monster_type()
            assert t in (MONSTER_WEREWOLF, MONSTER_VAMPIRE, MONSTER_ZOMBIE)

    def test_spawn_monster_preserves_type(self):
        grid = Grid()
        m = spawn_monster((0, 0), grid, monster_type=MONSTER_ZOMBIE)
        assert m.type == MONSTER_ZOMBIE
        assert m.health == 90


class TestVampireLifeSteal:
    def test_vampire_heals_on_dealing_damage(self):
        # Vampire (ATK 12, DEF 3, Max HP 40)
        vampire = Monster(0, 0, type=MONSTER_VAMPIRE)
        vampire.health = 20  # Damaged initially

        # NPC (ATK 8, DEF 2, HP 100)
        npc = NPC(0, 0)
        npc.attack = 8
        npc.defense = 2
        npc.health = 100

        resolve_combat([npc], [vampire])

        # NPC takes: max(1, 12 - 2) = 10 damage -> HP 90
        assert npc.health == 90
        # Vampire takes: max(1, 8 - 3) = 5 damage
        # Vampire heals: 10 damage dealt -> health was 20 - 5 + 10 = 25
        assert vampire.health == 25

    def test_non_vampire_does_not_life_steal(self):
        werewolf = Monster(0, 0, type=MONSTER_WEREWOLF)
        werewolf.health = 20

        npc = NPC(0, 0)
        npc.attack = 8
        npc.defense = 2
        npc.health = 100

        resolve_combat([npc], [werewolf])
        # Werewolf takes: max(1, 8 - 2) = 6 damage -> health = 14 (no heal)
        assert werewolf.health == 14
