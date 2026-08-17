# 20 — Freeze spell

**What to build:** `E`, 25s cooldown, freezes/slows every monster in a 3x3 tile radius around the nearest threat for 4 seconds, stopping their advance. First spell that affects movement rather than just dealing damage.

**Blocked by:** 18 — Magic framework + Lightning spell.

**Status:** done

- [x] `cast_freeze` in `magic.py` reuses the cast/cooldown scaffolding from ticket 18, with a 3x3-tile-radius query around the nearest-threat tile instead of single-target
- [x] `monster.py` gains a `frozen_timer` field
- [x] `Monster.update`'s movement step is skipped while `frozen_timer` is active
- [x] Re-hitting an already-frozen monster refreshes `frozen_timer` rather than stacking/extending indefinitely
- [x] `save.py` round-trips `frozen_timer`
- [x] Unit tests: AoE correctly includes tiles inside the 3x3 and excludes tiles outside it, frozen monster doesn't advance its path until expiry, refresh-not-stack on re-hit

**Implementation notes:**
- Added `cast_freeze` in `src/magic.py` with 3x3 AoE centered on nearest threat.
- Skipped path step in `Monster.update()` when `frozen_timer > 0`.
- Verified in `tests/test_magic.py`.

