"""Launch-time title screen: painted backdrop/logo/buttons (assets/ui) with
Start/Continue/Settings, falling back to the old primitive shapes/text if
that art isn't available."""

import pygame

from constants import WINDOW_HEIGHT, WINDOW_WIDTH
from sprites import other_background_sprite, title_background_sprite, title_logo_sprite
from ui_layout import (
    BUTTON_GAP_HORIZONTAL,
    BUTTON_HEIGHT,
    BUTTON_WIDTH,
    FIRST_LEVEL_TOP,
    SECOND_LEVEL_TOP,
    hit_test,
    render_button,
    render_screen_background,
    render_screen_title,
    stack_rect,
)

_TITLE_TEXT = "Colony Defense (WIP)"  # fallback heading, only shown without logo.png
_WARNING_TEXT = "Starting a new game will overwrite your existing save."
_LOGO_MAX_WIDTH = 600
_LOGO_BOTTOM_CLEARANCE = 30  # gap between the logo's bottom edge and the first button row


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
        background = title_background_sprite(WINDOW_WIDTH, WINDOW_HEIGHT)
        render_screen_background(surface, background)

        logo = title_logo_sprite(_LOGO_MAX_WIDTH)
        if logo is not None:
            logo_rect = logo.get_rect(
                centerx=WINDOW_WIDTH // 2, bottom=FIRST_LEVEL_TOP - _LOGO_BOTTOM_CLEARANCE
            )
            surface.blit(logo, logo_rect)
        else:
            render_screen_title(surface, font, _TITLE_TEXT)

        # Fixed identity->slot mapping (Start=1, Continue=2, Settings=3) so
        # each button's flourish stays the same regardless of whether
        # Continue happens to be visible this launch.
        render_button(surface, font, self.start_rect, "Start", slot=1)
        if save_exists:
            render_button(surface, font, self.continue_rect, "Continue", slot=2)
        render_button(surface, font, self.settings_rect, "Settings", slot=3)


class ConfirmOverwriteDialog:
    def __init__(self) -> None:
        # SECOND_LEVEL_TOP (not FIRST_LEVEL_TOP): TitleScreen is the only
        # screen that can transition here, and TitleScreen's own rows live
        # at FIRST_LEVEL_TOP - see ui_layout.py for why these must differ.
        y = SECOND_LEVEL_TOP
        self.yes_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - BUTTON_WIDTH - BUTTON_GAP_HORIZONTAL // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
        )
        self.no_rect = pygame.Rect(
            WINDOW_WIDTH // 2 + BUTTON_GAP_HORIZONTAL // 2, y, BUTTON_WIDTH, BUTTON_HEIGHT
        )

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        return hit_test(pos, [(self.yes_rect, "yes"), (self.no_rect, "no")])

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        background = other_background_sprite(WINDOW_WIDTH, WINDOW_HEIGHT)
        render_screen_background(surface, background)
        render_screen_title(surface, font, _WARNING_TEXT)
        render_button(surface, font, self.yes_rect, "Yes, start new")
        render_button(surface, font, self.no_rect, "No, go back")
