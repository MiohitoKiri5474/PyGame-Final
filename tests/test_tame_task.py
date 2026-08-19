import sys
import os
import random
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from animal import Animal
from build_task import Building
from constants import (
    BASE_TAME_SUCCESS_RATE,
    FARMER_TAME_SUCCESS_MULTIPLIER,
    HORSE_SPEED_BONUS,
    PEN_PRODUCTION_INTERVAL,
    ROLE_FARMER,
    ROLE_KNIGHT,
    TAME_WORK_SECONDS,
)
from coords import tile_center
from npc import NPC
from tame_task import (
    can_queue_tame,
    can_perform_tame,
    on_complete_tame,
    process_animal_for_food,
    _tick_pen_production,
)
from task import Task, update_npc_tasks
from world import World


class TestProcessAnimalForFood:
    def test_process_wild_boar_credits_meat_and_removes_animal(self):
        world = World()
        boar = Animal(*tile_center(10, 10), species="WildBoar", speed=70.0, dangerous=False, health=30)
        world.animals.append(boar)

        initial_meat = world.inventory.get("meat")
        meat_gained = process_animal_for_food(world, boar)

        assert meat_gained == 3
        assert world.inventory.get("meat") == initial_meat + 3
        assert boar not in world.animals

    def test_process_bear_credits_five_meat(self):
        world = World()
        bear = Animal(*tile_center(10, 10), species="Bear", speed=50.0, dangerous=True, health=60)
        world.animals.append(bear)

        meat_gained = process_animal_for_food(world, bear)
        assert meat_gained == 5
        assert bear not in world.animals


