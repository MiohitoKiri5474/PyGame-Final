# 22 — Wave settlement & skill point rewards

**What to build:** At the night→day transition, tally the night that just ended: if every monster spawned that night is dead (full clear), grant 2 skill points; otherwise grant 1 point per N monsters killed (partial clear). The simulation auto-pauses at the start of the new day only while points are pending, prompting the player to spend them.

**Blocked by:** None new — needs the `transitioned` bool `game.py` already captures (ticket 11's save hook), no other dependency.

**Status:** ready-for-agent

- [ ] Per-night spawn/kill counters (don't exist today — `combat.py`'s removal of dead monsters doesn't count kills anywhere) reset at each day→night transition
- [ ] Full clear = 2 points; partial clear = 1 point per N kills, N a named constant in `constants.py`
- [ ] `game.py` auto-pauses (reuses existing `self.paused`) at day start only when skill points are pending; unpausing is manual (Space) once the player has spent or dismissed them
- [ ] New `settlement.py` (pygame-free): `evaluate_wave(spawned_count, killed_count) -> points_awarded`
- [ ] `save.py` persists available skill points plus in-progress per-night counters (a save mid-night must not lose the tally)
- [ ] Unit tests: full-clear award, partial-clear award at various kill counts, pause-gating logic
