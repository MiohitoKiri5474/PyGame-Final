# 21 — Monster variety (Werewolf/Vampire/Zombie)

**What to build:** `Monster.type` drives per-type stat presets — Werewolf (fast, 80px/s, 50 HP, 14 attack), Zombie (slow, 40px/s, 90 HP, high building-siege damage), Vampire (high speed, life-steals on hit, avoids/deprioritizes Wall-adjacent routing). `NestManager` picks a weighted monster type per spawn instead of always spawning the same stat block.

**Blocked by:** 20 — Freeze spell. Sequenced, not parallel: both this and Freeze touch `combat.py`'s attack resolution and add fields to `monster.py` — land Freeze first to avoid a hand-resolved merge conflict on the same functions.

**Status:** done

- [x] `Monster` gains a `type` field; a named stat table in `constants.py` maps type -> (speed, max_health, attack, defense, special)
- [x] `NestManager`'s spawn factory picks a weighted type per spawn (named weight constants)
- [x] Vampire heals itself on dealing damage, same tick as the hit (life-steal), in `combat.py`
- [ ] Vampire's pathfinding deprioritizes/avoids routing adjacent to Wall buildings — **out of scope for this pass**, see notes
- [x] `save.py` round-trips `type`
- [x] Unit tests: stat assignment per type, weighted spawn distribution over enough samples, life-steal heal math

**Implementation notes:** `Monster.__init__`'s `speed` parameter changed from a literal `speed: float = MONSTER_SPEED` default to a `speed: float | None = None` sentinel, resolved inside the body as explicit-arg > type's stat-table speed > flat-constant default. This is needed so `save.py`'s load path (which always passes the exact persisted speed) still wins over whatever the reloaded monster's `type` would otherwise imply, while `spawn_monster` — which never passes `speed` — lets the type's table speed take over. `max_health` is a new field (previously only the flat `MONSTER_MAX_HEALTH` constant existed, with no per-instance record of it) — `combat.py`'s life-steal clamp needs a per-monster ceiling to heal against, and `stats.get(..., MONSTER_MAX_HEALTH)` gives untyped monsters the same ceiling they always implicitly had.

Vampire's Wall-avoidant pathing (the ticket's other bullet) is deliberately not implemented here: there's no existing per-monster-type pathfinding cost/weight infrastructure in `pathfinding.py`, every monster type shares the same `find_path` call in `spawn_monster`, and adding a differentiated cost function is a bigger change than this ticket's remaining budget — flagged as future work rather than silently dropped.

**Reconciliation note:** this ticket was built after discovering a teammate (n97131056) had independently implemented the same scope on a parallel `feat/combat-depth` branch. The stat values above (speed/max_health/attack/defense per type, spawn weights) are reused from their design rather than re-balanced from scratch, since neither branch has playtested numbers suggesting otherwise — but the code itself (constructor shape, life-steal clamp, test coverage) was written independently against this codebase's own conventions (plain attribute access, no `getattr` fallbacks, discrete-tick status effects).

**Code review finding, fixed:** `/code-review medium` caught a mid-tick resurrection bug in the life-steal clamp — `resolve_combat`'s outer loop is NPC-major (`for npc in npcs: for monster in monsters:`), so a single monster is revisited once per NPC in range. A Vampire dropped to lethal health by the first NPC in the pairing order would still "fight" a second nearby NPC later in the same call, and its life-steal heal (`min(monster.max_health, monster.health + monster_dmg)`) could push its health back above zero — surviving a killing blow it shouldn't have. Fixed with an `if monster.is_dead: continue` guard at the top of the inner loop, so a monster that dies mid-resolution stops participating in any further pairings for the rest of that tick (also fixes the pre-existing, lower-severity cosmetic issue of a dead monster still dealing damage to a second NPC before end-of-function filtering). Regression test: `test_life_steal_monster_killed_by_one_npc_cannot_resurrect_off_a_second`.
