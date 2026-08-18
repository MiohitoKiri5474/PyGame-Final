# 17 — Farmland building (plant → grow → harvest cycle)

**What to build:** Farmland places like Wall/Tower/House but carries growth state instead of being a one-shot building. Once built it grows on a fixed timer (ticked via the new per-tick hook); once ready, the player queues a Harvest task the same way Gather is queued by click. Harvesting credits crops and restarts the growth timer automatically — no replant step.

**Blocked by:** 13 — Per-tick simulation hook, 14 — Expanded material taxonomy.

**Status:** done

- [x] `BuildFarmland` registered via the standard Build-task flow (same `can_queue` shape as Wall/Tower/House)
- [x] `Building` gains `growth_timer: float = 0.0, ready: bool = False` — no-op defaults for Wall/Tower/House, only meaningful for Farmland
- [x] Growth timer advances every tick via `extensions.register_tick`, flips `ready = True` at a named threshold constant
- [x] New `HarvestFarmland` task type only queueable when the target Farmland's `ready` is `True`; completion credits the crop yield and resets `growth_timer`/`ready` to restart the cycle
- [x] `save.py`'s building dict round-trips `growth_timer`/`ready`, including a mid-growth (not-yet-ready) Farmland
- [x] Unit tests: growth timing to ready, harvest resets and the cycle repeats, Harvest not queueable pre-ready

**Implementation notes:** `BuildFarmland` reuses `build_task.py`'s `_can_queue`/`_try_build` directly (unchanged — works as-is since `Building`'s two new fields default correctly for a fresh build). `_tick_farmland_growth` is registered via ticket 13's `extensions.register_tick`, iterating `world.buildings` and advancing only `type == "Farmland" and not ready` entries.

`HarvestFarmland`'s `_find_farmland` looks up its target by tile coordinates, not object identity — this was a deliberate simplification, but `/code-review medium` caught a real exploit in the first pass: `HarvestFarmland` originally had no `can_perform` (mirroring `gather_task.py`'s "already-gone is a no-op" pattern), which meant a stale queued Harvest task survived a destroy-then-rebuild-on-the-same-tile race and could credit crop yield from a brand-new, not-yet-ready Farmland that just happened to share the old one's coordinates. Unlike a gathered wild-resource tile (which can never get a *new distinct* resource at the same coordinates — `tile.resource = None` is permanent), a Farmland can be destroyed and rebuilt, so coordinate-based identity isn't safe here the way it is for Gather. Fixed by adding back `can_perform` (`_can_perform_harvest`, re-verifying `farmland is not None and farmland.ready` every tick, not just at completion) — the original "no can_perform" instinct optimized for the wrong failure mode: closing the "orphaned task lingers unclaimed forever" cosmetic issue (a pre-existing task-engine limitation, not this ticket's to fix — same class flagged in ticket 11's notes) at the cost of an actual resource-duplication exploit. `_on_complete_harvest`'s "already gone" no-op guard is kept as defense-in-depth but should now be unreachable in practice, since `can_perform` gates every claim and every in-progress tick before it.

New extension point: `build_task.register_build_cost(task_type, cost)` — lets `farmland_task.py` (and later ticket 26's Animal Pen) register into the existing blocked-builds HUD line without `build_task.py` needing to import every future building type's cost constant directly.

Cost/timing (no exact numbers in `game-detail.md`, used `todo.md`'s Farmland spec plus reasonable judgment): `{"wood": 2, "crop": 1}` (todo.md says "2 Wood + 1 Water/Crop" — no water resource exists in this game, used crop), 3.0s build, 20.0s grow-to-ready, yield 3 crop per harvest (vs. Gather's yield of 1, reflecting the up-front build investment), 2.0s harvest work (matches Gather's work time).

Known temporary artifact: this branch was cut before ticket 15 (House) merged, so it couldn't import ticket 15's `_can_afford` refactor — `_can_perform_build_farmland` inlines the same afford-check `_can_perform_wall`/`_can_perform_tower` had before that refactor. Once both land on `develop`, a trivial follow-up could switch this to call `_can_afford` too; not worth blocking on.
