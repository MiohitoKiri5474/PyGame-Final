# 06 — Night combat core

**What to build:** Nest entities placed at map generation. When night falls, nests spawn monsters on a rate that ramps with round number; new nests can also appear over time (not just the ones present at generation) so threat keeps escalating across a long session. Spawned monsters path toward claimed territory using the same A* system NPCs use (ticket 01). When an NPC and a monster are adjacent, they auto-engage each round-tick: stat-based damage applies automatically (no manual targeting). A monster or NPC reaching 0 health is removed from play.

**Blocked by:** 01 — NPC entity + pathfinding + render

**Status:** ready-for-agent

- [ ] Nest entity placed at map generation (position, spawn timer/rate)
- [ ] Nest spawn rate is a named, tunable constant that scales with round number (ramp, not fixed)
- [ ] New nests can appear over time during play, independent of the generation-time set; rate/cap is a named tunable constant
- [ ] Monster entity spawned from a nest paths toward claimed territory via the shared A* pathfinding module
- [ ] Combat resolution: each tick, adjacent NPC↔monster pairs apply stat-based damage automatically (attack − defense style formula, exact numbers are tunable constants)
- [ ] NPC health decreases from monster attacks; NPC removed from play at 0 health
- [ ] Monster health decreases from NPC attacks; monster removed from play at 0 health
- [ ] Unit tests cover: nest spawn timing respects the rate/ramp constant, monster pathing reaches a claimed-territory tile on a known small grid, adjacent-pair damage resolution produces expected health deltas, 0-health removal for both NPC and monster
