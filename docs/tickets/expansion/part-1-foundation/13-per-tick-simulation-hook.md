# 13 — Per-tick simulation hook

**What to build:** A 4th extension point, `extensions.register_tick(fn)` where `fn(world, dt)`, called once per unpaused simulation tick from `game.py`, mirroring the existing `register_overlay`/`register_hud_line` pattern. Exists so Farmland growth (17), spell cooldowns/DoT (18-20), food spoilage decay (27), and Animal Pen production (26) each register their own callback instead of hand-editing the same line in `game.py`'s `update()`.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] `extensions.py` gains `register_tick(fn)` and a `run_ticks(world, dt)` that calls every registered callback in registration order
- [x] `game.py`'s `update()` calls `run_ticks(self.world, dt)` once per unpaused tick, next to the existing `update_npc_tasks` call (additive, no restructuring)
- [x] `run_ticks` is a no-op with zero callbacks registered (existing behavior unaffected until a later ticket registers one)
- [x] Unit test: multiple registered callbacks all fire once per call, in order, with correct `(world, dt)` args

**Implementation notes:** `_tick_callbacks: list[Callable]` module-level list, mirroring `_hud_line_providers`/`_overlay_renderers` exactly. `run_ticks(self.world, dt)` is called inside `game.py`'s existing `if not self.paused and not self.game_over_state.is_over:` block, right after `update_npc_tasks` — so anything registered here (Farmland growth, spell cooldowns, food spoilage decay) correctly freezes on pause/game-over along with the rest of the sim, not just camera/input. New `tests/test_extensions.py` (this module had no dedicated test file before).
