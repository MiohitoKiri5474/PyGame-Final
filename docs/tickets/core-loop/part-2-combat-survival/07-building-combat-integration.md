# 07 — Building combat integration

**What to build:** Wall and Tower buildings (ticket 04) become active participants in night combat (ticket 06). A Wall blocks monster pathing — monsters cannot route through or destroy it in this step, so they're forced around or halted. A Tower auto-attacks monsters within its range without needing adjacency (unlike NPCs, which require adjacency).

**Blocked by:** 04 — Build task + Wall/Tower buildings, 06 — Night combat core

**Status:** ready-for-agent

- [ ] Wall tiles are excluded from the walkable set the A* pathfinding module considers for monsters (and NPCs), forcing monsters to route around or halt if no path exists
- [ ] Wall has no attack behavior — purely a path obstruction in this step
- [ ] Tower auto-attacks any monster within its defined range each tick, independent of adjacency, using the same stat-based damage resolution as NPC combat
- [ ] Unit tests cover: pathfinding correctly routes around or reports no-path when a Wall blocks the only route on a known small grid, Tower damages a monster within range without requiring adjacency, Tower does not attack monsters outside its range
