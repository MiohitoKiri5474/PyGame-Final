"""Launch-time title screen: game title text + Start button, primitive
shapes/text only (no new art assets)."""

import pygame

from constants import WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_TEXT

_TITLE_TEXT = "Colony Defense (WIP)"
_WARNING_TEXT = "Starting a new game will overwrite your existing save."
_BUTTON_BG = (60, 64, 80)
_BUTTON_BORDER = (140, 150, 180)
_BUTTON_WIDTH = 200
_BUTTON_HEIGHT = 56
_BUTTON_GAP = 16


def _button_rect(x: int, y: int) -> pygame.Rect:
    return pygame.Rect(x, y, _BUTTON_WIDTH, _BUTTON_HEIGHT)


def _render_button(
    surface: pygame.Surface, font: pygame.font.Font, rect: pygame.Rect, label: str
) -> None:
    pygame.draw.rect(surface, _BUTTON_BG, rect)
    pygame.draw.rect(surface, _BUTTON_BORDER, rect, 2)
    label_surface = font.render(label, True, COLOR_TEXT)
    surface.blit(label_surface, label_surface.get_rect(center=rect.center))


def _hit_test(pos: tuple[int, int], rect_labels: list[tuple[pygame.Rect, str]]) -> str | None:
    for rect, label in rect_labels:
        if rect.collidepoint(pos):
            return label
    return None


class TitleScreen:
    def __init__(self) -> None:
        self.start_rect = _button_rect((WINDOW_WIDTH - _BUTTON_WIDTH) // 2, WINDOW_HEIGHT // 2)
        self.continue_rect = _button_rect(self.start_rect.x, self.start_rect.bottom + _BUTTON_GAP)

    def handle_click(self, pos: tuple[int, int], save_exists: bool) -> str | None:
        rect_labels = [(self.start_rect, "start")]
        if save_exists:
            rect_labels.append((self.continue_rect, "continue"))
        return _hit_test(pos, rect_labels)

    def render(self, surface: pygame.Surface, font: pygame.font.Font, save_exists: bool) -> None:
        title_surface = font.render(_TITLE_TEXT, True, COLOR_TEXT)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(title_surface, title_rect)

        _render_button(surface, font, self.start_rect, "Start")
        if save_exists:
            _render_button(surface, font, self.continue_rect, "Continue")


class ConfirmOverwriteDialog:
    def __init__(self) -> None:
        # Deliberately placed on a different y-band than TitleScreen's
        # start_rect (y: WINDOW_HEIGHT//2 to +56) and continue_rect (below
        # that): the two screens are never shown at once, but a plain
        # double-click at the same screen position must not land on Start
        # in one state and Yes/No in the other by coordinate coincidence.
        dialog_y = WINDOW_HEIGHT // 2 + 160
        self.yes_rect = _button_rect(WINDOW_WIDTH // 2 - _BUTTON_WIDTH - _BUTTON_GAP // 2, dialog_y)
        self.no_rect = _button_rect(WINDOW_WIDTH // 2 + _BUTTON_GAP // 2, dialog_y)

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        return _hit_test(pos, [(self.yes_rect, "yes"), (self.no_rect, "no")])

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        warning_surface = font.render(_WARNING_TEXT, True, COLOR_TEXT)
        warning_rect = warning_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        surface.blit(warning_surface, warning_rect)

        _render_button(surface, font, self.yes_rect, "Yes, start new")
        _render_button(surface, font, self.no_rect, "No, go back")
