"""Headless integration smoke check for game.py (the pygame-coupled seam,
not unit tested per the confirmed test seam). Runs the real init/update/
render path under a dummy SDL driver so it works on any machine with no
display, including CI.

Run: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/smoke_render.py
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

TICKS = 180


def main() -> None:
    import pygame

    from game import Game

    game = Game()
    for _ in range(TICKS):
        game.update(1 / 60)
        game.render()

    assert game.cycle.round_number >= 1
    assert len(game.npcs) > 0
    pygame.quit()
    print(f"smoke OK: {TICKS} ticks, phase={game.cycle.phase}, round={game.cycle.round_number}")


if __name__ == "__main__":
    main()
