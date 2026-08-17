# 11 — Save/load checkpoint

**What to build:** Full simulation state (grid claim/fog/resources, NPC positions/health/hunger/priority ranking, inventory, buildings, nests, round number/phase) is serialized to a single checkpoint file at each day/night phase boundary — hooked into `DayNightCycle`'s phase transition, never mid-tick. On launch, the game loads the most recent checkpoint if one exists, otherwise starts a fresh game. This is what makes the project runnable across multiple computers/sessions from a committed checkpoint.

**Blocked by:** 01 — NPC entity + pathfinding + render, 02 — Task queue + Gather task, 04 — Build task + Wall/Tower buildings, 05 — Priority table UI, 06 — Night combat core, 08 — Hunger & starvation

**Status:** done

- [x] Save module serializes: grid (claim/fog/resource state), all NPCs (position, health, hunger, priority ranking, current task), inventory, all buildings, all nests/monsters, round number, phase, phase timer
- [x] Save is triggered only on `DayNightCycle` phase transition (day→night or night→day), never at an arbitrary tick
- [x] Load reconstructs the full simulation state from the checkpoint file such that resuming is indistinguishable from having paused at that phase boundary
- [x] On launch, game loads the most recent checkpoint if the file exists; otherwise starts a fresh game (existing `Grid()` generation path)
- [x] Format is free (JSON/pickle/etc.) as long as the round-trip is exact
- [x] Unit tests cover: save→load round-trip reproduces identical state for a non-trivial mid-game snapshot (multiple NPCs with different tasks/hunger/health, several buildings, at least one nest), load-with-no-file-present falls back to fresh game generation without error

**Implementation notes:** New pygame-free `src/save.py` — JSON checkpoint (chosen over pickle: no arbitrary-code-execution risk on load, human-diffable). `DayNightCycle.update()` now returns `bool` (transition fired this tick) instead of `None`, giving `game.py` a clean hook instead of polling `phase` before/after. `Task.assigned_npc` / `NPC.task` form a live bidirectional reference that can't round-trip through JSON directly: saved as one-directional `assigned_npc_id` on the task, re-linked by id on load via `World.__new__` bypass (skips `World.__init__`'s random-gen + default-NPC-spawn side effects). `NPC._next_id` bumped past the max loaded id to avoid future collisions. Save file (`save.json`, gitignored — see below) written only on phase transition, not every tick.

Round-trip correctness verified two ways in `tests/test_save.py`: a double-dump comparison (`dump_state` before save == `dump_state` after load) catches any load-side bug in one assertion, plus explicit per-field assertions and `isinstance(..., tuple)` checks (JSON has no tuple type — `list.__eq__` vs `tuple.__eq__` would pass the dump-comparison test while breaking `task.target == tile` / `is_wall_blocked` coordinate comparisons at runtime).

Found but out of scope (flagging, not fixing): when an NPC dies mid-task (combat or starvation), `game.py`'s `world.npcs[:] = [npc for npc in npcs if not npc.is_dead]` drops the NPC but never clears `npc.task.assigned_npc`, so that task is permanently unclaimable — same starvation class as the ticket 03 Expand-task bug, just triggered by death instead of unreachable targets. Lives in already-merged ticket 06/08 code (`game.py`'s death-filter line), not save/load. `test_load_dangling_assigned_npc_id_leaves_task_reclaimable` confirms load at least doesn't perpetuate a stale reference across a save/load boundary — the underlying live-session bug still needs its own fix.

`save.json` is gitignored, not committed — ticket text says "committed checkpoint" but the file rewrites on every phase transition (~60-120s of real play) and a second collaborator is active on this repo; committing it would churn the tree and conflict on every PR. Confirmed with user before implementing.

Also corrected `CLAUDE.md`'s Test seam section: `world.py`/`plugins.py` have transitively imported pygame (via `plugins.py` → `render_buildings.py`) since ticket 04, not truly pygame-free as previously documented — harmless (no display/font calls at import time) but the doc claim was stale.
