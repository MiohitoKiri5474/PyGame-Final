# 16 — Population growth (+1 NPC every 3 rounds)

**What to build:** On the night→day transition where the new round number is a multiple of 3, spawn 1 new NPC at the colony center or an existing House, with a role assigned, but only if the colony is under its population cap.

**Blocked by:** 15 — House & population cap, 12 — NPC Role System.

**Status:** ready-for-agent

- [ ] New `population.py` (pygame-free): `maybe_spawn_npc(world, round_number, transitioned) -> NPC | None`
- [ ] Spawns exactly on rounds 3, 6, 9, ... at the night→day transition, never mid-round or on other transitions — reuses the `transitioned` bool `game.py` already captures for the save-checkpoint hook (ticket 11), don't add a second polling mechanism
- [ ] Suppressed once `len(world.npcs) >= population_cap(world)` (ticket 15's helper)
- [ ] Spawned NPC has a valid role (reasonable default: round-robin or random across the 3 roles)
- [ ] `game.py`'s `update()` calls this as one more additive consumer of `transitioned`, alongside the existing save-checkpoint call
- [ ] Unit tests: spawns on round 3/6/9, suppressed at cap, spawned NPC has a role
