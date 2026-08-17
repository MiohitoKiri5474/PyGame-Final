# 19 — Fire spell

**What to build:** `Q`, 15s cooldown, deals immediate damage to the nearest monster to territory plus a 3-second burn damage-over-time.

**Blocked by:** 18 — Magic framework + Lightning spell.

**Status:** done

- [x] `cast_fire` in `magic.py` reuses the cast/cooldown/targeting scaffolding from ticket 18 (no duplicated cooldown-tracking logic)
- [x] Deals immediate damage on cast, then 1 damage tick per second for 3 seconds via `extensions.register_tick`
- [x] `monster.py` gains burn-tracking fields (e.g. `burn_ticks_remaining`, `burn_damage_per_tick`)
- [x] Burn expires cleanly after 3 ticks; a monster dying mid-burn doesn't error (burn state on a removed monster is simply discarded)
- [x] `save.py` round-trips mid-burn state
- [x] Unit tests: total damage dealt (immediate + DoT), burn expiry, death mid-burn doesn't crash the tick loop

**Implementation notes:** `cast_fire` reuses `cast_lightning`'s exact scaffolding (ready-check, living-Mage check, `nearest_monster_to_territory`, cooldown start) — `Spellbook.cooldowns` is keyed by spell name, so Fire and Lightning cooldowns are naturally independent with zero extra code.

**Deviation from the ticket's literal spec, and why:** "via `extensions.register_tick`" isn't actually possible as written — monsters live on `Game.monsters`, not `World`, and `register_tick` callbacks only ever receive `(world, dt)` (this is exactly why ticket 18 had to put `Spellbook` on `World` in the first place). There is no path from a `world`-scoped tick callback to the monster list. Burn ticking is folded into `Monster.update(dt)` instead (`_tick_burn`, called first thing every `update()`) — which is already invoked once per monster per game tick from `game.py`'s existing `for monster in self.monsters: monster.update(dt)` loop, so this needed zero new call sites. `burn_ticks_remaining`/`burn_damage_per_tick` plus a `burn_tick_timer` sub-accumulator (ticks fire every `FIRE_BURN_TICK_INTERVAL`, not every frame) live directly on `Monster`. "Death mid-burn doesn't error" falls out for free from the existing architecture: `Monster.update` still runs (and can still tick burn) for a tick or two after health drops ≤0, until `combat.py`'s `monsters[:] = [m for m in monsters if not m.is_dead]` removes it later in the same `game.py.update()` call — nothing dereferences a "gone" monster in the meantime, so there's nothing to guard against.

Also extended `Spellbook.trigger_flash(position, duration, color)` (was `(position, duration)` in ticket 18) so Fire's flash renders orange (`COLOR_FIRE_FLASH`) instead of reusing Lightning's yellow — `render_magic.py` now reads `spellbook.flash_color` instead of a hardcoded constant. This is exactly the "reused by Fire/Freeze" scaffolding ticket 18's own description called for. `_magic_hud_line` now reports both spells' cooldowns on one line.

`save.py`'s monster dict gains `burn_ticks_remaining`/`burn_damage_per_tick`, with `0` defaults via `.get()` for backward compatibility with pre-ticket-19 save files.

**`/code-review medium` fixes (4 findings, all cleanup, no correctness bugs):**
1. `cast_fire` duplicated `cast_lightning`'s entire scaffolding line-for-line — flagged as compounding once Freeze (ticket 20, the third planned spell) lands as a third near-identical copy. Extracted `_cast_single_target_spell(world, monsters, spell, damage, cooldown, color, on_hit=None)`; `cast_lightning`/`cast_fire` are now thin wrappers, Fire's burn applied via the `on_hit` hook. (Freeze is AoE, not single-target, so it may still need its own variant — noted for that ticket, not solved here.)
2. `Monster._tick_burn`'s accumulate/while-loop pattern diverged from `DayNightCycle.update`/`Nest.update`'s simpler "accumulate, fire once, reset to 0" shape used elsewhere for the same kind of interval timer. Changed to match (single `if`, reset instead of subtract-and-loop) — no test depended on multi-tick-catch-up-in-one-call behavior, so this was a safe, non-breaking simplification.
3. `render_magic.py`'s flash guard checked `flash_color is None` as a third condition that can never independently be true (`trigger_flash` always sets all three together) — removed as validation for a state that can't happen, per this project's own coding-style rule.
4. Dropped `burn_tick_timer` from `save.py`'s persisted fields — preserving sub-second timing precision on a 3-second DoT across a save/load boundary isn't worth a dedicated save-file key, `.get()` default, and round-trip test. Still lives on `Monster` for live-session ticking; a reloaded mid-burn monster just restarts its current tick's timer (worst case ~1s of imperceptible drift).
