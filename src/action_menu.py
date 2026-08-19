"""Small popup listing task-type choices for a tile with more than one
applicable task (e.g. Hunt vs Tame on a wild animal). Most clicks resolve
to exactly one task and never touch this - see tile_actions.py.

Thin rendering/hit-test layer, not itself unit tested, matching
priority_ui.py's precedent.
"""

from __future__ import annotations

import pygame

_ROW_H = 30
_PADDING = 8
_BG = (24, 26, 32)
_BORDER = (255, 214, 100)
_ROW_HOVER = (50, 60, 80)
_TEXT = (225, 225, 230)
_TEXT_DISABLED = (110, 110, 116)


class ActionMenu:
    def __init__(self):
        self.options: list[str] = []
        self.tile: tuple[int, int] | None = None
        self.screen_pos: tuple[int, int] = (0, 0)
        self.disabled: set[str] = set()

    @property
    def visible(self) -> bool:
        return bool(self.options)

    def open(
        self,
        options: list[str],
        tile: tuple[int, int] | None,
        screen_pos: tuple[int, int],
        disabled: set[str] | None = None,
    ) -> None:
        self.options = options
        self.tile = tile
        self.screen_pos = screen_pos
        self.disabled = disabled or set()

    def close(self) -> None:
        self.options = []
        self.tile = None
        self.disabled = set()

    def _rows(self) -> list[tuple[str, pygame.Rect]]:
        x, y = self.screen_pos
        return [
            (option, pygame.Rect(x, y + i * _ROW_H, 160, _ROW_H))
            for i, option in enumerate(self.options)
        ]

    def is_hovering(self, pos: tuple[int, int]) -> bool:
        return any(rect.collidepoint(pos) for _, rect in self._rows())

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        """Returns the chosen task type and closes the menu, or closes it
        with no choice if the click missed every row (click-away-to-cancel)
        or landed on a disabled row (consumed, but inert)."""
        for option, rect in self._rows():
            if rect.collidepoint(pos):
                disabled = option in self.disabled
                self.close()
                return None if disabled else option
        self.close()
        return None

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        mouse_pos = pygame.mouse.get_pos()
        rows = self._rows()
        panel = pygame.Rect(
            self.screen_pos[0] - _PADDING,
            self.screen_pos[1] - _PADDING,
            160 + _PADDING * 2,
            len(rows) * _ROW_H + _PADDING * 2,
        )
        pygame.draw.rect(surface, _BG, panel, border_radius=6)
        pygame.draw.rect(surface, _BORDER, panel, 2, border_radius=6)

        for option, rect in rows:
            disabled = option in self.disabled
            if not disabled and rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, _ROW_HOVER, rect)
            surface.blit(font.render(option, True, _TEXT_DISABLED if disabled else _TEXT), (rect.x + 6, rect.y + 6))
