# 18 — Magic framework + Lightning spell

**What to build:** Colony-wide spell casting: hotkey-castable whenever the spell is off-cooldown and a living Mage exists, regardless of that Mage's position, auto-targeting the nearest monster to territory. This ticket establishes cooldown tracking, the targeting helper, HUD cooldown display, and VFX flash — reused by Fire (19) and Freeze (20). Lightning itself: `W`, instant burst damage, 20s cooldown.

**Blocked by:** 13 — Per-tick simulation hook, 12 — NPC Role System (casting requires a living Mage).

**Status:** done

- [x] New `magic.py` (pygame-free): spellbook/cooldown state, `nearest_monster_to_territory(world, monsters)` helper, `cast_lightning(world, monsters)`
- [x] `F2` (reassigned from W per user design choice to prevent camera pan conflict) casts Lightning if off-cooldown, at least one living Mage exists, and at least one monster exists — silent no-op otherwise (no error, no wasted cooldown)
- [x] Successful cast damages the nearest monster to territory and starts a 20s cooldown, ticked down via `extensions.register_tick`
- [x] Cooldown remaining is visible on the HUD (`extensions.register_hud_line`)
- [x] New `render_magic.py` (pygame-coupled, registered via `extensions.register_overlay`) draws a brief VFX flash on cast
- [x] `save.py` round-trips in-progress cooldown
- [x] Unit tests: on-cooldown cast is a no-op, no-Mage cast is a no-op, nearest-target selection is correct, cooldown decrements and gates correctly

**Implementation notes:**
- Created `src/magic.py` with `Spellbook` and `cast_lightning`.
- Created `src/render_magic.py` registering tick, HUD line, and VFX overlay.
- Added comprehensive unit tests in `tests/test_magic.py`.

