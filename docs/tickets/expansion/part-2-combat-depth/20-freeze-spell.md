# 20 — Freeze spell

**What to build:** `E`, 25s cooldown, freezes/slows every monster in a 3x3 tile radius around the nearest threat for 4 seconds, stopping their advance. First spell that affects movement rather than just dealing damage.

**Blocked by:** 18 — Magic framework + Lightning spell.

**Status:** ready-for-agent

- [ ] `cast_freeze` in `magic.py` reuses the cast/cooldown scaffolding from ticket 18, with a 3x3-tile-radius query around the nearest-threat tile instead of single-target
- [ ] `monster.py` gains a `frozen_until` timestamp/timer field
- [ ] `Monster.update`'s movement step is skipped (or halved, pick one and note it in code) while `frozen_until` is active
- [ ] Re-hitting an already-frozen monster refreshes `frozen_until` rather than stacking/extending indefinitely
- [ ] `save.py` round-trips `frozen_until`
- [ ] Unit tests: AoE correctly includes tiles inside the 3x3 and excludes tiles outside it, frozen monster doesn't advance its path until expiry, refresh-not-stack on re-hit
