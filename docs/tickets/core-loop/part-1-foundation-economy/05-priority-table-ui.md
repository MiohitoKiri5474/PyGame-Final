# 05 — Priority table UI

**What to build:** A screen/overlay listing every NPC with a reorderable list of task types (Gather, Expand Territory, BuildWall, BuildTower), letting the player express per-NPC preference — e.g. "this NPC prefers building over gathering." Reordering writes directly to the per-NPC priority ranking data structure introduced in ticket 02, which the idle-claim algorithm already reads from.

**Blocked by:** 03 — Expand Territory task, 04 — Build task + Wall/Tower buildings

**Status:** ready-for-agent

- [ ] Priority screen lists all current NPCs
- [ ] Each NPC shows its task-type ranking (Gather, Expand, BuildWall, BuildTower) in current order
- [ ] Player can reorder a given NPC's ranking through the UI
- [ ] Reordering updates the same priority-ranking data structure the idle-claim algorithm (ticket 02) already consults — no parallel/duplicate ranking store
- [ ] Changing priority order visibly changes which task an idle NPC claims next, when multiple task types are queued
- [ ] Test/verification: exercising the idle-claim algorithm with a manually-set ranking order (unit test, no UI needed) confirms it picks per the configured order — UI itself is manually verified, not unit tested (thin layer over already-tested logic)
