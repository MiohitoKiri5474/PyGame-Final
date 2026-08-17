# 24 — Wildlife / animal fauna

**What to build:** Neutral animals (Flying Squirrel, Fish, Wild Boar, Horse — small/large game; Wolf, Bear — dangerous beasts) spawn and wander passively on unclaimed/frontier map tiles. Non-dangerous species never initiate combat; dangerous species (Wolf, Bear) retaliate only if attacked first.

**Blocked by:** None — independent of Parts 1-2 aside from reusing `movement.py`/`pathfinding.py` as-is (no changes needed there).

**Status:** done

- [x] New `animal.py` (pygame-free): `Animal` entity (position, species, path, health if huntable) with a passive-wander `update(dt)`
- [x] New `wildlife.py`: spawn/placement logic mirroring `nest.py`'s edge/frontier-placement pattern, tunable spawn rate/cap, species tiers (small/large/dangerous)
- [x] `world.py` gains `world.animals: list[Animal]`
- [x] Non-dangerous species (Squirrel/Fish/Boar/Horse) never engage in combat under any circumstance
- [x] Dangerous species (Wolf/Bear) only retaliate after being attacked first — not proximity-aggro like monsters
- [x] `game.py` renders animals (additive, mirrors `render_monsters`); `save.py` persists the animal list
- [x] Unit tests: spawn respects frontier constraint, non-dangerous species never attacks, dangerous species retaliates only post-attack

**Implementation notes:** `Animal` carries `is_hostile`, flipped `True` only by `take_damage()` and only for `dangerous=True` species — no proximity check anywhere, so `combat.py` was never touched (satisfies "never proximity-aggro like monsters" by construction, not by a guard clause). Passive wander reuses `movement.step_toward_path` (the same primitive NPC/Monster already use): when an animal has no path, it picks a random cardinal-adjacent tile (bounds-checked against the grid) via its own injected `random.Random`, walks there, repeats. `wildlife.py`'s placement mirrors `nest.py`'s pattern but scans for *unclaimed* tiles anywhere on the map (`_unclaimed_tiles`) rather than map-edge tiles — animals are wild fauna roaming the frontier generally, not something walking in from outside the map like monsters. Species table (`ANIMAL_SPECIES` in `constants.py`) maps each of the 6 species to `(speed, dangerous, health)`; all 6 get a health stat (not just the dangerous ones) since `game-detail.md`'s hunting section lists every one of them as huntable, not just the dangerous pair.

Wired via the ticket-13 per-tick hook (`extensions.register_tick`) rather than a new `game.py` call site — `wildlife.py` self-registers its tick function at import time via `plugins.py`, same as every other feature module. `world.py`'s `World.__init__` calls `create_initial_animals` directly (unlike nests, which `Game.__init__` owns) since the ticket specifies `world.animals` as `World`'s own state, not `Game`'s.

This branch predated tickets 13/14 merging into `develop`; merged `develop` in before finishing so the per-tick hook and updated material constants were available, resolving two add/add doc conflicts (kept `develop`'s completed ticket 13/14 docs over this branch's stale to-do copies) and one both-sides-append conflict in `constants.py` (kept both blocks in sequence).

**`/code-review medium` fixes:**
1. `ANIMAL_MAX_COUNT` was defined but never read — only the one-time initial population (`ANIMAL_INITIAL_COUNT`) existed, nothing bounded ongoing growth. Fixed by adding an actual top-up mechanism: `world.animal_spawn_timer` (new `World` field, persisted through `save.py` like everything else here) accumulates in `_tick_wildlife`, and every `ANIMAL_SPAWN_INTERVAL` seconds one new animal spawns on a random unclaimed tile if under `ANIMAL_MAX_COUNT` — mirrors `NestManager`'s own ongoing-spawn pattern.
2. `Animal.is_hostile` is written by `take_damage()` but has no reader anywhere in this ticket — flagged as a concern. This is intentional, not an oversight: nothing in the game deals damage to animals yet (no Hunt task exists — that's ticket 25, which explicitly owns Knight-vs-fauna combat math per its own spec). `is_hostile`/`take_damage()` are the data-model half of "dangerous species only retaliate after being attacked" (the state transition itself), ready for ticket 25 to consume; building animal-side combat *resolution* now, before anything can attack an animal, would be speculative work duplicating what ticket 25 needs to do anyway. Left as-is, documented here so it doesn't read as dead code later.
