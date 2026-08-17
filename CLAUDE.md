# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

Ticket 01 (NPC entity + pathfinding + render) implemented. See `docs/tickets/core-loop/` for the remaining tickets and their blocking order.

## Environment

- Python 3.13.3 (pyenv), venv at `venv/`
- Deps: `pygame==2.6.1`, `pytest`, tracked in `requirement.txt` (via `pip freeze`)

```bash
source venv/bin/activate
pip install -r requirement.txt   # after clone
pip freeze > requirement.txt     # after adding a new dep

python src/main.py                       # run the game
pytest                                    # unit tests (pure-Python sim modules only, see seam below)
python tests/smoke_render.py              # headless integration smoke check for game.py
```

## Design Reference

`game-detail.md` is the source of truth for game design and is actively maintained by hand — do not overwrite it, only read.

## Git Workflow

- Branch structure: `main` → `develop` → `feat/*`/`fix/*`. `develop` is the mother branch every feature/fix branch cuts from and merges back into — `main` does not take feature work directly.
- No direct commits to `develop` or `main` from feature work. Every change goes through a `feat/`/`fix/` branch + PR into `develop`.
- Branch naming: `type/short-desc` (e.g. `feat/task-queue`, `fix/tile-render`). `type` matches commit types below.
- One branch = one logical change. Rebase/update from `develop` before opening PR if it's gone stale.

### Commits

- Conventional commit format: `type: description` (types: feat, fix, refactor, docs, test, chore, perf, ci) — see global `~/.claude/rules/common/git-workflow.md`.
- End every commit and PR body with `Disclosure: Based on Claude Code generated output.`

### PRs

- After a feature/fix is implemented, open a PR from its branch into `develop` — not `main`. Comprehensive summary + test plan (see global `git-workflow.md` for the exact template).
- Add Copilot as reviewer on open, and again after every push that addresses feedback. Do not merge with unresolved Copilot comments.
- Squash or keep history clean per branch before merge — reviewer's call, not enforced here.
- `develop` → `main` promotion (releases) is a separate, deliberate step, not part of the per-feature PR flow.

## Scope & Deadline

**1 week**, solo. Aiming for full `game-detail.md` scope but build in this order, cut from the tail if time runs out:

1. Core loop: grid, fog/claim, task queue + per-NPC priority table, 1 generic NPC, day/night timer, Wall/Tower, auto-combat, gather→inventory. Save/load (checkpoint at day boundary) goes in alongside this step — bolting serialization on later is worse than building it in from the start.
2. Role split (Farmer/Knight/Mage stats)
3. Combat depth (A* monster movement, nest spawn ramp, magic)
4. Taming, skill-tree upgrades, food spoilage polish

## Architecture Decisions

Resolved via grilling session, not yet all implemented — check `Project Status` / actual source for what exists vs. what's still planned.

**Core loop**: real-time simulation, pausable (pause freezes sim, not input/camera). Day/night on a fixed timer (~2min day, ~1min night), not player-triggered. Post-round: player picks 1-of-3 skill upgrade per leveled-up NPC. No win condition — endless survival, score = rounds survived. Loss: all NPCs dead (health or starvation).

**Map**: large fixed-size grid, procedurally generated once at new-game start, scrolling camera (viewport smaller than grid). Fog-of-war: "Expand territory" task reveals fog AND claims tiles as buildable in one action. Buildings: free placement on any claimed empty tile, no adjacency/line-of-sight validation.

**NPCs & movement**: continuous pixel movement + A* pathfinding (not tile-stepped). 3 roles (Farmer/Knight/Mage) per `game-detail.md` stats. Start with 3 NPCs, +1 every 3 rounds — population cap is **deferred/TBD**, will likely tie to House count later. Tasks: global queue, per-NPC priority table (full ONI-style, not one shared list) — idle NPCs auto-claim by their own ranking. Gathered resources go straight to a global inventory — no haul task, no ground items, no storage buildings.

**Combat**: night monster spawn from nests (dynamic — new nests can appear over time, not just fixed at map gen; exact cap/rate is a tunable default, not yet locked). Monsters path to territory via the same A* system. Base combat is auto-engage-by-proximity, stat-based — no manual attack targeting. Watch/shift duty from the doc is flavor only, not a separate assignable task; any nearby NPC auto-defends. Magic: 3 spells (Fire/Lightning/Freeze), cooldown-based (no mana bar), auto-targets nearest threat on cast — this is the only place combat is "reactive" (player triggers the cast).

**Art**: primitive shapes + color coding via `pygame.draw`, no sprite assets. Keep all drawing centralized so swapping in real sprites later doesn't touch game logic.

**Test seam**: `grid.py`, `camera.py`, `day_night.py`, `coords.py`, `pathfinding.py`, `npc.py` are pygame-free pure Python — unit tested directly with pytest. `game.py` is the pygame-coupled integration shell (window, event loop, rendering, click handling) — not unit tested, verified via `tests/smoke_render.py` (headless, `SDL_VIDEODRIVER=dummy`) plus manual play. Keep new simulation modules (tasks, buildings, combat, save) on the pygame-free side of this line.

**Not yet built** (source doesn't exist for these): task queue, buildings, combat, magic, taming, skills, save/load. NPC entity + A* pathfinding + click-to-select/move exist (ticket 01).
