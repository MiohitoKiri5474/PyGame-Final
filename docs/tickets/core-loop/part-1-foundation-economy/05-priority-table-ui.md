# 05 — Priority table UI

**What to build:** A screen/overlay listing every NPC with a reorderable list of task types (Gather, Expand Territory, BuildWall, BuildTower), letting the player express per-NPC preference — e.g. "this NPC prefers building over gathering." Reordering writes directly to the per-NPC priority ranking data structure introduced in ticket 02, which the idle-claim algorithm already reads from.

**Blocked by:** 03 — Expand Territory task, 04 — Build task + Wall/Tower buildings

**Status:** done

- [x] Priority screen lists all current NPCs
- [x] Each NPC shows its task-type ranking (Gather, Expand, BuildWall, BuildTower) in current order
- [x] Player can reorder a given NPC's ranking through the UI
- [x] Reordering updates the same priority-ranking data structure the idle-claim algorithm (ticket 02) already consults — no parallel/duplicate ranking store
- [x] Changing priority order visibly changes which task an idle NPC claims next, when multiple task types are queued
- [x] Test/verification: exercising the idle-claim algorithm with a manually-set ranking order (unit test, no UI needed) confirms it picks per the configured order — UI itself is manually verified, not unit tested (thin layer over already-tested logic)

**Implementation notes:**
- Created `src/priority_ui.py` for the overlay UI (`PriorityTableUI`).
- Pressing `P` toggles the priority overlay; `Tab` cycles NPCs; `↑/↓` selects task; `←/→` or `+/-` reorders priority ranks; `Esc` or `P` closes the overlay.
- Modifies `npc.priority` directly in place, which `TaskQueue.claim_for()` already uses for idle-claiming tasks.
- Integrated into `src/game.py` event handling and rendering layers.
- Added comprehensive unit tests in `tests/test_priority_ui.py` covering idle claim order by priority and UI data manipulations.
