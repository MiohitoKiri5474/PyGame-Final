"""Shared hover-tooltip box - single-line description that pops up next to
whatever's under the cursor. Used by magic_panel.py and build_bar.py so a
hovered button's description renders identically in both."""

from __future__ import annotations

import pygame

_BG = (18, 20, 26)
_BORDER = (90, 94, 106)
_TEXT = (220, 220, 225)
_PAD = 8


def render(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    anchor_rect: pygame.Rect,
    placement: str = "right",
) -> None:
    """Draws a tooltip box next to anchor_rect. "right" (default) - for a
    vertical stack of buttons - sits beside it, flipping to the left if it
    would run off the screen's right edge. "above" - for a horizontal row,
    where "right" would just cover the next button over - sits above it
    instead, centered."""
    text_surf = font.render(text, True, _TEXT)
    box_w = text_surf.get_width() + _PAD * 2
    box_h = text_surf.get_height() + _PAD * 2

    if placement == "above":
        x = anchor_rect.centerx - box_w // 2
        x = max(0, min(x, surface.get_width() - box_w))
        y = anchor_rect.top - box_h - 6
    else:
        x = anchor_rect.right + 8
        if x + box_w > surface.get_width():
            x = anchor_rect.left - box_w - 8
        y = anchor_rect.top

    box = pygame.Rect(x, y, box_w, box_h)
    pygame.draw.rect(surface, _BG, box, border_radius=6)
    pygame.draw.rect(surface, _BORDER, box, 1, border_radius=6)
    surface.blit(text_surf, (box.x + _PAD, box.y + _PAD))
