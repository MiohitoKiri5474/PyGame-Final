from blocking import is_wall_blocked


class _Building:
    def __init__(self, type_: str, x: int, y: int):
        self.type = type_
        self.x = x
        self.y = y


def test_true_when_wall_present_at_tile():
    assert is_wall_blocked([_Building("Wall", 3, 4)], 3, 4)


def test_false_when_no_building_at_tile():
    assert not is_wall_blocked([_Building("Wall", 3, 4)], 5, 5)


def test_false_for_non_wall_building_at_tile():
    assert not is_wall_blocked([_Building("Tower", 3, 4)], 3, 4)


def test_false_for_empty_buildings_list():
    assert not is_wall_blocked([], 0, 0)
