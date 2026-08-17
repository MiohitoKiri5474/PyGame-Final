# 10 — HUD: inventory + NPC task display

**What to build:** The HUD (already showing round/phase/timer/pause per the existing skeleton) gains two read-only panels: current inventory totals per resource type, and each NPC's current task (or "idle"). Purely presentational — reads existing state from tickets 02's inventory/task system, no new schema.

**Blocked by:** 02 — Task queue + Gather task

**Status:** done

- [x] HUD displays current inventory totals per resource type, updating live as inventory changes
- [x] HUD displays each NPC's current task type, or "idle" if it has none, updating live as NPCs claim/complete tasks
- [x] Verification: manual play — no unit tests needed for this presentational layer (game.py/rendering stays integration-only per the confirmed test seam); the underlying inventory/task state it reads is already covered by ticket 02's tests

## Implementation notes
Added `items()` method to `Inventory` to enumerate resources with nonzero counts.
Created `hud_display.py` which registers two HUD line providers via `extensions.py`: one for inventory totals and one for NPC tasks.
Registered `hud_display` in `plugins.py` to hook into the import chain.
Added unit tests for the HUD line formatting logic and `Inventory.items()`.
