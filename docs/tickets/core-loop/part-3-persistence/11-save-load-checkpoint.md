# 11 — Save/load checkpoint

**What to build:** Full simulation state (grid claim/fog/resources, NPC positions/health/hunger/priority ranking, inventory, buildings, nests, round number/phase) is serialized to a single checkpoint file at each day/night phase boundary — hooked into `DayNightCycle`'s phase transition, never mid-tick. On launch, the game loads the most recent checkpoint if one exists, otherwise starts a fresh game. This is what makes the project runnable across multiple computers/sessions from a committed checkpoint.

**Blocked by:** 01 — NPC entity + pathfinding + render, 02 — Task queue + Gather task, 04 — Build task + Wall/Tower buildings, 05 — Priority table UI, 06 — Night combat core, 08 — Hunger & starvation

**Status:** ready-for-agent

- [ ] Save module serializes: grid (claim/fog/resource state), all NPCs (position, health, hunger, priority ranking, current task), inventory, all buildings, all nests/monsters, round number, phase, phase timer
- [ ] Save is triggered only on `DayNightCycle` phase transition (day→night or night→day), never at an arbitrary tick
- [ ] Load reconstructs the full simulation state from the checkpoint file such that resuming is indistinguishable from having paused at that phase boundary
- [ ] On launch, game loads the most recent checkpoint if the file exists; otherwise starts a fresh game (existing `Grid()` generation path)
- [ ] Format is free (JSON/pickle/etc.) as long as the round-trip is exact
- [ ] Unit tests cover: save→load round-trip reproduces identical state for a non-trivial mid-game snapshot (multiple NPCs with different tasks/hunger/health, several buildings, at least one nest), load-with-no-file-present falls back to fresh game generation without error
