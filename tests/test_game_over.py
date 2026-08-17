from game_over import GameOverState


def test_not_over_while_npcs_remain():
    state = GameOverState()
    assert state.check(npcs=[object()], round_number=3) is False
    assert not state.is_over


def test_triggers_once_npc_list_is_empty_and_records_round_as_score():
    state = GameOverState()
    triggered = state.check(npcs=[], round_number=5)
    assert triggered is True
    assert state.is_over
    assert state.score == 5


def test_check_is_a_noop_on_calls_after_already_triggered():
    state = GameOverState()
    state.check(npcs=[], round_number=5)
    assert state.check(npcs=[], round_number=99) is False
    assert state.score == 5  # not overwritten by the later call
