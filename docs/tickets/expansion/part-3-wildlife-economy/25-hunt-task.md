# 25 — Hunt task

**What to build:** The player queues a Hunt task on a visible wild animal; a priority-ranked NPC (Knight gets a critical-hit bonus) paths to and engages it. `Task.target` stays a plain tile like every other task type (confirmed decision — no new entity-targeting concept on `Task`); the tile is snapshotted at claim time, and `update_npc_tasks`' arrival branch re-checks the animal's current tile and re-paths if it has moved, rather than unassigning the task the way `can_perform` does for blocked builds (a wandering animal isn't "unperformable," it just needs a new path).

**Blocked by:** 24 — Wildlife / animal fauna.

**Status:** done

- [x] New `hunt_task.py` registers a `Hunt` task type via the standard `register_task_type` pattern
- [x] Queueing is rejected on a tile with no animal present
- [x] `task.py`'s arrival-branch logic recomputes the NPC's path when the target animal's current tile differs from the tile it last pathed to
- [x] Arrival checks the animal's CURRENT position (not the stale snapshot) before resolving combat
- [x] Knight NPCs get a critical-hit-chance bonus against fauna specifically (not against monsters)
- [x] Animal death ends the Hunt task and hands off to ticket 26 (Post-Hunt decision)
- [x] `save.py` persists the hunted-animal's id on an in-progress Hunt task, mirroring the `assigned_npc_id`-by-id pattern from ticket 11 rather than a live object reference
- [x] Unit tests: reject-no-animal, re-path on animal movement, arrival uses current position, death hands off correctly

**Implementation notes:**
- Created `src/hunt_task.py` with `can_queue_hunt`, `can_perform_hunt`, and `on_complete_hunt`.
- Integrated moving-target re-pathing in `src/task.py`'s `update_npc_tasks` arrival branch.
- Added `Animal.id` and `Animal.retaliate()`.
- Added serialization for `target_animal_id` in `src/save.py`.
- Unit tests written in `tests/test_hunt_task.py`.

