"""Post-Hunt: Food processing, Taming task, and Animal Pen building (ticket 26).

- process_animal_for_food: credits meat to inventory and removes animal.
- Tame task: Farmer gets a 1.5x success-rate bonus; tamed animals are placed in Animal Pens.
  The "and speed" half of the ticket's bonus needs no Tame-specific code: Tame goes through
  task.py's generic work_seconds * npc.work_multiplier gate like every other task type, and
  ROLE_STATS already gives Farmer a 0.6x work_multiplier applied there - the same mechanism
  that makes every other Farmer task faster than a Knight/Mage's already covers Tame, so a
  second Tame-only multiplier would double-stack the bonus rather than deliver it once.
- Animal Pen building: passive production for penned animals + Horse travel-speed utility for colony.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from build_task import Building, _can_queue, _displace_npcs_from_wall, register_build_cost
from constants import (
    ANIMAL_MEAT_YIELD,
    ANIMAL_PEN_ATTACK,
    ANIMAL_PEN_BLOCK,
    ANIMAL_PEN_COST,
    ANIMAL_PEN_WORK_SECONDS,
    BASE_TAME_SUCCESS_RATE,
    FARMER_TAME_SUCCESS_MULTIPLIER,
    HORSE_SPEED_BONUS,
    PEN_PRODUCTION_INTERVAL,
    ROLE_FARMER,
    TAME_WORK_SECONDS,
)
from coords import tile_at, tile_center
from extensions import register_tick
from skills import taming_success_bonus
from task import register_task_type, resolve_task_animal, Task, TaskType

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
    animal = resolve_task_animal(world, task)
    return animal is not None and not getattr(animal, "is_tamed", False)


def on_complete_tame(world: "World", task: "Task", rng: random.Random | None = None) -> bool:
    """Resolve taming attempt on the target animal."""
    rng = rng or random.Random()
    animal = resolve_task_animal(world, task)

    if animal is None or animal.is_dead:
        return True

    npc = task.assigned_npc
    is_farmer = (getattr(npc, "role", None) == ROLE_FARMER)

    # Farmer gets 1.5x success rate bonus, plus a flat Taming Ability bonus (ticket 23)
    success_rate = BASE_TAME_SUCCESS_RATE
    if is_farmer:
        success_rate *= FARMER_TAME_SUCCESS_MULTIPLIER
    success_rate = min(1.0, success_rate + taming_success_bonus(world))

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

# Same claimed-empty-resource-free rule as Wall/Tower/House/Farmland - reuse
# build_task's rule directly so a future change to it doesn't silently miss
# Animal Pen (same pattern farmland_task.py already established).
_can_queue_pen = _can_queue


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

register_build_cost("BuildAnimalPen", ANIMAL_PEN_COST)


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
