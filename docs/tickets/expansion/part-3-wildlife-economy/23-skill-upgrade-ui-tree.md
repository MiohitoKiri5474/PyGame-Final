# 23 — Skill upgrade UI & tree

**What to build:** A keyboard-driven modal (same interaction shape as the existing Priority Table UI — toggle key, arrow-key navigation, closes on Escape/toggle) listing the 6 core skills from `game-detail.md` (Gather Speed, Hunting Accuracy, Taming Ability, Defense Ability, Magic Attack, AoE Attack). Skill levels are a **single global pool** shared by the whole colony, not tracked per-NPC (confirmed decision — game-detail.md's round diagram awards points per-round, not per-NPC-level, and no leveling system exists to hang per-character storage off).

**Blocked by:** 22 — Wave settlement & skill points, 12 — NPC Role System, 18 — Magic framework.

**Status:** ready-for-agent

- [ ] New `skills.py` (pygame-free): global `dict[skill_name, level]`, spend-a-point function gated on available points from ticket 22, effect helpers per skill
- [ ] New `skill_ui.py` mirrors `priority_ui.py`'s shape: toggle hotkey, lists all 6 skills with current level and points available, arrow-key nav, not itself unit-tested (matches `priority_ui.py` precedent — thin rendering layer over `skills.py`'s tested logic)
- [ ] Gather Speed reduces `task.py`'s work-seconds calculation, stacking multiplicatively with Farmer's role multiplier (ticket 12) — not replacing it
- [ ] Defense Ability adds a flat +2 defense / +10 max health per level on top of each NPC's role-based base stats (ticket 12)
- [ ] Magic Attack (+15% spell damage/level) and AoE Attack (expands Freeze's radius/splash) modify `magic.py`'s cast functions
- [ ] Spending is blocked at 0 available points; skill levels persist across saves (`save.py` gains one global skill-level dict, not a per-NPC field)
- [ ] Unit tests: point-spend math and gating, each skill's numeric effect at levels 0/1/2
