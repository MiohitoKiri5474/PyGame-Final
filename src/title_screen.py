"""Launch-time title screen: game title text + Start/Continue/Settings
buttons, primitive shapes/text only (no new art assets)."""

import pygame

from constants import WINDOW_WIDTH
from ui_layout import (
    BUTTON_GAP,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
    FIRST_LEVEL_TOP,
    SECOND_LEVEL_TOP,
    hit_test,
    render_button,
    render_screen_frame,
    render_screen_title,
    stack_rect,
)

_TITLE_TEXT = "Colony Defense (WIP)"
_WARNING_TEXT = "Starting a new game will overwrite your existing save."


class TitleScreen:
    def __init__(self) -> None:
        self.start_rect = stack_rect(FIRST_LEVEL_TOP, 0)
        self.continue_rect = stack_rect(FIRST_LEVEL_TOP, 1)
        self.settings_rect = stack_rect(FIRST_LEVEL_TOP, 2)

    def handle_click(self, pos: tuple[int, int], save_exists: bool) -> str | None:
        rect_labels = [(self.start_rect, "start"), (self.settings_rect, "settings")]
        if save_exists:
            rect_labels.append((self.continue_rect, "continue"))
        return hit_test(pos, rect_labels)

    def render(self, surface: pygame.Surface, font: pygame.font.Font, save_exists: bool) -> None:
        render_screen_frame(surface)
        render_screen_title(surface, font, _TITLE_TEXT)
        render_button(surface, font, self.start_rect, "Start")
        if save_exists:
            render_button(surface, font, self.continue_rect, "Continue")
        render_button(surface, font, self.settings_rect, "Settings")


class ConfirmOverwriteDialog:
    def __init__(self) -> None:
        # SECOND_LEVEL_TOP (not FIRST_LEVEL_TOP): TitleScreen is the only
        # screen that can transition here, and TitleScreen's own rows live
        # at FIRST_LEVEL_TOP - see ui_layout.py for why these must differ.
        y = SECOND_LEVEL_TOP
        self.yes_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - BUTTON_WIDTH - BUTTON_GAP // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
        )
        self.no_rect = pygame.Rect(WINDOW_WIDTH // 2 + BUTTON_GAP // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT)

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        return hit_test(pos, [(self.yes_rect, "yes"), (self.no_rect, "no")])

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        render_screen_frame(surface)
        render_screen_title(surface, font, _WARNING_TEXT)
        render_button(surface, font, self.yes_rect, "Yes, start new")
        render_button(surface, font, self.no_rect, "No, go back")
