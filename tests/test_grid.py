from grid import Grid


def test_new_grid_claims_smaller_radius_than_it_reveals():
    grid = Grid(seed=1)
    cx, cy = grid.width // 2, grid.height // 2

    # just outside claim radius but inside reveal radius: revealed, not claimed
    from constants import START_CLAIM_RADIUS, START_REVEAL_RADIUS

    assert START_REVEAL_RADIUS > START_CLAIM_RADIUS
    frontier = grid.get(cx + START_CLAIM_RADIUS + 1, cy)
    assert frontier.revealed
    assert not frontier.claimed


def test_expand_claim_radius_defaults_to_reveal_radius_when_omitted():
    grid = Grid(seed=1)
    grid.expand(5, 5, claim_radius=2)
    assert grid.get(5, 7).claimed
    assert grid.get(5, 7).revealed


def test_expand_reveal_radius_can_exceed_claim_radius():
    grid = Grid(seed=1)
    grid.expand(5, 5, claim_radius=1, reveal_radius=3)
    assert grid.get(5, 6).claimed  # within claim radius
    assert not grid.get(5, 8).claimed  # outside claim radius
    assert grid.get(5, 8).revealed  # but within reveal radius
