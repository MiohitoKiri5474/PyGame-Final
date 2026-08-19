"""Headless integration smoke check for game.py (the pygame-coupled seam,
not unit tested per the confirmed test seam). Runs the real init/update/
render path under a dummy SDL driver so it works on any machine with no
display, including CI.

Run: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/smoke_render.py
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path
from typing import Iterator

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

TICKS = 180
FIXTURE_MARKER_HEALTH = 7  # distinguishing value to verify a checkpoint round-trips exactly


@contextlib.contextmanager
def _preserved_save() -> Iterator[Path]:
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


def _click(game: "Game", pos: tuple[int, int]) -> None:
    import pygame

    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    game.handle_events()


def _make_checkpointed_fixture() -> None:
    """Builds a fresh game, marks npcs[0].health with FIXTURE_MARKER_HEALTH,
    and checkpoints it to save.json - the shared setup for both the Continue
    and overwrite-confirm checks below."""
    from game import Game
    from save import save_checkpoint

    fixture = Game()
    fixture._start_new_game()
    fixture.world.npcs[0].health = FIXTURE_MARKER_HEALTH
    save_checkpoint(
        fixture.world, fixture.cycle, fixture.nest_manager, fixture.monsters,
        fixture.game_over_state, fixture.skill_points_available, fixture._monsters_killed_this_night,
    )


def main() -> None:
    """Ticket #38: title screen boots with no world yet, and Start (with no
    save present) builds a fresh game and enters the simulation."""
    import pygame

    from game import Game, TITLE, PLAYING

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

    from game import Game, PLAYING

    with _preserved_save() as save_path:
        save_path.unlink(missing_ok=True)
        game = Game()
        assert not game.save_exists
        assert game.title_screen.handle_click(game.title_screen.continue_rect.center, game.save_exists) is None
        pygame.quit()

        _make_checkpointed_fixture()
        pygame.quit()

        game = Game()
        assert game.save_exists
        _click(game, game.title_screen.continue_rect.center)
        assert game.state == PLAYING
        assert game.world.npcs[0].health == FIXTURE_MARKER_HEALTH
        pygame.quit()

    print("continue OK: save-gated Continue button resumes the exact checkpoint")


def check_overwrite_confirm() -> None:
    """Ticket #40: Start over an existing save warns before overwriting;
    declining preserves the save and returns to title, confirming proceeds
    into a genuinely fresh game."""
    import pygame

    from game import Game, TITLE, PLAYING, CONFIRM_OVERWRITE

    with _preserved_save() as save_path:
        save_path.unlink(missing_ok=True)
        _make_checkpointed_fixture()
        pygame.quit()
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

        # A double-click on the same screen position must not smuggle Start's
        # click into the confirm dialog's Yes/No rects (regression check for
        # the rect-overlap bug: Start and Yes/No now live on different y-bands).
        assert game.title_screen.start_rect.colliderect(game.confirm_dialog.yes_rect) is False
        assert game.title_screen.start_rect.colliderect(game.confirm_dialog.no_rect) is False
        assert game.title_screen.continue_rect.colliderect(game.confirm_dialog.yes_rect) is False
        assert game.title_screen.continue_rect.colliderect(game.confirm_dialog.no_rect) is False

        # Confirm path: Yes proceeds into a fresh game (marker gone).
        _click(game, game.title_screen.start_rect.center)
        assert game.state == CONFIRM_OVERWRITE
        _click(game, game.confirm_dialog.yes_rect.center)
        assert game.state == PLAYING
        assert game.world.npcs[0].health != FIXTURE_MARKER_HEALTH
        pygame.quit()

        # No save at all: Start goes straight to PLAYING, no dialog.
        save_path.unlink(missing_ok=True)
        game = Game()
        assert not game.save_exists
        _click(game, game.title_screen.start_rect.center)
        assert game.state == PLAYING
        pygame.quit()

    print("overwrite-confirm OK: decline preserves the save, confirm starts fresh, buttons never overlap")


def check_continue_corrupt_save() -> None:
    """Ticket #39 hardening: a corrupt (unreadable) save.json must not leave
    Continue permanently visible-but-broken - clicking it should clear
    save_exists so the dead button disappears instead of no-op'ing forever."""
    import pygame

    from game import Game, TITLE

    with _preserved_save() as save_path:
        save_path.write_text("not valid json")
        game = Game()
        assert game.save_exists
        _click(game, game.title_screen.continue_rect.center)
        assert game.state == TITLE
        assert not game.save_exists
        pygame.quit()

    print("continue-corrupt OK: a broken save clears save_exists instead of a dead Continue button")


