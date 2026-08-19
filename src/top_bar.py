"""Top info bar: a narrow left-edge column (round/phase/ring box, then
Inventory stacked below it - narrow on purpose, so it covers as little of
the map as possible) and two stacked middle boxes (NPC count, Hint) - each
framed to match the build bar's button styling. The top-right Pause/
Priority/Skill buttons and the left-edge magic panel are separate modules
(top_buttons.py, magic_panel.py); magic_panel sits below the whole left
column (round/ring box + Inventory), same x-range, via left_box_bottom().

Thin rendering layer, not itself unit tested, matching priority_ui.py's
precedent.
"""

from __future__ import annotations

import math

import pygame

from constants import WINDOW_WIDTH
from sprites import resource_sprite

_MARGIN = 10
_PAD = 10
LEFT_W = 170  # public: magic_panel matches its outer box to this exactly
_LEFT_MIN_H = 150  # tall enough for the left box's round/phase/ring stack
_MIDDLE_GAP = 8
_RIGHT_COL_W = 150  # matches top_buttons._BUTTON_W, kept clear of overlap

_ROW_H = 22
_ITEM_ROW_H = 28  # inventory rows are taller: they carry an icon
_ICON = 22

_BOX_BG = (24, 26, 32)
_BOX_BORDER = (70, 74, 86)
_ROUND_COLOR = (220, 220, 225)
_LABEL = (225, 225, 230)
_HINT_TEXT = (200, 200, 205)
_EMPTY_COLOR = (120, 120, 130)

_RING_RADIUS = 34
_RING_WIDTH = 7
_RING_BG = (55, 58, 70)


def _draw_progress_ring(
    surface: pygame.Surface, center: tuple[int, int], fraction: float, color: tuple[int, int, int]
) -> None:
    """Clockwise-depleting ring starting at 12 o'clock, `fraction` = time left / phase length."""
    rect = pygame.Rect(0, 0, _RING_RADIUS * 2, _RING_RADIUS * 2)
    rect.center = center
    pygame.draw.circle(surface, _RING_BG, center, _RING_RADIUS, _RING_WIDTH)
    if fraction > 0:
        start_angle = -math.pi / 2
        end_angle = start_angle + 2 * math.pi * min(1.0, fraction)
        pygame.draw.arc(surface, color, rect, start_angle, end_angle, _RING_WIDTH)


def _inventory_height(item_count: int) -> int:
    return _PAD * 2 + max(1, item_count) * _ITEM_ROW_H


def left_box_bottom(item_count: int) -> int:
    """The whole left column's bottom y (round/ring box + Inventory below
    it) - so magic_panel can anchor to it for both click hit-testing
    (before render() runs each frame) and drawing, without needing
    render()'s return value first. `item_count` must match what render()
    is about to be called with, same reasoning as ui_layout.py's row-
    sharing warning: two things computing the same geometry have to agree."""
    return _MARGIN + _LEFT_MIN_H + _MARGIN + _inventory_height(item_count)


def _box(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, _BOX_BG, rect, border_radius=8)
    pygame.draw.rect(surface, _BOX_BORDER, rect, 2, border_radius=8)


def render(
    surface: pygame.Surface,
    font: pygame.font.Font,
    round_number: int,
    phase_label: str,
    remaining_seconds: float,
    duration_seconds: float,
    phase_color: tuple[int, int, int],
    npc_count: int,
    inventory_items: list[tuple[str, int]],
    hint_lines: list[tuple[str, tuple[int, int, int]]],
) -> int:
    """Draws the bar. Returns the whole left column's bottom y (round/ring
    box + Inventory) - the magic panel starts there, not at the (possibly
    taller) middle/right columns' bottom, since it shares the left
    column's x-range but not theirs."""
    left_rect = pygame.Rect(_MARGIN, _MARGIN, LEFT_W, _LEFT_MIN_H)
    _box(surface, left_rect)

    round_surf = font.render(f"Round {round_number}", True, _ROUND_COLOR)
    phase_surf = font.render(phase_label, True, phase_color)
    ring_diameter = _RING_RADIUS * 2
    stack_h = round_surf.get_height() + phase_surf.get_height() + ring_diameter + 8
    y = left_rect.centery - stack_h // 2
    surface.blit(round_surf, round_surf.get_rect(centerx=left_rect.centerx, top=y))
    y += round_surf.get_height() + 2
    surface.blit(phase_surf, phase_surf.get_rect(centerx=left_rect.centerx, top=y))
    y += phase_surf.get_height() + 6

    fraction = 0.0 if duration_seconds <= 0 else max(0.0, min(1.0, remaining_seconds / duration_seconds))
    ring_center = (left_rect.centerx, y + _RING_RADIUS)
    _draw_progress_ring(surface, ring_center, fraction, phase_color)
    number_surf = font.render(f"{remaining_seconds:.0f}s", True, phase_color)
    surface.blit(number_surf, number_surf.get_rect(center=ring_center))

    # Inventory sits below the round/ring box, same narrow column - keeps
    # collected items out of the wide middle strip so they cover less of
    # the map. Icon + count only (no resource name): this column is too
    # narrow to fit "raw_stone  x12" without overflow.
    inv_h = _inventory_height(len(inventory_items))
    inv_rect = pygame.Rect(_MARGIN, left_rect.bottom + _MARGIN, LEFT_W, inv_h)
    _box(surface, inv_rect)
    iy = inv_rect.y + _PAD
    if not inventory_items:
        surface.blit(font.render("(empty)", True, _EMPTY_COLOR), (inv_rect.x + _PAD, iy))
    else:
        for resource, count in inventory_items:
            icon = resource_sprite(resource)
            if icon is not None:
                small = pygame.transform.smoothscale(icon, (_ICON, _ICON))
                surface.blit(small, (inv_rect.x + _PAD, iy))
            label_x = inv_rect.x + _PAD + _ICON + 8
            surface.blit(font.render(f"x{count}", True, _LABEL), (label_x, iy + 3))
            iy += _ITEM_ROW_H

    # Middle column: NPC (fixed), Hint (grows with active hints) - two
    # independently-sized boxes, stacked.
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

    return inv_rect.bottom
