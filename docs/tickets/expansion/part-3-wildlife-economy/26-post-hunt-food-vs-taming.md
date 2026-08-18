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


**Integration note:** this implementation (n97131056's `feat/food-spoilage` stack) was independently built in parallel with my own `feat/wildlife-fauna` (ticket 24) attempt, which is superseded and closed in favor of this one - the Hunt/Taming/Spoilage pipeline needs an id-addressable `Animal` (to track which specific animal was killed/tamed), which this design has and mine didn't. Merged onto `develop` + House (ticket 15) + Farmland (ticket 17), which this branch predated: resolved conflicts in `constants.py` (duplicate stale `ROLES` block dropped), `render_buildings.py` (combined the magenta-unknown-type fallback with AnimalPen/Farmland-ready coloring), `save.py` (buildings now persist both `growth_timer`/`ready` and `assigned_animal_id`; inventory load order preserved so ledger restoration doesn't double-credit shelf life), and `game.py`/`plugins.py`/`world.py` (additive import merges). Full suite green post-merge on the first attempt (218 tests), no logic changes needed beyond the merge itself.

**Code review fixes (post-merge):** `/code-review medium` caught three issues:
1. `FARMER_TAME_WORK_MULTIPLIER` was imported but never applied anywhere - the "speed" half of the "1.5x success rate and speed" spec was dead. Root cause: Tame already goes through task.py's generic `work_seconds * npc.work_multiplier` gate like every task type, and `ROLE_STATS` already gives Farmer a 0.6x `work_multiplier` there - the same mechanism that makes every other Farmer task faster. Wiring in a second Tame-specific multiplier would have double-stacked the bonus (0.6 * 0.67 ≈ 0.4x, a ~2.5x speedup instead of the intended 1.5x). Removed the dead constant instead of wiring it in; added an end-to-end test (`test_farmer_tames_faster_than_other_roles`) proving Farmer finishes a real "Tame" task before Knight does, using the generic mechanism alone.
2. `_can_queue_pen` duplicated `build_task._can_queue`'s body verbatim instead of reusing it like `farmland_task.py` already does (`_can_queue_build_farmland = _can_queue`). Fixed with the same alias pattern.
3. `wildlife.py`'s periodic top-up spawn used bare `random.choice`/a fresh unseeded `random.Random()` per spawn instead of the module's own rng-injection pattern (`create_initial_animals`/`_spawn_animal` both accept an `rng` param specifically for this). Fixed by giving `World` a `wildlife_rng` field (same precedent as `NestManager.rng`), threaded through both the initial population and the periodic top-up; not persisted through `save.py` (same precedent as `NestManager`'s own rng - a reload gets a fresh unseeded generator, matching existing behavior elsewhere in the codebase).
