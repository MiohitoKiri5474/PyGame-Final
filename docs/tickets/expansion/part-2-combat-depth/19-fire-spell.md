# 19 — Fire spell

**What to build:** `Q`, 15s cooldown, deals immediate damage to the nearest monster to territory plus a 3-second burn damage-over-time.

**Blocked by:** 18 — Magic framework + Lightning spell.

**Status:** ready-for-agent

- [ ] `cast_fire` in `magic.py` reuses the cast/cooldown/targeting scaffolding from ticket 18 (no duplicated cooldown-tracking logic)
- [ ] Deals immediate damage on cast, then 1 damage tick per second for 3 seconds via `extensions.register_tick`
- [ ] `monster.py` gains burn-tracking fields (e.g. `burn_ticks_remaining`, `burn_damage_per_tick`)
- [ ] Burn expires cleanly after 3 ticks; a monster dying mid-burn doesn't error (burn state on a removed monster is simply discarded)
- [ ] `save.py` round-trips mid-burn state
- [ ] Unit tests: total damage dealt (immediate + DoT), burn expiry, death mid-burn doesn't crash the tick loop
