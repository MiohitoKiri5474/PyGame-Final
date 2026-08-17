from constants import WAVE_FULL_CLEAR_POINTS, WAVE_PARTIAL_CLEAR_KILLS_PER_POINT
from settlement import evaluate_wave


def test_full_clear_awards_full_clear_points():
    assert evaluate_wave(no_monsters_remain=True, killed_count=3) == WAVE_FULL_CLEAR_POINTS


def test_full_clear_with_zero_kills_awards_nothing():
    # an uneventful night (nothing spawned, nothing died) is not a free bonus
    assert evaluate_wave(no_monsters_remain=True, killed_count=0) == 0


def test_partial_clear_awards_one_point_per_n_kills():
    assert evaluate_wave(no_monsters_remain=False, killed_count=WAVE_PARTIAL_CLEAR_KILLS_PER_POINT) == 1
    assert evaluate_wave(no_monsters_remain=False, killed_count=WAVE_PARTIAL_CLEAR_KILLS_PER_POINT * 2) == 2


def test_partial_clear_floors_remainder_kills():
    assert evaluate_wave(no_monsters_remain=False, killed_count=WAVE_PARTIAL_CLEAR_KILLS_PER_POINT - 1) == 0


def test_monsters_remaining_with_zero_kills_awards_nothing():
    assert evaluate_wave(no_monsters_remain=False, killed_count=0) == 0
