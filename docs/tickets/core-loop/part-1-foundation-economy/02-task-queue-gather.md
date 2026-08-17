# 02 — Task queue + Gather task

**What to build:** A global task queue the player can add Gather tasks to by clicking a resource tile. Each NPC has its own priority ranking over task types (starts with just Gather, extended by later tickets). An idle NPC (no current task) scans the queue and auto-claims the highest-priority task type it's ranked for and that's available. Once claimed, the NPC paths to the resource tile (via ticket 01's pathfinding), spends gather time there, then the resource is removed from the tile and its value is credited directly to a shared global inventory (no ground items, no hauling).

**Blocked by:** 01 — NPC entity + pathfinding + render

**Status:** done

- [x] Task representation: type, target tile, assigned NPC (or unassigned), progress
- [x] Global task queue holds unassigned and in-progress tasks; tasks are removed on completion
- [x] Per-NPC priority ranking data structure exists (ordered list of task types), even with only Gather registered so far
- [x] Idle-NPC claim algorithm: NPC with no task scans the queue, picks the highest-ranked available task type per its own ranking, assigns itself
- [x] Clicking a resource tile queues a Gather task targeting it
- [x] NPC with an assigned Gather task paths to the tile, spends gather time on arrival, then: resource cleared from tile, inventory credited, task removed from queue, NPC returns to idle
- [x] Shared inventory module: resource type → count, with an add operation
- [x] Unit tests cover: idle-claim picks correctly by priority ranking with multiple queued tasks, full Gather task lifecycle (queued → assigned → walking → gathering → complete) updates tile/inventory/queue state as expected, inventory add is correct and cumulative

**Implementation notes:** built a task-type registry (`task.py`: `TaskType`/`register_task_type`/`TASK_TYPES`) rather than hardcoding Gather, plus `World` (pygame-free grid+inventory+npcs+tasks bundle) and three extension points on `game.py` (task-type registration via `plugins.py`, `extensions.register_overlay`, `extensions.register_hud_line`) — this is prep for 03/04/10 landing in parallel without editing `game.py`; see CLAUDE.md's "Extending the task/render system" section. `Grid.expand()` was also fixed to decouple fog-reveal radius from claim radius (separate commit), since 03's frontier-tile targeting needs a revealed-but-unclaimed band that didn't exist before. Task-type selection in-game is Tab-cycle (no per-task-type hotkeys), since a click-menu wasn't in scope here and building's Wall-vs-Tower choice (04) will reuse the same mechanism.
