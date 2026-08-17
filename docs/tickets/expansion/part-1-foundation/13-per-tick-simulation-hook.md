# 13 — Per-tick simulation hook

**What to build:** A 4th extension point, `extensions.register_tick(fn)` where `fn(world, dt)`, called once per unpaused simulation tick from `game.py`, mirroring the existing `register_overlay`/`register_hud_line` pattern. Exists so Farmland growth (17), spell cooldowns/DoT (18-20), food spoilage decay (27), and Animal Pen production (26) each register their own callback instead of hand-editing the same line in `game.py`'s `update()`.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `extensions.py` gains `register_tick(fn)` and a `run_ticks(world, dt)` that calls every registered callback in registration order
- [ ] `game.py`'s `update()` calls `run_ticks(self.world, dt)` once per unpaused tick, next to the existing `update_npc_tasks` call (additive, no restructuring)
- [ ] `run_ticks` is a no-op with zero callbacks registered (existing behavior unaffected until a later ticket registers one)
- [ ] Unit test: multiple registered callbacks all fire once per call, in order, with correct `(world, dt)` args
