# 23 — Skill upgrade UI & tree

**What to build:** A keyboard-driven modal (same interaction shape as the existing Priority Table UI — toggle key, arrow-key navigation, closes on Escape/toggle) listing the 6 core skills from `game-detail.md` (Gather Speed, Hunting Accuracy, Taming Ability, Defense Ability, Magic Attack, AoE Attack). Skill levels are a **single global pool** shared by the whole colony, not tracked per-NPC (confirmed decision — game-detail.md's round diagram awards points per-round, not per-NPC-level, and no leveling system exists to hang per-character storage off).

**Blocked by:** 22 — Wave settlement & skill points, 12 — NPC Role System, 18 — Magic framework.

**Status:** done

- [x] New `skills.py` (pygame-free): global `dict[skill_name, level]`, spend-a-point function gated on available points from ticket 22, effect helpers per skill
- [x] New `skill_ui.py` mirrors `priority_ui.py`'s shape: toggle hotkey, lists all 6 skills with current level and points available, arrow-key nav, not itself unit-tested (matches `priority_ui.py` precedent — thin rendering layer over `skills.py`'s tested logic)
- [x] Gather Speed reduces `task.py`'s work-seconds calculation, stacking multiplicatively with Farmer's role multiplier (ticket 12) — not replacing it
- [x] Defense Ability adds a flat +2 defense / +10 max health per level on top of each NPC's role-based base stats (ticket 12)
- [x] Magic Attack (+15% spell damage/level) and AoE Attack (expands Freeze's radius/splash) modify `magic.py`'s cast functions
- [x] Spending is blocked at 0 available points; skill levels persist across saves (`save.py` gains one global skill-level dict, not a per-NPC field)
- [x] Unit tests: point-spend math and gating, each skill's numeric effect at levels 0/1/2

**Implementation notes:**

- Skill levels live on `World` (`world.skills: dict[str, int]`), same placement rationale as `Spellbook` — every consumer that needs to read a skill level (`task.py`, `magic.py`, `hunt_task.py`, `tame_task.py`) already receives `world` as a parameter, so no new plumbing was needed to reach it.
- Toggle key is `K` (not from the ticket's own suggestion, since none was pinned) — checked against every existing binding (`ESC`, `SPACE`, `TAB`, `P`, `F1`/`F2`/`F3`, `1`-`9`, arrow keys/`WASD` for camera pan) and doesn't collide.
- **Defense Ability's mechanics differ slightly from a "read the level live" model**: rather than combat.py dynamically looking up the global skill level every tick (which would require threading `world` into `resolve_combat`, currently just `(npcs, monsters, buildings)`), each point spent on Defense Ability immediately and permanently adds `DEFENSE_BONUS_PER_LEVEL`/`HEALTH_BONUS_PER_LEVEL` to every currently-alive NPC's `defense`/`max_health`/`health`. This matches how every other NPC stat in this codebase already works — set once, mutated directly, never recomputed from world state — and avoids a combat.py signature change. **Known gap**: population growth (ticket 16, not yet merged as of this ticket) spawns new NPCs with only their role-based base stats; those NPCs won't retroactively receive already-spent Defense Ability points unless population.py's spawn path is updated to apply the current total bonus (`skills.defense_bonus_defense`/`defense_bonus_health`) at construction time. Flagged here rather than silently left for someone to discover later.
- **Gather Speed is scoped to the `"Gather"` task type specifically**, not every task type — the skill's name and the ticket's framing ("Gather Speed") both point at gathering specifically, distinct from the already-existing generic per-role `work_multiplier` that already applies to every task type uniformly.
- **Hunting Accuracy** boosts `KNIGHT_CRIT_CHANCE` (the roll threshold, not the crit damage multiplier) by a flat `+10pp/level`, capped at 100%. **Taming Ability** adds a flat `+10pp/level` on top of the (Farmer-multiplied) base tame success rate, also capped at 100% — this fixed a pre-existing minor bug in the taming formula while wiring it in: the old code applied `min(1.0, ...)` to the Farmer-multiplied rate *before* any further bonus could stack on top of an already-capped value; now the cap is applied once, after every additive/multiplicative factor.

**Reconciliation note:** built on a branch stacked on both `feat/combat-depth-reconciled` (tickets 18-21, for `magic.py`) and `feat/wildlife-economy-reconciled` (tickets 15/17/24-27, for `hunt_task.py`/`tame_task.py`) — this ticket's own "Blocked by" list only names 22/12/18, but two more of its six skills (Hunting Accuracy, Taming Ability) needed modules that only exist on the wildlife-economy branch, so building it required merging that branch in first rather than starting fresh off `develop`.

**Code review findings, fixed:**
1. `save.py` didn't persist `npc.max_health` at all - only `npc.health`. Defense Ability's +10 max_health/level bonus survived within a session but was silently discarded on reload (the reconstructed NPC got its role's plain base `max_health` back, with no way to tell it had been bumped - and a saved `health` value from *before* reload could end up exceeding the reloaded `max_health`). Fixed by adding `max_health` to the NPC dump/load dict, falling back to the role-derived default for saves predating this field.
2. Fire's burn DoT wasn't scaled by the Magic Attack multiplier - only its direct hit was, since `on_hit` passed the raw `FIRE_BURN_DAMAGE_PER_TICK` constant straight through. Since burn is a real fraction of Fire's total damage (15 of 25+15=40 at level 0), this meant Fire gained proportionally less per Magic Attack level than Lightning/Freeze's single scaled hit. Fixed by scaling `burn_damage_per_tick` the same way - using `round()` rather than `int()` here specifically, since `FIRE_BURN_DAMAGE_PER_TICK` (5) is small enough relative to the 15%/level step that truncation would silently erase the level-1 bump entirely (5 * 1.15 = 5.75, truncates back to 5).

280 tests pass, smoke_render.py OK.
