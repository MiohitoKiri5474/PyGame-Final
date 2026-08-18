# 18 — Magic framework + Lightning spell

**What to build:** Colony-wide spell casting: hotkey-castable whenever the spell is off-cooldown and a living Mage exists, regardless of that Mage's position, auto-targeting the nearest monster to territory. This ticket establishes cooldown tracking, the targeting helper, HUD cooldown display, and VFX flash — reused by Fire (19) and Freeze (20). Lightning itself: `F2`, instant burst damage, 20s cooldown.

**Blocked by:** 13 — Per-tick simulation hook, 12 — NPC Role System (casting requires a living Mage).

**Status:** done

- [x] New `magic.py` (pygame-free): spellbook/cooldown state, `nearest_monster_to_territory(world, monsters)` helper, `cast_lightning(world, monsters)`
- [x] `F2` casts Lightning if off-cooldown, at least one living Mage exists, and at least one monster exists — silent no-op otherwise (no error, no wasted cooldown)
- [x] Successful cast damages the nearest monster to territory and starts a 20s cooldown, ticked down via `extensions.register_tick`
- [x] Cooldown remaining is visible on the HUD (`extensions.register_hud_line`)
- [x] New `render_magic.py` (pygame-coupled, registered via `extensions.register_overlay`) draws a brief VFX flash on cast
- [x] `save.py` round-trips in-progress cooldown
- [x] Unit tests: on-cooldown cast is a no-op, no-Mage cast is a no-op, nearest-target selection is correct, cooldown decrements and gates correctly

**Implementation notes:** `Spellbook` (cooldowns dict + transient flash state) lives on `world.spellbook`, not `Game` — `extensions.register_tick` callbacks only receive `(world, dt)`, so cooldown state has to be reachable from `world` to tick via that hook; colony-wide magic state is also simulation state like everything else `World` already owns (npcs/buildings/animals/inventory). `nearest_monster_to_territory` reuses `monster.py`'s existing `nearest_claimed_tile` (used since ticket 06/07 for monster spawn pathing) rather than writing a new grid-scan — computes, for each monster, Manhattan distance to its own nearest claimed tile, returns the monster with the smallest distance ("closest to invading," matching CLAUDE.md's "auto-targets nearest threat" language). `magic.py` self-registers its tick (`_tick_magic`) and HUD line (`_magic_hud_line`); `render_magic.py` is the separate pygame-coupled VFX module the ticket calls for, keeping `magic.py` itself on the pygame-free side of the test seam.

Flash VFX state (`flash_position`/`flash_timer`) is deliberately NOT persisted through `save.py` — same scope call as camera/selection/pause state from ticket 11: a mid-animation flash has no meaningful "resume" state, it just won't be showing at the moment of a reload, which is fine.

**Superseded design note:** the original implementation bound Lightning/Fire/Freeze to `W`/`Q`/`E`, which collided with the `W` camera-pan-up binding (harmless — gated by cooldown/no-Mage/no-monster same as any no-op cast — but non-obvious). Rebound to `F2`/`F1`/`F3` during the ticket 18-21 reconciliation with a teammate's parallel `feat/combat-depth` branch, which avoided the collision entirely by using function keys. No overlap with any existing binding remains.
