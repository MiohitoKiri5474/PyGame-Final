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
    MOUNTED_SPEED_BONUS,
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


def _find_available_pen(world: "World") -> "Building | None":
    return next(
        (b for b in getattr(world, "buildings", []) if b.type == "AnimalPen" and getattr(b, "assigned_animal_id", None) is None),
        None,
    )


def idle_spot_near_pen(world: "World", pen_x: int, pen_y: int) -> tuple[float, float]:
    """A tamed animal doesn't sit *in* its pen's tile - it idles on one of
    the 4 cardinal tiles around it, whichever is actually free. Falls back
    to the pen's own tile if all four are blocked."""
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        nx, ny = pen_x + dx, pen_y + dy
        if world.grid.in_bounds(nx, ny) and not any(b.x == nx and b.y == ny for b in world.buildings):
            return tile_center(nx, ny)
    return tile_center(pen_x, pen_y)


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
        animal.tamer_npc_id = getattr(npc, "id", None)

        pen = _find_available_pen(world)
        if pen is not None:
            # A pen exists - walk over and idle beside it instead of vanishing in
            pen.assigned_animal_id = animal.id
            animal.pen_tile = (pen.x, pen.y)
            animal.idle_target = idle_spot_near_pen(world, pen.x, pen.y)
        else:
            # No pen (yet) - taming without one wouldn't otherwise do much,
            # so it defaults to following whoever tamed it
            animal.is_following = True

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

    # If any tamed animal has no pen yet, give this new one to it - whether
    # it's idling in place (walk it over now) or already following its
    # tamer (just bind the tile so "Back to Pen" has somewhere to send it,
    # without interrupting the follow it's currently doing)
    if hasattr(world, "animals"):
        for animal in world.animals:
            if getattr(animal, "is_tamed", False) and getattr(animal, "pen_tile", None) is None:
                pen.assigned_animal_id = animal.id
                animal.pen_tile = (x, y)
                if not animal.is_following:
                    animal.idle_target = idle_spot_near_pen(world, x, y)
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
                # Following pauses its pen output - it's off with its tamer,
                # not doing anything for the pen right now
                if animal is not None and not animal.is_following and animal.species != "Horse":
                    world.inventory.add("meat", 1)

    # Horse travel speed utility: apply speed buff to NPCs if Horse is tamed/penned (not off following)
    has_penned_horse = False
    if hasattr(world, "buildings") and hasattr(world, "animals"):
        for building in world.buildings:
            if building.type == "AnimalPen" and getattr(building, "assigned_animal_id", None) is not None:
                animal = next((a for a in world.animals if a.id == building.assigned_animal_id), None)
                if animal is not None and not animal.is_following and animal.species == "Horse":
                    has_penned_horse = True
                    break

    mounted_rider_ids = {
        a.tamer_npc_id
        for a in getattr(world, "animals", [])
        if getattr(a, "is_mounted", False) and a.tamer_npc_id is not None
    }
    for npc in getattr(world, "npcs", []):
        bonus = HORSE_SPEED_BONUS if has_penned_horse else 0.0
        if npc.id in mounted_rider_ids:
            bonus += MOUNTED_SPEED_BONUS
        npc.speed = npc.base_speed + bonus


register_tick(_tick_pen_production)
