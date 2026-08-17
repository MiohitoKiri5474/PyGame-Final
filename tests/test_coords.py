from coords import tile_at, tile_center


def test_tile_center_is_middle_of_tile():
    from constants import TILE_SIZE

    px, py = tile_center(2, 3)
    assert px == 2 * TILE_SIZE + TILE_SIZE / 2
    assert py == 3 * TILE_SIZE + TILE_SIZE / 2


def test_tile_at_round_trips_tile_center():
    assert tile_at(*tile_center(5, 7)) == (5, 7)


def test_tile_at_floors_to_containing_tile():
    from constants import TILE_SIZE

    gx, gy = tile_at(TILE_SIZE * 4 + 1, TILE_SIZE * 4 + TILE_SIZE - 1)
    assert (gx, gy) == (4, 4)
