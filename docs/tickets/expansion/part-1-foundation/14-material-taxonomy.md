# 14 — Expanded material taxonomy & recipe updates

**What to build:** Grid tiles yield Wood/Marble/Bricks (construction materials) and Berries/Raw Stone (magic materials) alongside the existing wild resource, each with its own spawn weight. `WALL_COST`/`TOWER_COST` move off the placeholder `{"crop": N}` onto real material recipes.

**Blocked by:** None — parallel-safe with ticket 12 (no shared files).

**Status:** ready-for-agent

- [ ] `Grid.__init__`'s single `RESOURCE_CHANCE` roll is replaced by a named weighted table in `constants.py` covering all 5 new resources (plus the existing one)
- [ ] `WALL_COST`/`TOWER_COST` reference real materials (e.g. Wood/Bricks), not `crop`
- [ ] No change needed in `gather_task.py` — its `on_complete` already does `world.inventory.add(tile.resource, GATHER_YIELD)` generically; a test confirms gathering each new resource type credits inventory correctly with zero `gather_task.py` edits
- [ ] Out of scope: the hardcoded `world.inventory.spend("crop", 1)` hunger-eat line in `task.py` — that becomes food-aware in ticket 27, not here
- [ ] Unit tests cover: weighted generation produces all resource types over enough tiles, updated build costs are spent correctly on task completion
