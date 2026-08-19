"""Settings screen, reachable from the title screen and the in-game pause
menu: currently just the Fullscreen toggle. Primitive shapes/text only (no
new art assets). Doesn't persist across launches - session-only, matching
every other in-memory Game setting."""

import pygame

from ui_layout import (
    SECOND_LEVEL_TOP,
    hit_test,
    render_button,
    render_screen_frame,
    render_screen_title,
    stack_rect,
)

_TITLE_TEXT = "Settings"


class SettingsScreen:
    def __init__(self) -> None:
        self.fullscreen_rect = stack_rect(SECOND_LEVEL_TOP, 0)
        self.back_rect = stack_rect(SECOND_LEVEL_TOP, 1)

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        return hit_test(pos, [(self.fullscreen_rect, "toggle_fullscreen"), (self.back_rect, "back")])

    def render(self, surface: pygame.Surface, font: pygame.font.Font, fullscreen: bool) -> None:
        render_screen_frame(surface)
        render_screen_title(surface, font, _TITLE_TEXT)
        render_button(surface, font, self.fullscreen_rect, f"Fullscreen: {'On' if fullscreen else 'Off'}")
        render_button(surface, font, self.back_rect, "Back")