def check_no_adjacent_screen_overlaps() -> None:
    """Regression guard, generalized past the one incident: no two screens
    that can transition into each other with a single click may share
    screen coordinates (see ui_layout.py's module docstring) - checked
    exhaustively for every state-adjacent pair, not just the pair that
    actually shipped a bug once."""
    import pygame

    from game import Game

    with _preserved_save() as save_path:
        save_path.unlink(missing_ok=True)
        game = Game()

        title = game.title_screen
        confirm = game.confirm_dialog
        pause = game.pause_menu
        settings = game.settings_screen

        # TITLE <-> CONFIRM_OVERWRITE (Start can lead there when a save exists)
        for title_rect in (title.start_rect, title.continue_rect, title.settings_rect):
            for confirm_rect in (confirm.yes_rect, confirm.no_rect):
                assert not title_rect.colliderect(confirm_rect)

        # TITLE <-> SETTINGS (the Settings button leads there)
        for title_rect in (title.start_rect, title.continue_rect, title.settings_rect):
            for settings_rect in (settings.fullscreen_rect, settings.back_rect):
                assert not title_rect.colliderect(settings_rect)

        # PAUSE_MENU <-> SETTINGS (the Settings button leads there)
        for pause_rect in (pause.resume_rect, pause.settings_rect, pause.quit_rect):
            for settings_rect in (settings.fullscreen_rect, settings.back_rect):
                assert not pause_rect.colliderect(settings_rect)

        pygame.quit()

    print("no-overlap OK: every state-adjacent screen pair has disjoint button rects")


def check_pause_menu_and_settings() -> None:
    """New feature: Esc during PLAYING opens a pause menu (Resume/Settings/
    Quit) instead of quitting instantly; Settings (reachable from both the
    title screen and the pause menu) holds a session-only Fullscreen toggle
    and returns to whichever screen opened it."""
    import pygame

    from game import Game, TITLE, PLAYING, PAUSE_MENU, SETTINGS

    with _preserved_save() as save_path:
        save_path.unlink(missing_ok=True)

        # Settings from the title screen returns to the title screen.
        game = Game()
        assert not game.fullscreen
        _click(game, game.title_screen.settings_rect.center)
        assert game.state == SETTINGS
        _click(game, game.settings_screen.fullscreen_rect.center)
        assert game.fullscreen
        _click(game, game.settings_screen.fullscreen_rect.center)
        assert not game.fullscreen  # toggles back off, and set_mode doesn't crash either direction
        _click(game, game.settings_screen.back_rect.center)
        assert game.state == TITLE
        pygame.quit()

        # Esc also closes Settings, same as Back.
        game = Game()
        _click(game, game.title_screen.settings_rect.center)
        assert game.state == SETTINGS
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()
        assert game.state == TITLE
        pygame.quit()

        # Esc during PLAYING opens the pause menu instead of quitting.
        game = Game()
        _click(game, game.title_screen.start_rect.center)
        assert game.state == PLAYING
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()
        assert game.state == PAUSE_MENU
        assert game.running  # unchanged: opening the menu must not quit the app

        # Simulation is fully frozen while the pause menu is open.
        round_before = game.cycle.round_number
        for _ in range(TICKS):
            game.update(1 / 60)
            game.render()
        assert game.cycle.round_number == round_before

        # Resume returns to PLAYING and the sim ticks again.
        _click(game, game.pause_menu.resume_rect.center)
        assert game.state == PLAYING
        game.update(1 / 60)
        game.render()

        # Esc from the pause menu also resumes, same as clicking Resume.
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()
        assert game.state == PAUSE_MENU
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()
        assert game.state == PLAYING

        # Settings reached from the pause menu returns to the pause menu, not the title screen.
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()
        assert game.state == PAUSE_MENU
        _click(game, game.pause_menu.settings_rect.center)
        assert game.state == SETTINGS
        _click(game, game.settings_screen.back_rect.center)
        assert game.state == PAUSE_MENU

        # Quit from the pause menu stops the app, same as the old direct-Esc-quit did.
        _click(game, game.pause_menu.quit_rect.center)
        assert not game.running
        pygame.quit()

    print("pause-menu/settings OK: Esc opens a real menu, Settings round-trips fullscreen and returns correctly")


if __name__ == "__main__":
    main()
    check_continue()
    check_overwrite_confirm()
    check_continue_corrupt_save()
    check_no_adjacent_screen_overlaps()
    check_pause_menu_and_settings()
