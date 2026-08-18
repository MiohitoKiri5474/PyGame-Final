"""Launch-time title screen: game title text + Start button, primitive
shapes/text only (no new art assets)."""

import pygame

from constants import WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_TEXT

TITLE = "title"
PLAYING = "playing"
CONFIRM_OVERWRITE = "confirm_overwrite"

_TITLE_TEXT = "Colony Defense (WIP)"
_WARNING_TEXT = "Starting a new game will overwrite your existing save."
_BUTTON_BG = (60, 64, 80)
_BUTTON_BORDER = (140, 150, 180)
_BUTTON_WIDTH = 200
_BUTTON_HEIGHT = 56
_BUTTON_GAP = 16


def _render_button(
    surface: pygame.Surface, font: pygame.font.Font, rect: pygame.Rect, label: str
) -> None:
    pygame.draw.rect(surface, _BUTTON_BG, rect)
    pygame.draw.rect(surface, _BUTTON_BORDER, rect, 2)
    label_surface = font.render(label, True, COLOR_TEXT)
    surface.blit(label_surface, label_surface.get_rect(center=rect.center))


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

        _render_button(surface, font, self.start_rect, "Start")
        if save_exists:
            _render_button(surface, font, self.continue_rect, "Continue")


class ConfirmOverwriteDialog:
    def __init__(self) -> None:
        self.yes_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - _BUTTON_WIDTH - _BUTTON_GAP // 2,
            WINDOW_HEIGHT // 2,
            _BUTTON_WIDTH,
            _BUTTON_HEIGHT,
        )
        self.no_rect = pygame.Rect(
            WINDOW_WIDTH // 2 + _BUTTON_GAP // 2,
            WINDOW_HEIGHT // 2,
            _BUTTON_WIDTH,
            _BUTTON_HEIGHT,
        )

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        if self.yes_rect.collidepoint(pos):
            return "yes"
        if self.no_rect.collidepoint(pos):
            return "no"
        return None

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        warning_surface = font.render(_WARNING_TEXT, True, COLOR_TEXT)
        warning_rect = warning_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(warning_surface, warning_rect)

        _render_button(surface, font, self.yes_rect, "Yes, start new")
        _render_button(surface, font, self.no_rect, "No, go back")
