# 15 — House building & population cap

**What to build:** House reuses the Wall/Tower build-task pattern exactly (place on any claimed empty tile, cost + work-seconds, no adjacency rules). Each built House raises the population cap by 1, on top of a base cap of 3.

**Blocked by:** 14 — Expanded material taxonomy (House's cost references Wood/Bricks).

**Status:** ready-for-agent

- [ ] `BuildHouse` task type registered via `build_task.py`'s existing pattern, reusing the current `Building` dataclass (no new fields needed for House itself)
- [ ] House can be queued only on a claimed, empty, resource-free tile — same rule as Wall/Tower
- [ ] `population_cap(world)` helper returns `BASE_POPULATION_CAP + count of House buildings`, exposed for ticket 16
- [ ] Unit tests mirror `test_build.py`'s shape (can_queue rules, on_complete spend/build) plus cap math at 0/1/2 houses
