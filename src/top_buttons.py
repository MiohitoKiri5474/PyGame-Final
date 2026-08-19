"""Top-right button column: Pause / Priority / Skill. Clickable, and each
shows its keyboard shortcut so the mouse and keyboard paths stay in sync
(both call the exact same game.py handlers). Skill lights up like an
"available" badge when there are points to spend - carries the hint the
old plain-text "Skill points: N [K]" line used to give.
"""

from __future__ import annotations

import pygame

from constants import WINDOW_WIDTH

_MARGIN = 10
_BUTTON_W = 150
_BUTTON_H = 36
_GAP = 8

_BG = (24, 26, 32)
_BORDER = (70, 74, 86)
_BORDER_ACTIVE = (255, 214, 100)
_LABEL = (225, 225, 230)
_KEY_HINT = (130, 130, 140)

_ORDER = ("pause", "priority", "skill")
_LABELS = {"pause": "Pause", "priority": "Priority", "skill": "Skill"}
_HOTKEYS = {"pause": "Space", "priority": "P", "skill": "K"}


def _rects() -> dict[str, pygame.Rect]:
    x = WINDOW_WIDTH - _MARGIN - _BUTTON_W
    rects = {}
    y = _MARGIN
    for name in _ORDER:
        rects[name] = pygame.Rect(x, y, _BUTTON_W, _BUTTON_H)
        y += _BUTTON_H + _GAP
    return rects


def handle_click(pos: tuple[int, int]) -> str | None:
    """Returns which button ("pause"/"priority"/"skill") was clicked, or
    None - caller decides what each one actually does."""
    for name, rect in _rects().items():
        if rect.collidepoint(pos):
            return name
    return None


def render(surface: pygame.Surface, font: pygame.font.Font, paused: bool, skill_points_available: int) -> int:
    """Returns the column's bottom y."""
    lit = {"pause": paused, "priority": False, "skill": skill_points_available > 0}
    bottom = _MARGIN
    for name, rect in _rects().items():
        pygame.draw.rect(surface, _BG, rect, border_radius=6)
        active = lit[name]
        pygame.draw.rect(surface, _BORDER_ACTIVE if active else _BORDER, rect, 2 if active else 1, border_radius=6)

        surface.blit(font.render(_LABELS[name], True, _LABEL), (rect.x + 10, rect.y + 8))
        hint = font.render(f"[{_HOTKEYS[name]}]", True, _KEY_HINT)
        surface.blit(hint, (rect.right - hint.get_width() - 8, rect.y + 8))
        bottom = rect.bottom
    return bottom
