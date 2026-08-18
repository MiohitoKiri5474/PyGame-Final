"""Full-width top info bar, replacing the old top-left stacked-line HUD.

Lays out short status segments left-to-right, wrapping to a new row when a
segment would overflow the window width, so the corner doesn't grow an
unbounded vertical list as more systems register hud_lines(). Per-NPC detail
lives in npc_status_ui.py instead, opened on demand - this bar only ever
carries compact, always-relevant status.

Thin rendering layer, not itself unit tested, matching priority_ui.py's
precedent.
"""

from __future__ import annotations

import pygame

from constants import WINDOW_WIDTH

_BG = (10, 11, 16, 215)
_PAD_X = 10
_PAD_Y = 6
_GAP_X = 22
_ROW_H = 22


def render(surface: pygame.Surface, font: pygame.font.Font, segments: list[tuple[str, tuple[int, int, int]]]) -> int:
    """Draws the bar and returns its pixel height (0 if there was nothing
    to show), so callers can stack other content below it if they want."""
    segments = [(text, color) for text, color in segments if text]
    if not segments:
        return 0

    rows: list[list[tuple[tuple[int, int, int], pygame.Surface]]] = [[]]
    x = _PAD_X
    for text, color in segments:
        rendered = font.render(text, True, color)
        if x + rendered.get_width() > WINDOW_WIDTH - _PAD_X and rows[-1]:
            rows.append([])
            x = _PAD_X
        rows[-1].append((color, rendered))
        x += rendered.get_width() + _GAP_X

    bar_h = _PAD_Y * 2 + _ROW_H * len(rows)
    overlay = pygame.Surface((WINDOW_WIDTH, bar_h), pygame.SRCALPHA)
    overlay.fill(_BG)
    surface.blit(overlay, (0, 0))

    y = _PAD_Y
    for row in rows:
        x = _PAD_X
        for color, rendered in row:
            surface.blit(rendered, (x, y))
            x += rendered.get_width() + _GAP_X
        y += _ROW_H

    return bar_h
