"""Settings screen, reachable from the title screen and the in-game pause
menu: Fullscreen and Mute SFX toggles. Painted backdrop
(assets/ui/other_background.png), falling back to the old primitive
shapes/text if that art isn't available. Doesn't persist across launches -
session-only, matching every other in-memory Game setting.

No Mute Music toggle yet: this branch has no background-music system to
mute (that's in a separate, unmerged PR) - add one here once it exists."""

import pygame

from constants import WINDOW_HEIGHT, WINDOW_WIDTH
from sprites import other_background_sprite
from ui_layout import (
    SECOND_LEVEL_TOP,
    hit_test,
    render_button,
    render_screen_background,
    render_screen_title,
    stack_rect,
)

_TITLE_TEXT = "Settings"


class SettingsScreen:
    def __init__(self) -> None:
        self.fullscreen_rect = stack_rect(SECOND_LEVEL_TOP, 0)
        self.mute_sfx_rect = stack_rect(SECOND_LEVEL_TOP, 1)
        self.back_rect = stack_rect(SECOND_LEVEL_TOP, 2)

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        return hit_test(
            pos,
            [
                (self.fullscreen_rect, "toggle_fullscreen"),
                (self.mute_sfx_rect, "toggle_sfx_muted"),
                (self.back_rect, "back"),
            ],
        )

    def render(
        self, surface: pygame.Surface, font: pygame.font.Font, fullscreen: bool, sfx_muted: bool
    ) -> None:
        background = other_background_sprite(WINDOW_WIDTH, WINDOW_HEIGHT)
        render_screen_background(surface, background)
        render_screen_title(surface, font, _TITLE_TEXT)
        render_button(surface, font, self.fullscreen_rect, f"Fullscreen: {'On' if fullscreen else 'Off'}")
        render_button(surface, font, self.mute_sfx_rect, f"Mute SFX: {'On' if sfx_muted else 'Off'}")
        render_button(surface, font, self.back_rect, "Back")
