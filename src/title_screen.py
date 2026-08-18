"""Launch-time title screen: game title text + Start button, primitive
shapes/text only (no new art assets)."""

import pygame

from constants import WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_TEXT

TITLE = "title"
PLAYING = "playing"

_TITLE_TEXT = "Colony Defense (WIP)"
_BUTTON_BG = (60, 64, 80)
_BUTTON_BORDER = (140, 150, 180)
_BUTTON_WIDTH = 200
_BUTTON_HEIGHT = 56
_BUTTON_GAP = 16


class TitleScreen:
    def __init__(self) -> None:
        self.start_rect = pygame.Rect(
            (WINDOW_WIDTH - _BUTTON_WIDTH) // 2,
            WINDOW_HEIGHT // 2,
            _BUTTON_WIDTH,
            _BUTTON_HEIGHT,
        )
        self.continue_rect = pygame.Rect(
            self.start_rect.x,
            self.start_rect.bottom + _BUTTON_GAP,
            _BUTTON_WIDTH,
            _BUTTON_HEIGHT,
        )

    def handle_click(self, pos: tuple[int, int], save_exists: bool) -> str | None:
        if self.start_rect.collidepoint(pos):
            return "start"
        if save_exists and self.continue_rect.collidepoint(pos):
            return "continue"
        return None

    def render(self, surface: pygame.Surface, font: pygame.font.Font, save_exists: bool) -> None:
        title_surface = font.render(_TITLE_TEXT, True, COLOR_TEXT)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(title_surface, title_rect)

        self._render_button(surface, font, self.start_rect, "Start")
        if save_exists:
            self._render_button(surface, font, self.continue_rect, "Continue")

    def _render_button(
        self, surface: pygame.Surface, font: pygame.font.Font, rect: pygame.Rect, label: str
    ) -> None:
        pygame.draw.rect(surface, _BUTTON_BG, rect)
        pygame.draw.rect(surface, _BUTTON_BORDER, rect, 2)
        label_surface = font.render(label, True, COLOR_TEXT)
        surface.blit(label_surface, label_surface.get_rect(center=rect.center))
