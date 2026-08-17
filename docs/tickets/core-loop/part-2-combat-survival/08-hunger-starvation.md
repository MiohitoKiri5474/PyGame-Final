# 08 — Hunger & starvation

**What to build:** Each NPC has a hunger stat that depletes over time (independent of combat). An NPC whose hunger reaches 0 dies (removed from play), same as combat death.

**Blocked by:** 01 — NPC entity + pathfinding + render

**Status:** ready-for-agent

- [ ] NPC entity gains a hunger stat alongside health
- [ ] Hunger decreases over time on a tunable, named rate constant
- [ ] NPC removed from play when hunger reaches 0 (starvation death), using the same death/removal path as combat death
- [ ] Unit tests cover: hunger decays at the expected rate over N ticks, NPC is removed once hunger hits 0
