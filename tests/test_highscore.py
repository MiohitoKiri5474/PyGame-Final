from highscore import load_best_score, save_best_score


def test_load_returns_zero_when_file_missing(tmp_path):
    path = tmp_path / "highscore.json"
    assert load_best_score(path) == 0


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "highscore.json"
    save_best_score(7, path)
    assert load_best_score(path) == 7


def test_load_returns_zero_on_corrupt_file(tmp_path):
    path = tmp_path / "highscore.json"
    path.write_text("not json")
    assert load_best_score(path) == 0
