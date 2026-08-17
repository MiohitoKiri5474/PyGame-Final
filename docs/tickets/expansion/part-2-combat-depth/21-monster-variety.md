# 21 — Monster variety (Werewolf/Vampire/Zombie)

**What to build:** `Monster.type` drives per-type stat presets — Werewolf (fast, 80px/s, 50 HP, 14 attack), Zombie (slow, 40px/s, 90 HP, high building-siege damage), Vampire (high speed, life-steals on hit, avoids/deprioritizes Wall-adjacent routing). `NestManager` picks a weighted monster type per spawn instead of always spawning the same stat block.

**Blocked by:** 20 — Freeze spell. Sequenced, not parallel: both this and Freeze touch `combat.py`'s attack resolution and add fields to `monster.py` — land Freeze first to avoid a hand-resolved merge conflict on the same functions.

**Status:** ready-for-agent

- [ ] `Monster` gains a `type` field; a named stat table in `constants.py` maps type -> (speed, max_health, attack, defense, special)
- [ ] `NestManager`'s spawn factory picks a weighted type per spawn (named weight constants)
- [ ] Vampire heals itself on dealing damage, same tick as the hit (life-steal), in `combat.py`
- [ ] Vampire's pathfinding deprioritizes/avoids routing adjacent to Wall buildings (Werewolf/Zombie unaffected, same pathing as today)
- [ ] `save.py` round-trips `type`
- [ ] Unit tests: stat assignment per type, weighted spawn distribution over enough samples, life-steal heal math
