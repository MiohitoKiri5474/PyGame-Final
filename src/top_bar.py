"""Full-width top info bar: a small left box for round/phase/countdown and
a larger right box listing everything else as a bulleted list - framed to
match the build bar's button styling, per the requester's redesign ask.

Per-NPC detail lives in npc_status_ui.py instead, opened on demand - this
bar only ever carries compact, always-relevant status.

Thin rendering layer, not itself unit tested, matching priority_ui.py's
precedent.
"""

from __future__ import annotations

import pygame

from constants import WINDOW_WIDTH

_MARGIN = 10
_PAD = 12
_LEFT_W = 170
_ROW_H = 22
_MIN_BOX_H = 112  # tall enough for the left box's round/phase/number stack
_BOX_BG = (24, 26, 32)
_BOX_BORDER = (70, 74, 86)
_ROUND_COLOR = (220, 220, 225)
_EMPTY_COLOR = (120, 120, 130)
_BULLET = "• "


def render(
    surface: pygame.Surface,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
    round_number: int,
    phase_label: str,
    remaining_seconds: float,
    phase_color: tuple[int, int, int],
    items: list[tuple[str, tuple[int, int, int]]],
) -> int:
    """Draws the bar and returns its total pixel height so callers can
    stack other content below it if they want."""
    items = [(text, color) for text, color in items if text]

    right_x = _MARGIN + _LEFT_W + _MARGIN
    right_w = WINDOW_WIDTH - right_x - _MARGIN
    box_h = max(_MIN_BOX_H, _PAD * 2 + max(1, len(items)) * _ROW_H)

    left_rect = pygame.Rect(_MARGIN, _MARGIN, _LEFT_W, box_h)
    right_rect = pygame.Rect(right_x, _MARGIN, right_w, box_h)
    for rect in (left_rect, right_rect):
        pygame.draw.rect(surface, _BOX_BG, rect, border_radius=8)
        pygame.draw.rect(surface, _BOX_BORDER, rect, 2, border_radius=8)

    # Left: round / phase / a big countdown number, vertically centered.
    round_surf = font.render(f"Round {round_number}", True, _ROUND_COLOR)
    phase_surf = font.render(phase_label, True, phase_color)
    number_surf = big_font.render(f"{remaining_seconds:.0f}s", True, phase_color)
    stack_h = round_surf.get_height() + phase_surf.get_height() + number_surf.get_height() + 8
    y = left_rect.centery - stack_h // 2
    surface.blit(round_surf, round_surf.get_rect(centerx=left_rect.centerx, top=y))
    y += round_surf.get_height() + 2
    surface.blit(phase_surf, phase_surf.get_rect(centerx=left_rect.centerx, top=y))
    y += phase_surf.get_height() + 6
    surface.blit(number_surf, number_surf.get_rect(centerx=left_rect.centerx, top=y))

    # Right: one bullet per line.
    y = right_rect.top + _PAD
    rows = items or [("(nothing to report)", _EMPTY_COLOR)]
    for text, color in rows:
        surf = font.render(f"{_BULLET}{text}", True, color)
        surface.blit(surf, (right_rect.left + _PAD, y))
        y += _ROW_H

    return left_rect.bottom + _MARGIN
