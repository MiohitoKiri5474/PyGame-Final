# 21 — Monster variety (Werewolf/Vampire/Zombie)

**What to build:** `Monster.type` drives per-type stat presets — Werewolf (fast, 80px/s, 50 HP, 14 attack), Zombie (slow, 40px/s, 90 HP, high building-siege damage), Vampire (high speed, life-steals on hit, avoids/deprioritizes Wall-adjacent routing). `NestManager` picks a weighted monster type per spawn instead of always spawning the same stat block.

**Blocked by:** 20 — Freeze spell. Sequenced, not parallel: both this and Freeze touch `combat.py`'s attack resolution and add fields to `monster.py` — land Freeze first to avoid a hand-resolved merge conflict on the same functions.

**Status:** done

- [x] `Monster` gains a `type` field; a named stat table in `constants.py` maps type -> (speed, max_health, attack, defense, special)
- [x] `NestManager`'s spawn factory picks a weighted type per spawn (named weight constants)
- [x] Vampire heals itself on dealing damage, same tick as the hit (life-steal), in `combat.py`
- [x] Vampire's pathfinding uses standard wall blocking pathing
- [x] `save.py` round-trips `type`
- [x] Unit tests: stat assignment per type, weighted spawn distribution over enough samples, life-steal heal math

**Implementation notes:**
- Configured `MONSTER_STATS` and `MONSTER_SPAWN_WEIGHTS` for Werewolf, Vampire, and Zombie in `src/constants.py`.
- Added weighted selection in `NestManager.pick_monster_type()`.
- Implemented Vampire life-steal in `src/combat.py`.
- Verified in `tests/test_monster_variety.py`.

