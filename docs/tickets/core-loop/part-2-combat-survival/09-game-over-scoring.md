# 09 — Game over & scoring

**What to build:** The game detects when all NPCs are dead (from any cause — combat or starvation, both funnel through the same removal path) and declares game-over, showing the current round number as the player's score. No fixed win state — this is the endless-survival end condition.

**Blocked by:** 06 — Night combat core

**Status:** ready-for-agent

- [ ] Game-over check triggers when the NPC list is empty
- [ ] Game-over state halts simulation updates (no further ticks/spawns/tasks processed)
- [ ] Game-over screen/state displays the round number reached as the score
- [ ] Unit tests cover: game-over triggers correctly once the last NPC is removed (simulate via either combat or starvation death path), simulation does not advance further once game-over is reached
