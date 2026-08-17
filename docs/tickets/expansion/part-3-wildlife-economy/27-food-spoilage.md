# 27 — Food spoilage system

**What to build:** Stored food decays over time — raw food (e.g. mushrooms, wild meat) spoils in roughly 3 game-days, cooked/processed food in roughly 5. Expired batches are automatically discarded from inventory with a HUD alert. This ticket also generalizes the currently-hardcoded `world.inventory.spend("crop", 1)` hunger-eat line in `task.py` so hungry NPCs draw from whatever food is actually in stock (soonest-to-expire first), not just crops.

**Blocked by:** 17 — Farmland building, 26 — Post-hunt food vs. taming (both needed so there's real food variety for spoilage to matter against).

**Status:** ready-for-agent

- [ ] `Inventory` gains a parallel perishables ledger (e.g. `list[(resource, expires_at, amount)]`) alongside its existing flat counts — non-food resources (Wood, Marble, Bricks, Berries, Raw Stone, buildings) are untouched by this ledger entirely
- [ ] Each food unit added to inventory tracks its own expiry; raw vs. processed food use different named shelf-life constants
- [ ] Expired batches are auto-discarded via `extensions.register_tick`; the flat count and the ledger stay consistent with each other after a discard
- [ ] A HUD line (`extensions.register_hud_line`) reports spoilage the tick it happens
- [ ] `task.py`'s hunger-eat logic pulls from the perishables ledger (soonest-to-expire first) instead of the hardcoded `"crop"` string
- [ ] `save.py` persists the full ledger
- [ ] Unit tests: expiry timing per food type, discard keeps flat-count/ledger consistent, hunger-eat consumes soonest-to-expire first, non-food resources never enter the ledger
