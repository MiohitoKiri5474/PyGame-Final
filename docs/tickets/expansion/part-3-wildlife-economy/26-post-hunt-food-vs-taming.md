# 26 — Post-hunt: food vs. taming

**What to build:** After a Hunt kill, the player chooses between "Process for Food" (credits meat to the colony inventory) and "Tame" (a Farmer attempts to tame the animal at 1.5x success rate and speed vs. other roles; a tamed animal is placed in a new Animal Pen building for passive production — Horse grants a travel-speed utility as the simplest viable form, not milk/eggs/meat).

**Blocked by:** 25 — Hunt task, 15 — House & population cap (Animal Pen reuses the same build-task pattern). Soft dependency on 23 — Skill Upgrade UI (the Taming Ability skill boosts this further, but base taming works without it).

**Status:** done

- [x] New `tame_task.py`: `Tame` task type, plus a new Animal Pen building registered via the standard build-task pattern
- [x] "Process for Food" credits meat to inventory and removes the animal (`process_animal_for_food`)
- [x] "Tame" success rate is 1.5x for Farmer NPCs vs. other roles (`BASE_TAME_SUCCESS_RATE`, `FARMER_TAME_SUCCESS_MULTIPLIER`)
- [x] A tamed-but-not-yet-penned animal doesn't crash or silently vanish — it stays in colony waiting until an Animal Pen is built
- [x] Penned Horse provides travel-speed utility effect (`HORSE_SPEED_BONUS`) for colony NPCs
- [x] Pen production for penned animals ticks via `extensions.register_tick` (`_tick_pen_production`)
- [x] `save.py` persists tamed animals, pen occupancy, and production timer
- [x] Unit tests: food-credit path, tame success-rate math by role, pen production tick

**Implementation notes:**
- Created `src/tame_task.py` with `process_animal_for_food`, `Tame` task, `BuildAnimalPen` task, and `_tick_pen_production`.
- Updated `src/animal.py` with `is_tamed` and `pen_tile`.
- Updated `src/render_buildings.py` to render `AnimalPen`.
- Updated `src/save.py` to serialize `is_tamed`, `pen_tile`, `assigned_animal_id`, and `pen_production_timer`.
- Comprehensive unit tests in `tests/test_tame_task.py`.

