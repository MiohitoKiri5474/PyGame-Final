# 02 — Task queue + Gather task

**What to build:** A global task queue the player can add Gather tasks to by clicking a resource tile. Each NPC has its own priority ranking over task types (starts with just Gather, extended by later tickets). An idle NPC (no current task) scans the queue and auto-claims the highest-priority task type it's ranked for and that's available. Once claimed, the NPC paths to the resource tile (via ticket 01's pathfinding), spends gather time there, then the resource is removed from the tile and its value is credited directly to a shared global inventory (no ground items, no hauling).

**Blocked by:** 01 — NPC entity + pathfinding + render

**Status:** ready-for-agent

- [ ] Task representation: type, target tile, assigned NPC (or unassigned), progress
- [ ] Global task queue holds unassigned and in-progress tasks; tasks are removed on completion
- [ ] Per-NPC priority ranking data structure exists (ordered list of task types), even with only Gather registered so far
- [ ] Idle-NPC claim algorithm: NPC with no task scans the queue, picks the highest-ranked available task type per its own ranking, assigns itself
- [ ] Clicking a resource tile queues a Gather task targeting it
- [ ] NPC with an assigned Gather task paths to the tile, spends gather time on arrival, then: resource cleared from tile, inventory credited, task removed from queue, NPC returns to idle
- [ ] Shared inventory module: resource type → count, with an add operation
- [ ] Unit tests cover: idle-claim picks correctly by priority ranking with multiple queued tasks, full Gather task lifecycle (queued → assigned → walking → gathering → complete) updates tile/inventory/queue state as expected, inventory add is correct and cumulative
