# 19 — Fire spell

**What to build:** `Q`, 15s cooldown, deals immediate damage to the nearest monster to territory plus a 3-second burn damage-over-time.

**Blocked by:** 18 — Magic framework + Lightning spell.

**Status:** done

- [x] `cast_fire` in `magic.py` reuses the cast/cooldown/targeting scaffolding from ticket 18 (no duplicated cooldown-tracking logic)
- [x] `F1` (reassigned from Q per user design choice) deals immediate damage on cast, plus burn DoT over 3 seconds
- [x] `monster.py` gains burn-tracking fields (`burn_remaining`, `burn_dps`)
- [x] Burn expires cleanly after duration; a monster dying mid-burn doesn't error (burn state on a removed monster is simply discarded)
- [x] `save.py` round-trips mid-burn state
- [x] Unit tests: total damage dealt (immediate + DoT), burn expiry, death mid-burn doesn't crash the tick loop

**Implementation notes:**
- Added `cast_fire` in `src/magic.py` with `FIRE_DAMAGE` and `FIRE_BURN_DURATION`.
- Handled burn DoT tick in `Monster.update()`.
- Verified in `tests/test_magic.py`.

