# 12 — NPC Role System (Farmer/Knight/Mage)

**What to build:** Every NPC gets a `role`. Starting colony is exactly 1 Farmer / 1 Knight / 1 Mage. Role sets base combat stats (Farmer Atk 8/Def 3, Knight Atk 18/Def 8/HP 140, Mage Atk 22/Def 2/HP 70), Farmer's 0.6x work-seconds multiplier across all task types, and Mage's 3-tile combat range (everyone else stays melee-adjacent). Role shows as a badge color on the NPC sprite and in the hover tooltip.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `NPC` has a `role` field; a named stat table in `constants.py` maps role -> (attack, defense, max_health, combat_range, work_multiplier)
- [ ] Starting `World` spawns exactly 1 Farmer/1 Knight/1 Mage (not random)
- [ ] `task.py`'s `update_npc_tasks` applies the NPC's role work-multiplier to `task_type.work_seconds` (Farmer finishes any task in 0.6x the base time)
- [ ] `combat.py`'s `resolve_combat` uses each NPC's own combat range instead of the flat `COMBAT_RANGE` constant (Mage engages from 3 tiles, others stay melee-adjacent)
- [ ] `game.py` renders a role-colored badge on NPCs and includes role in the hover tooltip (additive change, no restructuring of existing render/hover code)
- [ ] `save.py` round-trips `role`; unit tests cover stat lookup, work multiplier, and combat range per role
