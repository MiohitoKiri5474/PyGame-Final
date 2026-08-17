# Core Loop tickets — 3-part split

Source: `docs/spec-core-loop.md`. 11 tickets, grouped into 3 parts so up to 3 people can work in parallel without stepping on each other. Each ticket file still has its own "Blocked by" — the grouping below is ownership/parallelism, not a replacement for those edges.

## part-1-foundation-economy/

01 → 02 → {03, 04, 10}, then 05 (needs 03 + 04). Sequential chain — NPCs/pathfinding/render, then the task queue + Gather/Expand/Build tasks, buildings, priority UI, and the inventory/task HUD. **01 blocks Part 2's ticket 06 too** — land it first regardless of who owns which part.

## part-2-combat-survival/

06 (needs only 01) → 07 (also needs 04 from Part 1) → 09. 08 only needs 01. Can start as soon as 01 is done, in parallel with the rest of Part 1 — 07 is the one ticket here that also waits on Part 1's 04 (Wall/Tower).

## part-3-persistence/

11 — save/load checkpoint. Blocked by 01, 02, 04, 05, 06, 08, i.e. by most of Part 1 and Part 2. Naturally the last ticket to land; whoever owns it can scaffold the serialization module early but can't finish/verify the round-trip until both other parts are done.

## Suggested parallelization

- One person: Part 1 (01 first, solo — it blocks everyone else).
- Once 01 lands: second person picks up Part 2 while the first continues Part 1's 02→05 chain.
- Part 3 owner scaffolds early, finishes once both land.
