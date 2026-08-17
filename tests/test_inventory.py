from inventory import Inventory


def test_new_inventory_has_zero_of_everything():
    inv = Inventory()
    assert inv.get("crop") == 0


def test_add_increases_count():
    inv = Inventory()
    inv.add("crop", 3)
    inv.add("crop", 2)
    assert inv.get("crop") == 5


def test_spend_deducts_and_returns_true_when_sufficient():
    inv = Inventory()
    inv.add("crop", 5)
    assert inv.spend("crop", 3) is True
    assert inv.get("crop") == 2


def test_spend_returns_false_and_does_not_change_balance_when_insufficient():
    inv = Inventory()
    inv.add("crop", 2)
    assert inv.spend("crop", 3) is False
    assert inv.get("crop") == 2


def test_spend_never_goes_negative_on_missing_resource():
    inv = Inventory()
    assert inv.spend("wood", 1) is False
    assert inv.get("wood") == 0


def test_spend_all_deducts_every_resource_when_all_affordable():
    inv = Inventory()
    inv.add("crop", 5)
    inv.add("wood", 3)
    assert inv.spend_all({"crop": 2, "wood": 1}) is True
    assert inv.get("crop") == 3
    assert inv.get("wood") == 2


def test_spend_all_spends_nothing_when_any_resource_is_short():
    inv = Inventory()
    inv.add("crop", 5)
    inv.add("wood", 0)  # short on wood
    assert inv.spend_all({"crop": 2, "wood": 1}) is False
    assert inv.get("crop") == 5  # untouched, not partially spent
    assert inv.get("wood") == 0
