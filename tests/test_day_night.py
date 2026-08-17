from day_night import DAY, NIGHT, DayNightCycle
from constants import DAY_SECONDS, NIGHT_SECONDS


def test_update_returns_false_mid_phase():
    cycle = DayNightCycle()
    assert cycle.update(1.0) is False
    assert cycle.phase == DAY


def test_update_returns_true_on_day_to_night_transition():
    cycle = DayNightCycle()
    assert cycle.update(DAY_SECONDS) is True
    assert cycle.phase == NIGHT
    assert cycle.round_number == 1


def test_update_returns_true_on_night_to_day_transition_and_bumps_round():
    cycle = DayNightCycle()
    cycle.update(DAY_SECONDS)
    assert cycle.update(NIGHT_SECONDS) is True
    assert cycle.phase == DAY
    assert cycle.round_number == 2
