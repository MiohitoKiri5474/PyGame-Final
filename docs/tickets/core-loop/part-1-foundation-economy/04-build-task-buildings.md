# 04 — Build task + Wall/Tower buildings

**What to build:** Building entities (Wall, Tower) with distinct stats (Wall: high block, no attack; Tower: ranged attack, low block). The player places a building by clicking any claimed, empty tile and choosing Wall or Tower — no adjacency/connectivity placement rule. This queues a Build task reusing the ticket 02 task infrastructure. An idle, ranked NPC claims it, paths to the site, spends build time, then — if the inventory has enough resources — spends them and places the building. If resources are insufficient when the NPC arrives, the task stays queued/reports insufficiently-funded rather than silently vanishing.

**Blocked by:** 02 — Task queue + Gather task

**Status:** done

- [x] Building entity: type (Wall/Tower), position, stats (block value, attack value — Tower/Wall differ per the spec)
- [x] Building placement validation: claimed + empty tile only, any placement accepted (no adjacency/perimeter/line-of-sight checks)
- [x] BuildWall and BuildTower registered as task types
- [x] Clicking a valid tile + choosing a building type queues the corresponding Build task
- [x] Inventory module gains a spend operation that is atomic/checked — never allows a negative balance
- [x] NPC with an assigned Build task paths to the site, spends build time, then: if inventory covers the cost, resources are spent and the building is placed; if not, the task remains queued and reports insufficient resources rather than failing silently
- [x] Unit tests cover: placement validation (rejects unclaimed/occupied tiles, accepts any claimed empty tile regardless of neighbors), full Build task lifecycle with sufficient funds places the building and deducts inventory, insufficient funds leaves task queued and inventory untouched

**Implementation notes:**
- `src/constants.py` was updated with Wall and Tower stats, costs, build times, and display colors.
- `src/world.py` now includes a `buildings` list in the `World` entity.
- Created `src/build_task.py` which contains the `Building` dataclass, handles the `BuildWall` and `BuildTower` task validation and behavior, and registers the tasks.
- Created `src/render_buildings.py` to draw the buildings on the screen, registered as an overlay using `extensions`.
- `plugins.py` imports `build_task`, which in turn safely loads the render overlay callback.
- Tests covering all scenarios were added in `tests/test_build.py`.
