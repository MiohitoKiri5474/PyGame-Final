# 26 — Post-hunt: food vs. taming

**What to build:** After a Hunt kill, the player chooses between "Process for Food" (credits meat to the colony inventory) and "Tame" (a Farmer attempts to tame the animal at 1.5x success rate and speed vs. other roles; a tamed animal is placed in a new Animal Pen building for passive production — Horse grants a travel-speed utility as the simplest viable form, not milk/eggs/meat).

**Blocked by:** 25 — Hunt task, 15 — House & population cap (Animal Pen reuses the same build-task pattern). Soft dependency on 23 — Skill Upgrade UI (the Taming Ability skill boosts this further, but base taming works without it).

**Status:** ready-for-agent

- [ ] New `tame_task.py`: `Tame` task type, plus a new Animal Pen building registered via the standard build-task pattern (like House)
- [ ] "Process for Food" credits meat to inventory and removes the animal
- [ ] "Tame" success rate/speed is 1.5x for Farmer NPCs vs. other roles (base rate/speed named constants)
- [ ] A tamed-but-not-yet-penned animal doesn't crash or silently vanish — it waits until a Pen is available or is handled with a defined fallback
- [ ] Penned Horse provides a defined travel-speed utility effect (simplest viable implementation, not the full milk/eggs/meat production loop)
- [ ] Pen production (for species that do produce food) ticks via `extensions.register_tick`
- [ ] `save.py` persists tamed animals and pen occupancy
- [ ] Unit tests: food-credit path, tame success-rate math by role, pen production tick
