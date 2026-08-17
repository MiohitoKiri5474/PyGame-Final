# 17 — Farmland building (plant → grow → harvest cycle)

**What to build:** Farmland places like Wall/Tower/House but carries growth state instead of being a one-shot building. Once built it grows on a fixed timer (ticked via the new per-tick hook); once ready, the player queues a Harvest task the same way Gather is queued by click. Harvesting credits crops and restarts the growth timer automatically — no replant step.

**Blocked by:** 13 — Per-tick simulation hook, 14 — Expanded material taxonomy.

**Status:** ready-for-agent

- [ ] `BuildFarmland` registered via the standard Build-task flow (same `can_queue` shape as Wall/Tower/House)
- [ ] `Building` gains `growth_timer: float = 0.0, ready: bool = False` — no-op defaults for Wall/Tower/House, only meaningful for Farmland
- [ ] Growth timer advances every tick via `extensions.register_tick`, flips `ready = True` at a named threshold constant
- [ ] New `HarvestFarmland` task type only queueable when the target Farmland's `ready` is `True`; completion credits the crop yield and resets `growth_timer`/`ready` to restart the cycle
- [ ] `save.py`'s building dict round-trips `growth_timer`/`ready`, including a mid-growth (not-yet-ready) Farmland
- [ ] Unit tests: growth timing to ready, harvest resets and the cycle repeats, Harvest not queueable pre-ready
