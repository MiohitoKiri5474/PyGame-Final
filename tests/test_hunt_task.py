import sys
import os
import random
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from animal import Animal
from constants import (
    ROLE_KNIGHT,
    ROLE_FARMER,
    KNIGHT_CRIT_MULTIPLIER,
    HUNT_WORK_SECONDS,
)
from coords import tile_center
from hunt_task import can_queue_hunt, can_perform_hunt, on_complete_hunt
from npc import NPC
from task import Task, TaskQueue, update_npc_tasks
from world import World


class TestHuntQueueing:
    def test_can_queue_hunt_true_when_living_animal_present(self):
        world = World(animal_count=0)  # World() also seeds random wildlife - keep only this test's own animal(s)
        animal = Animal(*tile_center(10, 10), species="WildBoar", speed=70.0, dangerous=False, health=30)
        world.animals.append(animal)

        assert can_queue_hunt(world, (10, 10))

    def test_can_queue_hunt_false_when_no_animal_on_tile(self):
        world = World(animal_count=0)  # World() also seeds random wildlife - keep only this test's own animal(s)
        assert not can_queue_hunt(world, (10, 10))

    def test_can_queue_hunt_false_when_animal_is_dead(self):
        world = World(animal_count=0)  # World() also seeds random wildlife - keep only this test's own animal(s)
        animal = Animal(*tile_center(10, 10), species="WildBoar", speed=70.0, dangerous=False, health=0)
        world.animals.append(animal)

        assert not can_queue_hunt(world, (10, 10))


class TestHuntRepathing:
    def test_npc_repaths_when_animal_moves_out_of_combat_range(self):
        world = World(npc_count=1, animal_count=0)
        # Position animal at (12, 10) initially
        animal = Animal(*tile_center(12, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        # Queue hunt task targeting (12, 10)
        task = world.tasks.add("Hunt", (12, 10), target_animal_id=animal.id)
        npc = world.npcs[0]
        npc.x, npc.y = tile_center(10, 10)

        # NPC claims task and begins walking
        update_npc_tasks(world, 0.1)
        assert npc.task is task

        # Animal hops well beyond the NPC's combat_range (adjacent-tile range)
        animal.x, animal.y = tile_center(16, 10)
        animal.path = []

        # NPC reaches (12, 10)
        npc.x, npc.y = tile_center(12, 10)
        npc.path = []

        # Tick: NPC should detect it's out of range and re-path toward (16, 10)
        update_npc_tasks(world, 0.1)
        assert npc.task.target == (16, 10)
        assert len(npc.path) > 0  # Re-pathed toward (16, 10)

    def test_npc_holds_position_and_works_once_in_range(self):
        world = World(npc_count=1, animal_count=0)
        # Animal one tile away - within the default NPC's combat_range
        animal = Animal(*tile_center(11, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        task = world.tasks.add("Hunt", (11, 10), target_animal_id=animal.id)
        npc = world.npcs[0]
        npc.x, npc.y = tile_center(10, 10)
        npc.path = []
        npc.task = task
        task.assigned_npc = npc

        update_npc_tasks(world, 0.1)
        assert npc.path == []  # holds position instead of walking onto the animal's tile
        assert npc.task_progress > 0  # work actually accumulated this tick

    def test_progress_pauses_instead_of_resetting_when_animal_leaves_range(self):
        world = World(npc_count=1, animal_count=0)
        animal = Animal(*tile_center(11, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        task = world.tasks.add("Hunt", (11, 10), target_animal_id=animal.id)
        npc = world.npcs[0]
        npc.x, npc.y = tile_center(10, 10)
        npc.path = []
        npc.task = task
        npc.task_progress = 0.5
        task.assigned_npc = npc

        # Animal hops far away this same tick
        animal.x, animal.y = tile_center(16, 10)
        animal.path = []

        update_npc_tasks(world, 0.1)
        assert npc.task_progress == 0.5  # unchanged, not wiped back to 0


class TestHuntCombatAndKnightBonus:
    def test_regular_npc_deals_base_attack_damage(self):
        world = World(animal_count=0)  # World() also seeds random wildlife - keep only this test's own animal(s)
        animal = Animal(*tile_center(10, 10), species="Bear", speed=50.0, dangerous=True, health=60)
        world.animals.append(animal)

        npc = NPC(*tile_center(10, 10))
        npc.attack = 10
        npc.role = ROLE_FARMER
        task = Task(type="Hunt", target=(10, 10), assigned_npc=npc, target_animal_id=animal.id)

        # Complete one hunt strike
        finished = on_complete_hunt(world, task)
        assert animal.health == 50  # 60 - 10
        assert not finished  # Still alive

    def test_knight_gets_crit_bonus(self):
        world = World(animal_count=0)  # World() also seeds random wildlife - keep only this test's own animal(s)
        animal = Animal(*tile_center(10, 10), species="Bear", speed=50.0, dangerous=True, health=60)
        world.animals.append(animal)

        npc = NPC(*tile_center(10, 10))
        npc.attack = 10
        npc.role = ROLE_KNIGHT
        task = Task(type="Hunt", target=(10, 10), assigned_npc=npc, target_animal_id=animal.id)

        # Mock rng to guarantee crit (rng.random() returns 0.0)
        rng = random.Random(42)
        # Force crit by using rng where random() < KNIGHT_CRIT_CHANCE
        class AlwaysCritRNG:
            def random(self):
                return 0.0

        on_complete_hunt(world, task, rng=AlwaysCritRNG())
        assert animal.health == 60 - (10 * KNIGHT_CRIT_MULTIPLIER)

    def test_dangerous_animal_retaliates_against_npc(self):
        world = World(animal_count=0)  # World() also seeds random wildlife - keep only this test's own animal(s)
        animal = Animal(*tile_center(10, 10), species="Wolf", speed=90.0, dangerous=True, health=35)
        world.animals.append(animal)

        npc = NPC(*tile_center(10, 10))
        npc.attack = 10
        npc.defense = 2
        npc.health = 100
        task = Task(type="Hunt", target=(10, 10), assigned_npc=npc, target_animal_id=animal.id)

        on_complete_hunt(world, task)
        assert animal.is_hostile
        # Wolf attack is 10, NPC defense is 2 -> NPC takes max(1, 10 - 2) = 8 dmg
        assert npc.health == 92


class TestHuntCompletion:
    def test_animal_death_removes_animal_and_completes_task(self):
        world = World(animal_count=0)  # World() also seeds random wildlife - keep only this test's own animal(s)
        animal = Animal(*tile_center(10, 10), species="FlyingSquirrel", speed=100.0, dangerous=False, health=5)
        world.animals.append(animal)

        npc = NPC(*tile_center(10, 10))
        npc.attack = 10
        task = world.tasks.add("Hunt", (10, 10), target_animal_id=animal.id)
        task.assigned_npc = npc
        npc.task = task

        finished = on_complete_hunt(world, task)
        assert finished
        assert animal not in world.animals
        assert animal.is_dead
