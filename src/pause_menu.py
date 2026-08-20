"""In-game pause menu, opened with Esc while playing: Resume / Save Game /
Settings / Quit. Painted backdrop (assets/ui/other_background.png), falling
back to the old primitive shapes/text if that art isn't available."""

import pygame

from constants import WINDOW_HEIGHT, WINDOW_WIDTH
from sprites import other_background_sprite
from ui_layout import (
    FIRST_LEVEL_TOP,
    hit_test,
    render_button,
    render_screen_background,
    render_screen_title,
    stack_rect,
)

_TITLE_TEXT = "Paused"


class PauseMenu:
    def __init__(self) -> None:
        self.resume_rect = stack_rect(FIRST_LEVEL_TOP, 0)
        self.save_rect = stack_rect(FIRST_LEVEL_TOP, 1)
        self.settings_rect = stack_rect(FIRST_LEVEL_TOP, 2)
        self.quit_rect = stack_rect(FIRST_LEVEL_TOP, 3)
        self._saved_flash_until_ms = 0

    def mark_saved(self) -> None:
        self._saved_flash_until_ms = pygame.time.get_ticks() + 1500

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        return hit_test(
            pos,
            [
                (self.resume_rect, "resume"),
                (self.save_rect, "save"),
                (self.settings_rect, "settings"),
                (self.quit_rect, "quit"),
            ],
        )

    def render(
        self, surface: pygame.Surface, font: pygame.font.Font, big_font: pygame.font.Font | None = None
    ) -> None:
        background = other_background_sprite(WINDOW_WIDTH, WINDOW_HEIGHT)
        render_screen_background(surface, background)
        render_screen_title(surface, big_font or font, _TITLE_TEXT)
        render_button(surface, font, self.resume_rect, "Resume")
        save_label = "Saved!" if pygame.time.get_ticks() < self._saved_flash_until_ms else "Save Game"
        render_button(surface, font, self.save_rect, save_label)
        render_button(surface, font, self.settings_rect, "Settings")
        render_button(surface, font, self.quit_rect, "Quit")
