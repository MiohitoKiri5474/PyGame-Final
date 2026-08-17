# 24 — Wildlife / animal fauna

**What to build:** Neutral animals (Flying Squirrel, Fish, Wild Boar, Horse — small/large game; Wolf, Bear — dangerous beasts) spawn and wander passively on unclaimed/frontier map tiles. Non-dangerous species never initiate combat; dangerous species (Wolf, Bear) retaliate only if attacked first.

**Blocked by:** None — independent of Parts 1-2 aside from reusing `movement.py`/`pathfinding.py` as-is (no changes needed there).

**Status:** ready-for-agent

- [ ] New `animal.py` (pygame-free): `Animal` entity (position, species, path, health if huntable) with a passive-wander `update(dt)`
- [ ] New `wildlife.py`: spawn/placement logic mirroring `nest.py`'s edge/frontier-placement pattern, tunable spawn rate/cap, species tiers (small/large/dangerous)
- [ ] `world.py` gains `world.animals: list[Animal]`
- [ ] Non-dangerous species (Squirrel/Fish/Boar/Horse) never engage in combat under any circumstance
- [ ] Dangerous species (Wolf/Bear) only retaliate after being attacked first — not proximity-aggro like monsters
- [ ] `game.py` renders animals (additive, mirrors `render_monsters`); `save.py` persists the animal list
- [ ] Unit tests: spawn respects frontier constraint, non-dangerous species never attacks, dangerous species retaliates only post-attack
