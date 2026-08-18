"""Post-Hunt: Food processing, Taming task, and Animal Pen building (ticket 26).

- process_animal_for_food: credits meat to inventory and removes animal.
- Tame task: Farmer gets 1.5x success rate and speed bonus; tamed animals are placed in Animal Pens.
- Animal Pen building: passive production for penned animals + Horse travel-speed utility for colony.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from build_task import Building, _displace_npcs_from_wall
from constants import (
    ANIMAL_MEAT_YIELD,
    ANIMAL_PEN_ATTACK,
    ANIMAL_PEN_BLOCK,
    ANIMAL_PEN_COST,
    ANIMAL_PEN_WORK_SECONDS,
    BASE_TAME_SUCCESS_RATE,
    FARMER_TAME_SUCCESS_MULTIPLIER,
    FARMER_TAME_WORK_MULTIPLIER,
    HORSE_SPEED_BONUS,
    PEN_PRODUCTION_INTERVAL,
    ROLE_FARMER,
    TAME_WORK_SECONDS,
)
from coords import tile_at, tile_center
from extensions import register_tick
from task import register_task_type, Task, TaskType

if TYPE_CHECKING:
    from animal import Animal
    from world import World


def process_animal_for_food(world: "World", animal: "Animal") -> int:
    """Credit meat to inventory based on animal species and remove the animal."""
    yield_amount = ANIMAL_MEAT_YIELD.get(animal.species, 1)
    world.inventory.add("meat", yield_amount)
    if hasattr(world, "animals") and animal in world.animals:
        world.animals.remove(animal)
    return yield_amount


# ── Tame Task ─────────────────────────────────────────────────────────────

def can_queue_tame(world: "World", tile: tuple[int, int]) -> bool:
    """Can only queue Tame on a tile with a living, untamed animal."""
    if not hasattr(world, "animals"):
        return False
    return any(tile_at(a.x, a.y) == tile and not a.is_dead and not getattr(a, "is_tamed", False) for a in world.animals)


def can_perform_tame(world: "World", task: "Task") -> bool:
    """Can perform Tame if target animal still exists, is alive and untamed."""
    if not hasattr(world, "animals"):
        return False
    if task.target_animal_id is not None:
        return any(a.id == task.target_animal_id and not a.is_dead and not getattr(a, "is_tamed", False) for a in world.animals)
    return any(tile_at(a.x, a.y) == task.target and not a.is_dead and not getattr(a, "is_tamed", False) for a in world.animals)


def on_complete_tame(world: "World", task: "Task", rng: random.Random | None = None) -> bool:
    """Resolve taming attempt on the target animal."""
    if not hasattr(world, "animals"):
        return True

    rng = rng or random.Random()
    animal = None
    if task.target_animal_id is not None:
        animal = next((a for a in world.animals if a.id == task.target_animal_id), None)
    if animal is None:
        animal = next((a for a in world.animals if tile_at(a.x, a.y) == task.target and not a.is_dead), None)

    if animal is None or animal.is_dead:
        return True

    npc = task.assigned_npc
    is_farmer = (getattr(npc, "role", None) == ROLE_FARMER)

    # Farmer gets 1.5x success rate bonus
    success_rate = BASE_TAME_SUCCESS_RATE
    if is_farmer:
        success_rate = min(1.0, success_rate * FARMER_TAME_SUCCESS_MULTIPLIER)

    if rng.random() < success_rate:
        animal.is_tamed = True
        # Try to assign to an available Animal Pen
        for building in getattr(world, "buildings", []):
            if building.type == "AnimalPen" and getattr(building, "assigned_animal_id", None) is None:
                building.assigned_animal_id = animal.id
                animal.pen_tile = (building.x, building.y)
                animal.x, animal.y = tile_center(building.x, building.y)
                animal.set_path([])
                break

    return True


register_task_type(
    "Tame",
    TaskType(
        work_seconds=TAME_WORK_SECONDS,
        can_queue=can_queue_tame,
        on_complete=on_complete_tame,
        can_perform=can_perform_tame,
    ),
)


# ── Animal Pen Building ───────────────────────────────────────────────────

def _can_queue_pen(world: "World", tile: tuple[int, int]) -> bool:
    x, y = tile
    t = world.grid.get(x, y)
    if not t.claimed or t.resource is not None:
        return False
    if any(b.x == x and b.y == y for b in world.buildings):
        return False
    if any(task.type.startswith("Build") and task.target == tile for task in world.tasks.tasks):
        return False
    return True


def _can_perform_pen(world: "World", task: Task) -> bool:
    return all(world.inventory.get(res) >= amt for res, amt in ANIMAL_PEN_COST.items())


def _on_complete_pen(world: "World", task: Task) -> bool:
    if not world.inventory.spend_all(ANIMAL_PEN_COST):
        return False

    x, y = task.target
    pen = Building(type="AnimalPen", x=x, y=y, block=ANIMAL_PEN_BLOCK, attack=ANIMAL_PEN_ATTACK)
    pen.assigned_animal_id = None
    world.buildings.append(pen)

    # If any tamed animal is currently waiting for a pen, place it here
    if hasattr(world, "animals"):
        for animal in world.animals:
            if getattr(animal, "is_tamed", False) and getattr(animal, "pen_tile", None) is None:
                pen.assigned_animal_id = animal.id
                animal.pen_tile = (x, y)
                animal.x, animal.y = tile_center(x, y)
                animal.set_path([])
                break

    return True


register_task_type(
    "BuildAnimalPen",
    TaskType(
        work_seconds=ANIMAL_PEN_WORK_SECONDS,
        can_queue=_can_queue_pen,
        on_complete=_on_complete_pen,
        can_perform=_can_perform_pen,
    ),
)


# ── Pen Production & Horse Buff Tick Hook ────────────────────────────────

def _tick_pen_production(world: "World", dt: float) -> None:
    if not hasattr(world, "pen_production_timer"):
        world.pen_production_timer = 0.0

    world.pen_production_timer += dt
    if world.pen_production_timer >= PEN_PRODUCTION_INTERVAL:
        world.pen_production_timer = 0.0
        for building in getattr(world, "buildings", []):
            if building.type == "AnimalPen" and getattr(building, "assigned_animal_id", None) is not None:
                animal = next((a for a in getattr(world, "animals", []) if a.id == building.assigned_animal_id), None)
                if animal is not None and animal.species != "Horse":
                    world.inventory.add("meat", 1)

    # Horse travel speed utility: apply speed buff to NPCs if Horse is tamed/penned
    has_penned_horse = False
    if hasattr(world, "buildings") and hasattr(world, "animals"):
        for building in world.buildings:
            if building.type == "AnimalPen" and getattr(building, "assigned_animal_id", None) is not None:
                animal = next((a for a in world.animals if a.id == building.assigned_animal_id), None)
                if animal is not None and animal.species == "Horse":
                    has_penned_horse = True
                    break

    for npc in getattr(world, "npcs", []):
        if not hasattr(npc, "base_speed"):
            npc.base_speed = npc.speed
        npc.speed = npc.base_speed + (HORSE_SPEED_BONUS if has_penned_horse else 0.0)


register_tick(_tick_pen_production)
