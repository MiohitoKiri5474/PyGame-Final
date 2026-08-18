"""Headless integration smoke check for game.py (the pygame-coupled seam,
not unit tested per the confirmed test seam). Runs the real init/update/
render path under a dummy SDL driver so it works on any machine with no
display, including CI.

Run: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/smoke_render.py
"""

import contextlib
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

TICKS = 180


@contextlib.contextmanager
def _preserved_save():
    """Whatever save.json is on disk (a real developer save, or none) is
    restored byte-for-byte on exit, however the wrapped code left it - the
    title-screen tests below need to freely create/delete save.json to
    exercise both branches without ever losing real save data."""
    from save import SAVE_PATH

    original_bytes = SAVE_PATH.read_bytes() if SAVE_PATH.exists() else None
    try:
        yield SAVE_PATH
    finally:
        if original_bytes is None:
            SAVE_PATH.unlink(missing_ok=True)
        else:
            SAVE_PATH.write_bytes(original_bytes)


def _click(game, pos) -> None:
    import pygame

    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    game.handle_events()


def main() -> None:
    """Ticket #38: title screen boots with no world yet, and Start (with no
    save present) builds a fresh game and enters the simulation."""
    import pygame

    from game import Game
    from title_screen import TITLE, PLAYING

    with _preserved_save() as save_path:
        save_path.unlink(missing_ok=True)  # exercise the no-save Start path deterministically

        game = Game()
        assert game.state == TITLE
        assert not game.save_exists
        game.render()  # title screen must render without a world yet

        _click(game, game.title_screen.start_rect.center)
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
    """Ticket #39: Continue is only offered when save.json exists, and
    clicking it resumes the exact checkpointed state."""
    import pygame

    from game import Game
    from save import save_checkpoint
    from title_screen import PLAYING

    with _preserved_save() as save_path:
        save_path.unlink(missing_ok=True)
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
        _click(game, game.title_screen.continue_rect.center)
        assert game.state == PLAYING
        assert game.world.npcs[0].health == 7
        pygame.quit()

    print("continue OK: save-gated Continue button resumes the exact checkpoint")


def check_overwrite_confirm() -> None:
    """Ticket #40: Start over an existing save warns before overwriting;
    declining preserves the save and returns to title, confirming proceeds
    into a genuinely fresh game."""
    import pygame

    from game import Game
    from save import save_checkpoint
    from title_screen import TITLE, PLAYING, CONFIRM_OVERWRITE

    with _preserved_save() as save_path:
        save_path.unlink(missing_ok=True)
        fixture = Game()
        fixture._start_new_game()
        fixture.world.npcs[0].health = 7  # marker: still present after decline, gone after confirm
        save_checkpoint(
            fixture.world, fixture.cycle, fixture.nest_manager, fixture.monsters,
            fixture.game_over_state, fixture.skill_points_available, fixture._monsters_killed_this_night,
        )
        saved_bytes = save_path.read_bytes()

        # Decline path: Start -> confirm -> No/Esc both return to title untouched.
        game = Game()
        assert game.save_exists
        _click(game, game.title_screen.start_rect.center)
        assert game.state == CONFIRM_OVERWRITE
        _click(game, game.confirm_dialog.no_rect.center)
        assert game.state == TITLE
        assert save_path.read_bytes() == saved_bytes

        _click(game, game.title_screen.start_rect.center)
        assert game.state == CONFIRM_OVERWRITE
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()
        assert game.state == TITLE
        assert save_path.read_bytes() == saved_bytes

        # Confirm path: Yes proceeds into a fresh game (marker gone).
        _click(game, game.title_screen.start_rect.center)
        assert game.state == CONFIRM_OVERWRITE
        _click(game, game.confirm_dialog.yes_rect.center)
        assert game.state == PLAYING
        assert game.world.npcs[0].health != 7

        # No save at all: Start goes straight to PLAYING, no dialog.
        save_path.unlink(missing_ok=True)
        game = Game()
        assert not game.save_exists
        _click(game, game.title_screen.start_rect.center)
        assert game.state == PLAYING

        pygame.quit()

    print("overwrite-confirm OK: decline preserves the save, confirm starts fresh")


if __name__ == "__main__":
    main()
    check_continue()
    check_overwrite_confirm()
