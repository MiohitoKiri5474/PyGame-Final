"""Top info bar: a small left box for round/phase/countdown, then three
stacked middle boxes (NPC count, Inventory, Hint) - each framed to match
the build bar's button styling. The top-right Pause/Priority/Skill buttons
and the left-edge magic panel are separate modules (top_buttons.py,
magic_panel.py); this one only lays out the round box and the three
middle boxes so each stays independently sized.

Thin rendering layer, not itself unit tested, matching priority_ui.py's
precedent.
"""

from __future__ import annotations

import pygame

from constants import WINDOW_WIDTH
from sprites import resource_sprite

_MARGIN = 10
_PAD = 10
LEFT_W = 170  # public: magic_panel matches its outer box to this exactly
_LEFT_MIN_H = 112  # tall enough for the left box's round/phase/number stack
_MIDDLE_GAP = 8
_RIGHT_COL_W = 150  # matches top_buttons._BUTTON_W, kept clear of overlap

_ROW_H = 22
_ITEM_ROW_H = 28  # inventory rows are taller: they carry an icon
_ICON = 22
_ITEM_GAP = 24  # horizontal gap between inventory items sharing a row

_BOX_BG = (24, 26, 32)
_BOX_BORDER = (70, 74, 86)
_ROUND_COLOR = (220, 220, 225)
_LABEL = (225, 225, 230)
_HINT_TEXT = (200, 200, 205)
_EMPTY_COLOR = (120, 120, 130)


def left_box_bottom() -> int:
    """The round/phase/countdown box's bottom y - fixed, so magic_panel can
    anchor to it for both click hit-testing (before render() runs each
    frame) and drawing, without needing render()'s return value first."""
    return _MARGIN + _LEFT_MIN_H


def _box(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, _BOX_BG, rect, border_radius=8)
    pygame.draw.rect(surface, _BOX_BORDER, rect, 2, border_radius=8)


def _layout_inventory_rows(
    items: list[tuple[str, int]], font: pygame.font.Font, max_width: int
) -> list[list[tuple[str, str, int]]]:
    """Packs items left-to-right - several per row, e.g. 5 side by side -
    and only starts a new row once the current one actually runs out of
    width, rather than always dropping to one item per line."""
    rows: list[list[tuple[str, str, int]]] = [[]]
    x = 0
    for resource, count in items:
        label = f"{resource}  x{count}"
        w = _ICON + 8 + font.size(label)[0]
        if x > 0 and x + w > max_width:
            rows.append([])
            x = 0
        rows[-1].append((resource, label, w))
        x += w + _ITEM_GAP
    return rows


def render(
    surface: pygame.Surface,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
    round_number: int,
    phase_label: str,
    remaining_seconds: float,
    phase_color: tuple[int, int, int],
    npc_count: int,
    inventory_items: list[tuple[str, int]],
    hint_lines: list[tuple[str, tuple[int, int, int]]],
) -> int:
    """Draws the bar. Returns the left box's own bottom y - the magic panel
    starts there, not at the (possibly taller) middle/right columns'
    bottom, since it shares the left box's x-range but not theirs."""
    left_rect = pygame.Rect(_MARGIN, _MARGIN, LEFT_W, _LEFT_MIN_H)
    _box(surface, left_rect)

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

    # Middle column: NPC (fixed), Inventory (grows with item count), Hint
    # (grows with active hints) - three independently-sized boxes, stacked.
    middle_x = left_rect.right + _MARGIN
    middle_w = WINDOW_WIDTH - middle_x - _MARGIN - _RIGHT_COL_W - _MARGIN
    my = _MARGIN

    npc_h = _PAD * 2 + _ROW_H
    npc_rect = pygame.Rect(middle_x, my, middle_w, npc_h)
    _box(surface, npc_rect)
    surface.blit(
        font.render(f"NPC: {npc_count}  [N] to see detail", True, _LABEL),
        (npc_rect.x + _PAD, npc_rect.y + _PAD),
    )
    my = npc_rect.bottom + _MIDDLE_GAP

    inv_rows = _layout_inventory_rows(inventory_items, font, middle_w - _PAD * 2)
    inv_h = _PAD * 2 + max(1, len(inv_rows)) * _ITEM_ROW_H
    inv_rect = pygame.Rect(middle_x, my, middle_w, inv_h)
    _box(surface, inv_rect)
    iy = inv_rect.y + _PAD
    if not inventory_items:
        surface.blit(font.render("Inventory: (empty)", True, _EMPTY_COLOR), (inv_rect.x + _PAD, iy))
    else:
        for row in inv_rows:
            ix = inv_rect.x + _PAD
            for resource, label, w in row:
                icon = resource_sprite(resource)
                if icon is not None:
                    small = pygame.transform.smoothscale(icon, (_ICON, _ICON))
                    surface.blit(small, (ix, iy))
                surface.blit(font.render(label, True, _LABEL), (ix + _ICON + 8, iy + 3))
                ix += w + _ITEM_GAP
            iy += _ITEM_ROW_H
    my = inv_rect.bottom + _MIDDLE_GAP

    # Hint box absorbs whatever's left: no fixed height, it just grows with
    # however many hint lines are active this frame.
    hint_lines = [(text, color) for text, color in hint_lines if text]
    hint_h = _PAD * 2 + max(1, len(hint_lines)) * _ROW_H
    hint_rect = pygame.Rect(middle_x, my, middle_w, hint_h)
    _box(surface, hint_rect)
    hy = hint_rect.y + _PAD
    rows = hint_lines or [("(nothing to report)", _EMPTY_COLOR)]
    for text, color in rows:
        surface.blit(font.render(text, True, color), (hint_rect.x + _PAD, hy))
        hy += _ROW_H

    return left_rect.bottom
