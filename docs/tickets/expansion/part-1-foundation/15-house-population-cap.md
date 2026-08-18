# 15 — House building & population cap

**What to build:** House reuses the Wall/Tower build-task pattern exactly (place on any claimed empty tile, cost + work-seconds, no adjacency rules). Each built House raises the population cap by 1, on top of a base cap of 3.

**Blocked by:** 14 — Expanded material taxonomy (House's cost references Wood/Bricks).

**Status:** done

- [x] `BuildHouse` task type registered via `build_task.py`'s existing pattern, reusing the current `Building` dataclass (no new fields needed for House itself)
- [x] House can be queued only on a claimed, empty, resource-free tile — same rule as Wall/Tower
- [x] `population_cap(world)` helper returns `BASE_POPULATION_CAP + count of House buildings`, exposed for ticket 16
- [x] Unit tests mirror `test_build.py`'s shape (can_queue rules, on_complete spend/build) plus cap math at 0/1/2 houses

**Implementation notes:** `HOUSE_COST = {"wood": 4, "bricks": 2}`, 4.0s work, per `todo.md`'s spec. Reuses `_can_queue`/`_try_build` verbatim (same claimed-empty-resource-free rule, same atomic `Inventory.spend_all` path) — only `_can_perform_house`/`_on_complete_house` are new, identical shape to Wall/Tower's pair. `population_cap(world)` lives in `build_task.py` next to House's own registration (it's directly about counting House buildings, not a separate concern) and is a plain function ticket 16 imports directly. Also fixed `render_buildings.py`'s color lookup: it was a two-way ternary (`Wall` vs. everything-else-is-Tower-colored), which would have silently painted every House Tower-blue; replaced with a `_COLOR_BY_TYPE` dict.

**`/code-review medium` fixes:**
1. The `_COLOR_BY_TYPE.get(building.type, COLOR_TOWER)` fallback reproduced the exact bug it was meant to fix — any future building type left out of the dict (Farmland/Animal Pen are both coming in later tickets) would still silently render Tower-blue. Fixed: fallback is now `COLOR_UNKNOWN_BUILDING` (magenta), an unmistakable "missing mapping" marker instead of a plausible-looking wrong color.
2. `_can_perform_wall`/`_can_perform_tower`/`_can_perform_house` were three copies of the identical afford-check, differing only in which cost dict they closed over. Extracted a shared `_can_afford(world, cost)`, all three now call it.
