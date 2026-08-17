# 03 — Expand Territory task

**What to build:** A new task type, Expand Territory, reusing the task queue/priority/claim infrastructure from ticket 02. The player clicks a revealed-but-unclaimed frontier tile to queue it. An idle NPC ranked for this task type claims it, paths to the tile, and on completion reveals fog and claims tiles within a radius around it (same "expand" primitive already used for the starting territory in `grid.py`, now driven by an NPC task instead of only at game start).

**Blocked by:** 02 — Task queue + Gather task

**Status:** done

- [x] Expand Territory registered as a task type NPCs can be ranked for and can claim from the queue
- [x] Clicking a valid frontier tile (revealed-or-not, unclaimed) queues an Expand task targeting it
- [x] NPC with an assigned Expand task paths to the tile, spends work time on arrival, then reveals fog + claims tiles in the existing expand radius, task removed from queue, NPC returns to idle
- [x] Unit tests cover: full Expand task lifecycle updates grid claim/fog state as expected, task only queueable on a valid frontier tile (not on already-claimed tiles)

**Implementation notes:**
- Created `src/expand_task.py` based on the reference pattern of `gather_task.py`.
- Task validity checks that the targeted tile is inbound and unclaimed, but does not strictly require it to be revealed, which is useful when working with game fog.
- Configured expansion radius parameters and work seconds in `src/constants.py`.
- Verified task queueing and lifecycle successfully claim tiles and reveal fog in `tests/test_expand_task.py`.
