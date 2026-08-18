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


class TitleScreen:
    def __init__(self) -> None:
        self.start_rect = pygame.Rect(
            (WINDOW_WIDTH - _BUTTON_WIDTH) // 2,
            WINDOW_HEIGHT // 2,
            _BUTTON_WIDTH,
            _BUTTON_HEIGHT,
        )

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        if self.start_rect.collidepoint(pos):
            return "start"
        return None

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        title_surface = font.render(_TITLE_TEXT, True, COLOR_TEXT)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(title_surface, title_rect)

        pygame.draw.rect(surface, _BUTTON_BG, self.start_rect)
        pygame.draw.rect(surface, _BUTTON_BORDER, self.start_rect, 2)
        start_label = font.render("Start", True, COLOR_TEXT)
        surface.blit(start_label, start_label.get_rect(center=self.start_rect.center))
