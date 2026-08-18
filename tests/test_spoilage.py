import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from constants import (
    RAW_FOOD_SHELF_LIFE,
    PROCESSED_FOOD_SHELF_LIFE,
    HUNGER_EAT_THRESHOLD,
)
from inventory import Inventory, PerishableBatch
from npc import NPC
from spoilage import _tick_spoilage, _spoilage_hud_line
from task import update_npc_tasks
from world import World


class TestPerishablesLedger:
    def test_food_added_to_ledger_with_shelf_life(self):
        inv = Inventory()
        inv.add("crop", 5)
        inv.add("berries", 2)

        assert inv.get("crop") == 5
        assert inv.get("berries") == 2
        assert len(inv.ledger) == 2

        crop_batch = next(b for b in inv.ledger if b.resource == "crop")
        assert crop_batch.amount == 5
        assert crop_batch.expires_in == pytest.approx(RAW_FOOD_SHELF_LIFE)

        berries_batch = next(b for b in inv.ledger if b.resource == "berries")
        assert berries_batch.amount == 2
        assert berries_batch.expires_in == pytest.approx(PROCESSED_FOOD_SHELF_LIFE)

    def test_non_food_never_enters_ledger(self):
        inv = Inventory()
        inv.add("wood", 10)
        inv.add("bricks", 5)
        inv.add("marble", 3)
        inv.add("raw_stone", 8)

        assert inv.get("wood") == 10
        assert inv.get("bricks") == 5
        assert len(inv.ledger) == 0  # No non-food in perishables ledger!


class TestSpoilageDiscardAndConsistency:
    def test_spoilage_discards_expired_batches_and_keeps_count_consistent(self):
        inv = Inventory()
        inv.add("meat", 3, shelf_life=10.0)
        inv.add("crop", 2, shelf_life=50.0)

        # Advance time by 15s -> meat should spoil and be removed
        spoiled = inv.tick_spoilage(15.0)

        assert spoiled == {"meat": 3}
        assert inv.get("meat") == 0
        assert inv.get("crop") == 2
        assert len(inv.ledger) == 1
        assert inv.ledger[0].resource == "crop"

    def test_spoilage_hud_alert(self):
        world = World()
        world.inventory.add("meat", 2, shelf_life=5.0)

        _tick_spoilage(world, 10.0)
        hud_text = _spoilage_hud_line(world)

        assert "Food spoiled: 2 meat" in hud_text


class TestSoonestExpiringConsumption:
    def test_consume_soonest_food_prioritizes_earliest_expiry(self):
        inv = Inventory()
        # Meat expiring in 10s, crop expiring in 30s
        inv.add("crop", 1, shelf_life=30.0)
        inv.add("meat", 1, shelf_life=10.0)

        consumed = inv.consume_soonest_food(1)
        assert consumed == "meat"  # Meat expires first!
        assert inv.get("meat") == 0
        assert inv.get("crop") == 1

        # Next consumption takes crop
        consumed_next = inv.consume_soonest_food(1)
        assert consumed_next == "crop"
        assert inv.get("crop") == 0

    def test_hungry_npc_consumes_soonest_food_via_task_update(self):
        world = World(npc_count=1)
        npc = world.npcs[0]
        npc.hunger = HUNGER_EAT_THRESHOLD - 5  # Hungry

        world.inventory.add("crop", 1, shelf_life=100.0)
        world.inventory.add("meat", 1, shelf_life=20.0)

        update_npc_tasks(world, 0.1)

        # NPC should have eaten the meat (expires sooner)
        assert world.inventory.get("meat") == 0
        assert world.inventory.get("crop") == 1
        assert npc.hunger > HUNGER_EAT_THRESHOLD

    def test_spend_deducts_from_ledger_soonest_first(self):
        inv = Inventory()
        inv.add("meat", 2, shelf_life=10.0)
        inv.add("meat", 3, shelf_life=50.0)

        inv.spend("meat", 1)

        # Flat count is 4
        assert inv.get("meat") == 4
        # First batch had 2, now has 1
        assert inv.ledger[0].amount == 1
        assert inv.ledger[0].expires_in == pytest.approx(10.0)
