# Spec: Core Loop (Build Order Step 1)

Status: ready-for-agent
Source: grilling session recorded in `game-detail.md` § Implementation Decisions and `CLAUDE.md` § Architecture Decisions.

## Problem Statement

The Lord (player) currently has a map they can look at (grid with fog-of-war, scrollable camera, day/night timer, pause) but no way to actually play the game: no NPCs to command, no way to queue work, nothing to build, nothing to fight, and no resources to collect. Without this, there is no playable loop — the project is a screensaver, not a game.

## Solution

Build the minimum playable colony loop: NPCs exist and move around the claimed territory, the Lord can queue tasks (gather, build, expand) that NPCs pick up according to their own priority ranking, gathered resources land in a shared inventory, defensive buildings (Wall, Tower) can be placed and fought over automatically when monsters arrive at night, and progress survives a restart via a day-boundary checkpoint save.

This is Build Order Step 1 from `game-detail.md` — the foundation every later step (roles, combat depth, magic/taming/skills) builds on top of.

## User Stories

1. As the Lord, I want to see NPCs standing in my claimed territory when a new game starts, so that I know who I'm commanding.
2. As the Lord, I want an NPC to walk from its current position to a target tile along a real path (not through fog, not off the claimed/walkable grid), so that movement looks and feels correct on the scrolling map.
3. As the Lord, I want to click a claimed tile and choose an action (Gather, Build Wall, Build Tower, Expand Territory), so that I can direct my colony's work.
4. As the Lord, I want the action I chose to become a task in a shared queue, so that any available NPC can eventually do it.
5. As the Lord, I want each NPC to pick its next task by its own priority ranking over task types, so that NPCs specialize in what I've told them to prefer, per the ONI-style per-NPC priority table decision.
6. As the Lord, I want to open a priority screen and reorder task-type priority per NPC, so that I can express "this NPC prefers building over gathering."
7. As the Lord, I want an idle NPC (no current task) to automatically claim the highest-priority available task it's ranked for, so that I don't have to hand-assign every action.
8. As the Lord, I want an NPC executing a Gather task to walk to the resource tile, spend some time gathering, and have the resource removed from the tile, so that gathering feels like real work, not an instant menu click.
9. As the Lord, I want gathered resources to appear immediately in a shared inventory total (not as ground items), so that I can see what I have without managing hauling.
10. As the Lord, I want an NPC executing an Expand Territory task to walk to a frontier tile and, on completion, reveal fog and claim tiles in a radius around it, so that my territory grows through NPC work rather than instantly.
11. As the Lord, I want an NPC executing a Build task to walk to the target claimed+empty tile, spend build time there, consume the required resources from inventory, and place the building on completion, so that building costs something and takes NPC time.
12. As the Lord, I want to place a Wall or a Tower on any claimed empty tile with no adjacency/connectivity requirement, so that I have full freedom over my defensive layout (per the "free placement" decision).
13. As the Lord, I want each building to have distinct stats (Wall = high block/no attack, Tower = ranged attack, low block), so that my building choices have different tactical value.
14. As the Lord, I want a build task to fail gracefully (stay queued, or report insufficient resources) if the inventory doesn't have enough resources when an NPC reaches the site, so that I'm not silently blocked without feedback.
15. As the Lord, I want night to trigger monster spawns from existing nests, so that the round has stakes.
16. As the Lord, I want existing nests to spawn monsters at an increasing rate as rounds progress, so that difficulty escalates over a session.
17. As the Lord, I want new nests to be able to appear over time (not just the ones present at map generation), so that the threat keeps growing across a long session.
18. As the Lord, I want spawned monsters to path toward my claimed territory using the same movement system NPCs use, so that behavior is consistent and monsters can be blocked by Walls/terrain like anything else on the grid.
19. As the Lord, I want any NPC or Tower within range of an adjacent monster to automatically fight it (stat-based, no manual targeting), so that I don't have to micromanage every attack.
20. As the Lord, I want a Wall to block monster advance (monsters can't path through/destroy it in step 1) so that Walls are a meaningful defensive choice distinct from Towers.
21. As the Lord, I want an NPC's health to drop when a monster attacks it, and the NPC to die (removed from play) at 0 health, so that combat has real consequences.
22. As the Lord, I want an NPC's hunger to deplete over time and the NPC to die if hunger runs out, so that food/gathering matters even without combat.
23. As the Lord, I want the game to declare game-over when all NPCs are dead, so that the endless-survival loop has a clear end state.
24. As the Lord, I want to see the current round count as my score when the game ends, so that I know how well I did (endless-survival scoring, no fixed win state).
25. As the Lord, I want the game to auto-save a checkpoint at each day/night boundary, so that I don't lose meaningful progress.
26. As the Lord, I want to load the most recent checkpoint on next launch (or start a fresh game if none exists), so that a session can be resumed.
27. As the developer, I want the saved checkpoint to capture exactly what "day boundary" state means (grid claim/fog/resources, NPC positions/health/hunger, inventory, buildings, nests, round number, phase) so that a reload is indistinguishable from having paused there.
28. As the Lord, I want the HUD to show my current inventory totals, so that I know what I have before queuing a Build task.
29. As the Lord, I want the HUD to show each NPC's current task (or "idle"), so that I can tell whether my colony is being productive.
30. As the developer, I want task-queue, NPC, building, combat, and save logic to live in pygame-free pure-Python modules, so that they're directly unit-testable without a display or event loop (the confirmed test seam).

## Implementation Decisions

**New modules** (pygame-free, alongside the existing `grid.py`, `camera.py`, `day_night.py`):
- Task/queue module: task representation, the global queue, per-NPC priority ranking, and the idle-NPC claim algorithm (pick highest-ranked task type among currently queued/available tasks).
- NPC module: NPC entity (position, health, hunger, current task, priority ranking), pathfinding integration, and per-tick update (move toward task target, execute task once adjacent/on-site, apply hunger decay).
- Pathfinding module (or function set): A* over the grid, respecting claimed/walkable tiles and blocking buildings (Walls). Shared by NPCs and monsters.
- Building module: Building entity (type, position, stats), placement validation (claimed + empty tile only, no adjacency rule), and the block/attack behavior Walls and Towers contribute to combat.
- Inventory module: a shared resource-count store (dict-like: resource type → count), with add/spend operations; spend must be atomic/checked (no negative balances).
- Combat module: proximity-based auto-engage resolution — each tick, for NPCs/Towers adjacent to a monster (and vice versa), apply stat-based damage; handle NPC death and monster death.
- Nest/monster spawn module: nest entities placed at map generation, spawn-rate schedule that ramps with round number, and the rule for new nests appearing over time (exact rate/cap is a tunable constant, not fixed by this spec — expose it as a named constant so balance is a one-line change).
- Save module: serialize/deserialize the full simulation state (grid, NPCs, buildings, inventory, nests, round/phase/timer) to a single checkpoint file; save is called only at the day/night phase boundary (hook into `DayNightCycle`'s phase transition), never mid-tick.

**Task lifecycle** (decision-precise shape, informed by what's already built):
```
Task: { type: Gather | BuildWall | BuildTower | Expand, target_tile: (x, y), assigned_npc: NPC | None, progress: float }
Queue: list[Task]  # unassigned or in-progress, tasks are removed on completion
```
An idle NPC scans the queue for tasks whose type is unassigned, picks the highest-priority type (per that NPC's own ranking) among those available, and assigns itself.

**NPC per-tick behavior**: if no task, look for one (see above); if has task and not at target, path/move toward target; if at target, accumulate task-specific work time, then apply the task's effect (remove resource + inventory credit, reveal/claim radius, or consume resources + place building) and clear the task.

**Combat resolution**: no projectile/animation system in step 1 — damage applies directly on the tick two hostile entities are adjacent, using flat or simple stat formulas (attack − defense, floored at some minimum). Exact numbers are balance constants, not part of this spec's contract.

**Priority table UI**: a screen/overlay listing NPCs with a reorderable list of task types per NPC — exact widget implementation is free, but the underlying data model is "ordered list of task types per NPC," queried by the task-claim algorithm.

**Save format**: implementation is free (JSON, pickle, etc.) as long as it fully round-trips the state listed in User Story 27 and is only ever written/read at a phase boundary.

**Out-of-band from this spec but referenced**: Grid, Camera, DayNightCycle, and the pause/render loop already exist (`src/grid.py`, `src/camera.py`, `src/day_night.py`, `src/game.py`) and are not being redesigned — new modules integrate with them, not replace them.

## Testing Decisions

- Good tests here assert externally observable state transitions (task completes → inventory increases by the right amount and resource tile clears; NPC reaches 0 health → removed from NPC list; day boundary crossed → save file written with expected round number) — not internal call counts or private helper behavior.
- Modules under test: task/queue claim algorithm, NPC per-tick state machine (idle → moving → working → task complete), pathfinding correctness (respects claimed/walkable + Wall blocking), building placement validation, inventory add/spend (including insufficient-funds rejection), combat damage resolution and death handling, nest spawn-rate scheduling, and save/load round-trip.
- Prior art in this repo: none yet — no test suite exists. `Grid`, `Camera`, and `DayNightCycle` are already pygame-free and were only verified via an ad-hoc headless smoke script (`SDL_VIDEODRIVER=dummy` + manual `update()`/`render()` calls), not pytest. This spec's modules should be the first to get real pytest coverage, following the same "no pygame import" pattern those three already establish.
- `game.py` (window, event loop, rendering, camera pan input) stays integration-only per the confirmed seam — covered by manual play and the existing headless smoke script, not unit tests.

## Out of Scope

- NPC roles (Farmer/Knight/Mage stat differentiation) — Build Order Step 2.
- Deepened combat (manual targeting, projectiles/animation), magic spells, nest placement beyond a simple ramp — Build Order Step 3.
- Taming, skill-tree upgrade UI, food spoilage — Build Order Step 4.
- Haul tasks, ground items, storage buildings — explicitly rejected in the grilling session (instant global inventory instead).
- Manual attack targeting or spell-casting — not part of step 1 (base combat is fully automatic; spells are step 3).
- Any save format beyond a single checkpoint slot (no save slots/versioning UI).
- Character population cap enforcement — still an open decision (see `CLAUDE.md`), not implemented here; the +1-NPC-every-3-rounds growth can proceed uncapped for step 1.

## Further Notes

- All resource/build-cost/damage numeric values referenced above (build costs, gather time, spawn rate, attack/defense numbers, starting NPC count/positions) are tunable balance constants. This spec defines the systems and their contracts, not the final numbers — pick sane defaults during implementation and keep them as named constants (matching the existing `constants.py` pattern) so they're one-line changes.
- No issue tracker is configured for this repo (no `/setup-matt-pocock-skills` run, no remote configured) — this spec is recorded directly in `docs/` instead of being published as a tracked issue, per explicit request.
