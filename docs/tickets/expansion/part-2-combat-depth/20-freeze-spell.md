# 20 — Freeze spell

**What to build:** `F3`, 25s cooldown, freezes/slows every monster in a 3x3 tile radius around the nearest threat for 4 seconds, stopping their advance. First spell that affects movement rather than just dealing damage.

**Blocked by:** 18 — Magic framework + Lightning spell.

**Status:** done

- [x] `cast_freeze` in `magic.py` reuses the cast/cooldown scaffolding from ticket 18, with a 3x3-tile-radius query around the nearest-threat tile instead of single-target
- [x] `monster.py` gains a `frozen_until` timestamp/timer field
- [x] `Monster.update`'s movement step is skipped (or halved, pick one and note it in code) while `frozen_until` is active
- [x] Re-hitting an already-frozen monster refreshes `frozen_until` rather than stacking/extending indefinitely
- [x] `save.py` round-trips `frozen_until`
- [x] Unit tests: AoE correctly includes tiles inside the 3x3 and excludes tiles outside it, frozen monster doesn't advance its path until expiry, refresh-not-stack on re-hit

**Implementation notes:** Named the field `frozen_remaining` (a countdown float, ticked down by `dt` each `update()`), not `frozen_until` — this codebase has no absolute/wall-clock game-time counter anywhere (every timer is a dt-accumulated countdown or count-up, e.g. `DayNightCycle.timer`, `Nest.spawn_timer`, ticket 19's `burn_tick_timer`), so a "until" timestamp would need a clock reference that doesn't exist. Movement is **skipped entirely** while frozen (`Monster.update` returns right after ticking burn/freeze, before the `step_toward_path` call), not halved — simpler, and "stopping their advance" in the ticket's own wording reads as a full stop. `apply_freeze(duration)` overwrites `frozen_remaining` rather than adding to it, so refresh-not-stack is correct by construction, no special-casing needed.

`cast_freeze` does **not** reuse `_cast_single_target_spell` from tickets 18/19 (AoE targeting and multi-target effect application are fundamentally different from single-target damage) — but it does share the new `_can_cast(world, spell)` helper (extracted from `_cast_single_target_spell`'s inline ready+Mage checks) with both Lightning and Fire, so the one truly identical piece of scaffolding across all three spells lives in exactly one place. AoE selection: find the nearest monster to territory (same helper as the other two spells) as the anchor, then freeze every monster whose tile is within `FREEZE_RADIUS` (1) on both axes of the anchor's tile — a plain 3x3 box, not a circular radius.

`save.py`'s monster dict gains `frozen_remaining` (unlike ticket 19's `burn_tick_timer`, this is the primary countdown state itself, not a sub-tick precision accumulator — dropping it would mean a frozen monster silently unfreezes on reload, a real behavior change, so it's persisted the same way spell cooldowns are).

**Post-merge update (ticket 18-21 reconciliation with `feat/combat-depth`):** `Spellbook`'s single `flash_position`/`flash_timer`/`flash_color` slot was replaced with a `flashes: list[dict]` so an AoE cast can show one flash per affected monster instead of clobbering itself down to the last one — `cast_freeze` now calls `trigger_flash` once per monster inside the 3x3 box, not once at the anchor tile.
