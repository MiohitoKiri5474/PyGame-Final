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
