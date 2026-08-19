"""In-game pause menu, opened with Esc while playing: Resume / Save Game /
Settings / Quit. Primitive shapes/text only (no new art assets)."""

import pygame

from ui_layout import (
    FIRST_LEVEL_TOP,
    hit_test,
    render_button,
    render_screen_frame,
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

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        render_screen_frame(surface)
        render_screen_title(surface, font, _TITLE_TEXT)
        render_button(surface, font, self.resume_rect, "Resume")
        save_label = "Saved!" if pygame.time.get_ticks() < self._saved_flash_until_ms else "Save Game"
        render_button(surface, font, self.save_rect, save_label)
        render_button(surface, font, self.settings_rect, "Settings")
        render_button(surface, font, self.quit_rect, "Quit")
