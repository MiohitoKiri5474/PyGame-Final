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
    from title_screen import TITLE, PLAYING

    game = Game()
    assert game.state == TITLE
    game.render()  # title screen must render without a world yet

    # Drive the real click path (not a direct state assignment) so the
    # title-screen wiring in handle_events() is actually exercised.
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=game.title_screen.start_rect.center, button=1,
    ))
    game.handle_events()
    assert game.state == PLAYING

    for _ in range(TICKS):
        game.update(1 / 60)
        game.render()

    assert game.cycle.round_number >= 1
    assert len(game.world.npcs) > 0

    # ticket 09: killing the last NPC should trigger game-over and freeze
    # the sim (round/phase/monsters/nests all stop advancing) from then on.
    game.world.npcs.clear()
    game.update(1 / 60)
    assert game.game_over_state.is_over
    assert game.game_over_state.score == game.cycle.round_number
    round_at_game_over = game.cycle.round_number
    phase_at_game_over = game.cycle.phase
    for _ in range(TICKS):
        game.update(1 / 60)
        game.render()
    assert game.cycle.round_number == round_at_game_over
    assert game.cycle.phase == phase_at_game_over

    pygame.quit()
    print(f"smoke OK: {TICKS} ticks, phase={game.cycle.phase}, round={game.cycle.round_number}")
    print(f"game-over OK: score={game.game_over_state.score}")


def check_continue() -> None:
    """Ticket #39: Continue only offered when save.json exists, and clicking
    it resumes the exact checkpointed state. Saves/restores whatever real
    save.json is on disk so running this test never loses a developer's
    actual save."""
    import pygame

    from game import Game
    from save import SAVE_PATH, save_checkpoint
    from title_screen import PLAYING

    original_bytes = SAVE_PATH.read_bytes() if SAVE_PATH.exists() else None
    try:
        SAVE_PATH.unlink(missing_ok=True)
        game = Game()
        assert not game.save_exists
        assert game.title_screen.handle_click(game.title_screen.continue_rect.center, game.save_exists) is None

        fixture = Game()
        fixture._start_new_game()
        fixture.world.npcs[0].health = 7  # distinguishing marker to verify the exact checkpoint round-trips
        save_checkpoint(
            fixture.world, fixture.cycle, fixture.nest_manager, fixture.monsters,
            fixture.game_over_state, fixture.skill_points_available, fixture._monsters_killed_this_night,
        )

        game = Game()
        assert game.save_exists
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=game.title_screen.continue_rect.center, button=1,
        ))
        game.handle_events()
        assert game.state == PLAYING
        assert game.world.npcs[0].health == 7
        pygame.quit()
    finally:
        if original_bytes is None:
            SAVE_PATH.unlink(missing_ok=True)
        else:
            SAVE_PATH.write_bytes(original_bytes)

    print("continue OK: save-gated Continue button resumes the exact checkpoint")


if __name__ == "__main__":
    main()
    check_continue()