class TestTameTask:
    def test_can_queue_tame_true_for_untamed_animal(self):
        world = World()
        animal = Animal(*tile_center(10, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        assert can_queue_tame(world, (10, 10))

    def test_can_queue_tame_false_for_already_tamed_animal(self):
        world = World()
        animal = Animal(*tile_center(10, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        animal.is_tamed = True
        world.animals.append(animal)

        assert not can_queue_tame(world, (10, 10))

    def test_farmer_tame_success_rate_bonus(self):
        world = World()
        animal = Animal(*tile_center(10, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        farmer = NPC(*tile_center(10, 10))
        farmer.role = ROLE_FARMER
        task = Task(type="Tame", target=(10, 10), assigned_npc=farmer, target_animal_id=animal.id)

        # RNG returning 0.6: fails for base 0.50, but succeeds for Farmer (0.50 * 1.5 = 0.75)
        class FixedRNG:
            def random(self):
                return 0.60

        on_complete_tame(world, task, rng=FixedRNG())
        assert animal.is_tamed

    def test_non_farmer_fails_above_base_success_rate(self):
        world = World()
        animal = Animal(*tile_center(10, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        knight = NPC(*tile_center(10, 10))
        knight.role = ROLE_KNIGHT
        task = Task(type="Tame", target=(10, 10), assigned_npc=knight, target_animal_id=animal.id)

        class FixedRNG:
            def random(self):
                return 0.60

        on_complete_tame(world, task, rng=FixedRNG())
        assert not animal.is_tamed

    def test_tamed_animal_places_in_available_pen(self):
        world = World()
        pen = Building(type="AnimalPen", x=5, y=5, block=20, attack=0)
        world.buildings.append(pen)

        animal = Animal(*tile_center(10, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        npc = NPC(*tile_center(10, 10))
        task = Task(type="Tame", target=(10, 10), assigned_npc=npc, target_animal_id=animal.id)

        class AlwaysSuccessRNG:
            def random(self):
                return 0.0

        on_complete_tame(world, task, rng=AlwaysSuccessRNG())
        assert animal.is_tamed
        assert pen.assigned_animal_id == animal.id
        assert animal.pen_tile == (5, 5)

    def test_tamed_animal_waits_if_no_pen_available(self):
        world = World()  # No pens
        animal = Animal(*tile_center(10, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        npc = NPC(*tile_center(10, 10))
        task = Task(type="Tame", target=(10, 10), assigned_npc=npc, target_animal_id=animal.id)

        class AlwaysSuccessRNG:
            def random(self):
                return 0.0

        on_complete_tame(world, task, rng=AlwaysSuccessRNG())
        assert animal.is_tamed
        assert animal.pen_tile is None
        assert animal in world.animals  # Does not vanish!

    def test_farmer_tames_faster_than_other_roles(self):
        # Ticket 26's "1.5x success rate and speed vs. other roles" speed
        # half needs no Tame-specific multiplier: Tame goes through task.py's
        # generic work_seconds * npc.work_multiplier gate like every task,
        # and ROLE_STATS already gives Farmer 0.6x there. This locks that in
        # end-to-end using the real registered "Tame" task type.
        def _setup(role):
            world = World(npc_count=0)
            cx, cy = world.grid.width // 2, world.grid.height // 2
            world.grid.get(cx, cy).claimed = True
            animal = Animal(*tile_center(cx, cy), species="Horse", speed=140.0, dangerous=False, health=40)
            world.animals.append(animal)
            npc = NPC(*tile_center(cx, cy), role=role)
            world.npcs.append(npc)
            world.tasks.add("Tame", (cx, cy))
            return world, npc

        farmer_world, farmer = _setup(ROLE_FARMER)
        knight_world, knight = _setup(ROLE_KNIGHT)

        # Between Farmer's effective work time (TAME_WORK_SECONDS * 0.6) and
        # Knight's (TAME_WORK_SECONDS * 1.0): enough for Farmer to finish,
        # not enough for Knight.
        ticks = int(TAME_WORK_SECONDS * 0.8 * 60)
        for _ in range(ticks):
            update_npc_tasks(farmer_world, 1 / 60)
            update_npc_tasks(knight_world, 1 / 60)

        assert farmer.task is None  # finished already, thanks to the 0.6x multiplier
        assert knight.task is not None  # still working


class TestTameRepathing:
    def test_npc_binds_animal_id_and_repaths_when_animal_moves_out_of_range(self):
        # Tame previously never bound target_animal_id at claim time (only
        # Hunt did), so a wandering animal would silently desync from the
        # stale target tile with no chase logic to recover - this covers
        # the same claim-and-chase path Hunt already had, now shared by Tame.
        world = World(npc_count=1)
        animal = Animal(*tile_center(12, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        task = world.tasks.add("Tame", (12, 10))
        npc = world.npcs[0]
        npc.x, npc.y = tile_center(10, 10)

        update_npc_tasks(world, 0.1)
        assert npc.task is task
        assert task.target_animal_id == animal.id

        animal.x, animal.y = tile_center(16, 10)
        animal.path = []
        npc.x, npc.y = tile_center(12, 10)
        npc.path = []

        update_npc_tasks(world, 0.1)
        assert npc.task.target == (16, 10)
        assert len(npc.path) > 0

    def test_npc_holds_position_and_works_once_in_range(self):
        world = World(npc_count=1)
        animal = Animal(*tile_center(11, 10), species="Horse", speed=140.0, dangerous=False, health=40)
        world.animals.append(animal)

        task = world.tasks.add("Tame", (11, 10), target_animal_id=animal.id)
        npc = world.npcs[0]
        npc.x, npc.y = tile_center(10, 10)
        npc.path = []
        npc.task = task
        task.assigned_npc = npc

        update_npc_tasks(world, 0.1)
        assert npc.path == []
        assert npc.task_progress > 0


class TestAnimalPenProductionAndHorseBuff:
    def test_penned_animal_produces_meat_periodically(self):
        world = World()
        pen = Building(type="AnimalPen", x=5, y=5, block=20, attack=0)
        world.buildings.append(pen)

        boar = Animal(*tile_center(5, 5), species="WildBoar", speed=70.0, dangerous=False, health=30)
        boar.is_tamed = True
        boar.pen_tile = (5, 5)
        pen.assigned_animal_id = boar.id
        world.animals.append(boar)

        initial_meat = world.inventory.get("meat")
        # Tick elapsed >= PEN_PRODUCTION_INTERVAL
        _tick_pen_production(world, PEN_PRODUCTION_INTERVAL)

        assert world.inventory.get("meat") == initial_meat + 1

    def test_penned_horse_grants_travel_speed_bonus(self):
        world = World()
        pen = Building(type="AnimalPen", x=5, y=5, block=20, attack=0)
        world.buildings.append(pen)

        horse = Animal(*tile_center(5, 5), species="Horse", speed=140.0, dangerous=False, health=40)
        horse.is_tamed = True
        horse.pen_tile = (5, 5)
        pen.assigned_animal_id = horse.id
        world.animals.append(horse)

        npc = NPC(0, 0, speed=120.0)
        world.npcs = [npc]

        _tick_pen_production(world, 0.1)
        assert npc.speed == 120.0 + HORSE_SPEED_BONUS
