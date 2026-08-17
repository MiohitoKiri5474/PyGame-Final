# 01 — NPC entity + pathfinding + render

**What to build:** NPCs exist as entities in the simulation, spawn on the claimed starting territory when a new game begins, and render on the scrolling map. As a temporary interaction (to be replaced by the task system in ticket 02), the player can click a claimed/walkable tile to command a selected NPC to walk there — the NPC follows a real A* path across the grid (never through fog, never off claimed/walkable tiles), moving with continuous pixel motion rather than instant tile-snapping.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] NPC entity has position, and spawns at/near the starting claimed area on new game
- [x] NPCs render on the map at their current position, correctly offset by the scrolling camera
- [x] A* pathfinding module computes a path across the grid respecting claimed/walkable tiles (pure Python, no pygame import — this is the confirmed test seam)
- [x] NPC given a move-to target walks the computed path with continuous pixel movement (not teleporting tile-to-tile)
- [x] Clicking a valid claimed tile while an NPC is selected issues the move-to command
- [x] Unit tests cover: path avoids unclaimed/unwalkable tiles, path from A to B on a known small grid matches expected route or route length, NPC position updates toward path waypoints over successive ticks

**Implementation notes:** coordinate conversion centralized in `coords.py` (`tile_center`/`tile_at`) so pathfinding, movement, and click-handling all agree on grid↔pixel space — needed by later tickets (06 adjacency, 04 placement, 11 serialization). `pathfinding.py` takes an `is_walkable(x, y)` callback rather than a `Grid`, decoupling it from grid generation for testing. Selection is click-on-NPC (no drag-select/hotkeys yet, not required by this ticket).
