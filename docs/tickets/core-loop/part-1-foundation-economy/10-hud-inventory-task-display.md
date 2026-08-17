# 10 — HUD: inventory + NPC task display

**What to build:** The HUD (already showing round/phase/timer/pause per the existing skeleton) gains two read-only panels: current inventory totals per resource type, and each NPC's current task (or "idle"). Purely presentational — reads existing state from tickets 02's inventory/task system, no new schema.

**Blocked by:** 02 — Task queue + Gather task

**Status:** ready-for-agent

- [ ] HUD displays current inventory totals per resource type, updating live as inventory changes
- [ ] HUD displays each NPC's current task type, or "idle" if it has none, updating live as NPCs claim/complete tasks
- [ ] Verification: manual play — no unit tests needed for this presentational layer (game.py/rendering stays integration-only per the confirmed test seam); the underlying inventory/task state it reads is already covered by ticket 02's tests
