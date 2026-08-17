# 22 — Wave settlement & skill point rewards

**What to build:** At the night→day transition, tally the night that just ended: if every monster spawned that night is dead (full clear), grant 2 skill points; otherwise grant 1 point per N monsters killed (partial clear). The simulation auto-pauses at the start of the new day only while points are pending, prompting the player to spend them.

**Blocked by:** None new — needs the `transitioned` bool `game.py` already captures (ticket 11's save hook), no other dependency.

**Status:** done

- [x] Per-night kill counter (don't exist today — `combat.py`'s removal of dead monsters doesn't count kills anywhere) reset at each day→night transition
- [x] Full clear = 2 points; partial clear = 1 point per N kills, N a named constant in `constants.py`
- [x] `game.py` auto-pauses (reuses existing `self.paused`) at day start only when skill points are pending; unpausing is manual (Space) once the player has spent or dismissed them
- [x] New `settlement.py` (pygame-free): `evaluate_wave(no_monsters_remain, killed_count) -> points_awarded`
- [x] `save.py` persists available skill points plus the in-progress per-night kill counter (a save mid-night must not lose the tally)
- [x] Unit tests: full-clear award, partial-clear award at various kill counts, pause gating

**Implementation notes:** `evaluate_wave(no_monsters_remain, killed_count) -> int` is a pure function in `settlement.py`. Full clear = `no_monsters_remain and killed_count > 0` (an empty night with zero spawns/kills is explicitly NOT a free 2-point bonus), otherwise `killed_count // WAVE_PARTIAL_CLEAR_KILLS_PER_POINT`. `game.py` tracks `_monsters_killed_this_night` as a plain instance counter, reset right after `self.cycle.update(dt)` returns `True` with the new phase `NIGHT`, incremented from `len(self.monsters)` before/after `resolve_combat` (`resolve_combat` already removes dead monsters from the list in place, so this needed zero changes to its signature or behavior). Evaluated on the `NIGHT`→`DAY` transition using `len(self.monsters) == 0` for `no_monsters_remain`, added to `self.skill_points_available`, which gates the auto-pause.

**Design pivot from the original spec (code review, first pass):** initially tracked a per-night *spawn* counter too and compared `spawned == killed` for full-clear, matching the ticket text literally ("if every monster spawned that night is dead"). Review caught a real bug: monsters have no despawn-at-dawn mechanic, so a monster that survived from an earlier night is still in `self.monsters` on a later night; killing it counted toward *that* night's kill tally without ever having been counted as *that* night's spawn, so `killed >= spawned` could trip a false full-clear even with the current night's own monsters still alive. Fixed by dropping spawn-tracking entirely and judging full clear on whether `self.monsters` is empty at day start — simpler, and arguably closer to what "full clear" should mean anyway (no monsters left roaming your territory, regardless of which night spawned them) than a strict per-night spawn/kill match that a persistent-monster model can't support cleanly.

**Also fixed (code review):** the auto-pause set by a pending-points night wasn't restored on load — `self.paused` was never persisted and `Game.__init__` unconditionally set it `False` before checking the loaded checkpoint. Fixed by re-deriving it: after loading a checkpoint, `if self.skill_points_available > 0: self.paused = True`. This is more robust than persisting `paused` as raw state, since it self-heals from any future code path that sets points without remembering to also pause.

`save_checkpoint`/`dump_state`/`load_checkpoint` gained 2 new int parameters (`skill_points_available`, `monsters_killed_this_night`) with `0` defaults — `load_checkpoint` reads them via `data.get(..., 0)` so an old save file from before this ticket still loads instead of raising `KeyError`. `tests/test_save.py`'s `_build_nontrivial_state()` fixture was extended to return non-zero values for both so the existing round-trip tests actually exercise this new state, not just prove the rest of the save format still works.
