"""All-time best score, persisted separately from save.json's checkpoint -
restart()/game-over intentionally wipe the checkpoint, but the best score
needs to survive exactly that, so it lives in its own tiny file."""

from __future__ import annotations

import json
from pathlib import Path

HIGHSCORE_PATH = Path(__file__).resolve().parent.parent / "highscore.json"


def load_best_score(path: Path = HIGHSCORE_PATH) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text())
        return int(data.get("best_score", 0))
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return 0


def save_best_score(score: int, path: Path = HIGHSCORE_PATH) -> None:
    path.write_text(json.dumps({"best_score": score}))
