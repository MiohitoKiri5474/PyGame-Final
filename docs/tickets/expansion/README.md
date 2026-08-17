# Expansion tickets — todo.md feature breakdown

Source: `todo.md` (Figma export) + `game-detail.md`. 16 tickets (12-27, continuing the numbering from `docs/tickets/core-loop/`'s 01-11), grouped into 3 parts so multiple people can work in parallel without stepping on each other. todo.md's Phase 8 (save/load) is already done — ticket 11, merged as PR #13 — and isn't repeated here.

Full design rationale, architecture notes, and the 4 confirmed open-design decisions (global skill pool, Hunt re-paths a snapshotted tile, magic casts colony-wide, Farmland ships now) live in the plan this epic was generated from: `~/.claude/plans/polymorphic-seeking-quiche.md`.

**Branch strategy**: every ticket branches fresh off `develop`, never off `feat/tile-inspect-and-skip-blocked-tasks` (that branch predates ticket 11 and is missing `save.py` — unrelated pre-existing scope, not a base for this epic).

## part-1-foundation/

12 (Role System) and 14 (Material Taxonomy) can start immediately in parallel — no shared files. 13 (Per-Tick Hook) is also independent. Then: 14 → 15 (House) → 16 (Population Growth, also needs 12). 17 (Farmland) needs 13 + 14. This part is the backbone nearly everything else depends on for roles/materials/the tick hook.

## part-2-combat-depth/

18 (Magic + Lightning, needs 13 + 12) → 19 (Fire) and 20 (Freeze) can both follow 18 in parallel with each other — but 21 (Monster Variety) must come **after** 20, not parallel with it: both touch `combat.py`'s attack resolution and `monster.py`'s fields.

## part-3-wildlife-economy/

22 (Wave Settlement) is independent — only needs the `transitioned` bool from ticket 11, already merged. 23 (Skill UI) needs 22 + 12 + 18. 24 (Wildlife) is independent of everything else. 25 (Hunt) needs 24. 26 (Post-Hunt/Taming) needs 25 + 15 (Animal Pen reuses House's pattern). 27 (Food Spoilage) needs 17 + 26 — it's the natural last ticket, same role ticket 11 played for core-loop.

## Suggested parallelization

- Part 1: one person on 12+13+14 (all independent, pick any order), converging on 15→16→17.
- Part 2 can't start meaningfully until 12+13 land (needs a Mage role and the tick hook) — second person picks it up once those two are in.
- Part 3's 22 and 24 can start immediately, in parallel with Part 1 — 23/25/26/27 wait on their specific blockers as noted above.
