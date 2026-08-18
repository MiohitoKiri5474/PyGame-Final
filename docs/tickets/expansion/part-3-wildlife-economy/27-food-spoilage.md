# 27 — Food spoilage system

**What to build:** Stored food decays over time — raw food (e.g. mushrooms, wild meat) spoils in roughly 3 game-days, cooked/processed food in roughly 5. Expired batches are automatically discarded from inventory with a HUD alert. This ticket also generalizes the currently-hardcoded `world.inventory.spend("crop", 1)` hunger-eat line in `task.py` so hungry NPCs draw from whatever food is actually in stock (soonest-to-expire first), not just crops.

**Blocked by:** 17 — Farmland building, 26 — Post-hunt food vs. taming (both needed so there's real food variety for spoilage to matter against).

**Status:** done

- [x] `Inventory` gains a parallel perishables ledger (`ledger: list[PerishableBatch]`) alongside its existing flat counts — non-food resources untouched by this ledger
- [x] Each food unit added to inventory tracks its own expiry; raw vs. processed food use named shelf-life constants (`RAW_FOOD_SHELF_LIFE`, `PROCESSED_FOOD_SHELF_LIFE`, `FOOD_SHELF_LIFE`)
- [x] Expired batches are auto-discarded via `extensions.register_tick` (`_tick_spoilage`); flat count and ledger stay consistent
- [x] A HUD line (`extensions.register_hud_line`) reports spoilage when it happens
- [x] `task.py`'s hunger-eat logic pulls from the perishables ledger (soonest-to-expire first) via `inventory.consume_soonest_food()`
- [x] `save.py` persists the full perishables ledger
- [x] Unit tests: expiry timing per food type, discard keeps flat-count/ledger consistent, hunger-eat consumes soonest-to-expire first, non-food resources never enter the ledger

**Implementation notes:**
- Updated `src/inventory.py` with `PerishableBatch`, `ledger`, `consume_soonest_food`, and `tick_spoilage`.
- Created `src/spoilage.py` with `_tick_spoilage` and `_spoilage_hud_line`.
- Updated `src/task.py` to use `inventory.consume_soonest_food()`.
- Updated `src/save.py` to serialize `inventory_ledger`.
- Comprehensive unit tests in `tests/test_spoilage.py`.

