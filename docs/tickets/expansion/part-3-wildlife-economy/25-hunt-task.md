# 25 — Hunt task

**What to build:** The player queues a Hunt task on a visible wild animal; a priority-ranked NPC (Knight gets a critical-hit bonus) paths to and engages it. `Task.target` stays a plain tile like every other task type (confirmed decision — no new entity-targeting concept on `Task`); the tile is snapshotted at claim time, and `update_npc_tasks`' arrival branch re-checks the animal's current tile and re-paths if it has moved, rather than unassigning the task the way `can_perform` does for blocked builds (a wandering animal isn't "unperformable," it just needs a new path).

**Blocked by:** 24 — Wildlife / animal fauna.

**Status:** ready-for-agent

- [ ] New `hunt_task.py` registers a `Hunt` task type via the standard `register_task_type` pattern
- [ ] Queueing is rejected on a tile with no animal present
- [ ] `task.py`'s arrival-branch logic (the one place moving-target re-path is introduced — don't duplicate this elsewhere) recomputes the NPC's path when the target animal's current tile differs from the tile it last pathed to
- [ ] Arrival checks the animal's CURRENT position (not the stale snapshot) before resolving combat
- [ ] Knight NPCs get a critical-hit-chance bonus against fauna specifically (not against monsters) in `combat.py`/`npc.py`
- [ ] Animal death ends the Hunt task and hands off to ticket 26 (Post-Hunt decision)
- [ ] `save.py` persists the hunted-animal's id on an in-progress Hunt task, mirroring the `assigned_npc_id`-by-id pattern from ticket 11 rather than a live object reference
- [ ] Unit tests: reject-no-animal, re-path on animal movement, arrival uses current position, death hands off correctly
