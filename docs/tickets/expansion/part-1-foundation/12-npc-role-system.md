# 12 — NPC Role System (Farmer/Knight/Mage)

**What to build:** Every NPC gets a `role`. Starting colony is exactly 1 Farmer / 1 Knight / 1 Mage. Role sets base combat stats (Farmer Atk 8/Def 3, Knight Atk 18/Def 8/HP 140, Mage Atk 22/Def 2/HP 70), Farmer's 0.6x work-seconds multiplier across all task types, and Mage's 3-tile combat range (everyone else stays melee-adjacent). Role shows as a badge color on the NPC sprite and in the hover tooltip.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] `NPC` has a `role` field; a named stat table in `constants.py` maps role -> (attack, defense, max_health, combat_range, work_multiplier)
- [x] Starting `World` spawns exactly 1 Farmer/1 Knight/1 Mage (not random)
- [x] `task.py`'s `update_npc_tasks` applies the NPC's role work-multiplier to `task_type.work_seconds` (Farmer finishes any task in 0.6x the base time)
- [x] `combat.py`'s `resolve_combat` uses each NPC's own combat range instead of the flat `COMBAT_RANGE` constant (Mage engages from 3 tiles, others stay melee-adjacent)
- [x] `game.py` renders a role-colored badge on NPCs and includes role in the hover tooltip (additive change, no restructuring of existing render/hover code)
- [x] `save.py` round-trips `role`; unit tests cover stat lookup, work multiplier, and combat range per role

**Implementation notes:** `role: str | None = None` on `NPC` — `None` keeps every existing flat-constant default (`NPC_ATTACK`/`NPC_DEFENSE`/`NPC_MAX_HEALTH`/`COMBAT_RANGE`/1.0x work) byte-for-byte, so none of the ~130 pre-existing tests needed touching for behavior, only `test_combat.py`'s `_Entity` fixture needed a `combat_range` field added (it was standing in for the real `NPC` interface, which combat.py now reads `npc.combat_range` from). `World.__init__` assigns roles via `ROLES[i % len(ROLES)]`, giving exactly 1/1/1 at the default `STARTING_NPC_COUNT=3` while leaving `npc_count=0`/other counts (used throughout the test suite) unaffected. Added `NPC.max_health` (didn't exist before — health was always compared against the flat `NPC_MAX_HEALTH` constant) since per-role health now varies; this also fixes a display bug in `game.py`'s hover tooltip, which was dividing every NPC's current health by the flat constant regardless of role (harmless while every NPC had the same max health, wrong the moment Knight/Mage exist).

