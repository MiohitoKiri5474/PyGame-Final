"""Top info bar: a small left box for round/phase/countdown, then a single
middle box for the collected-materials inventory. The top-right Pause/
Priority/Skill buttons, the Sanctuary box, and the left-edge magic panel
are separate modules; this one only lays out the round box and the
inventory box so each stays independently sized.

render_side_info() is a second, unrelated cluster that happens to live
here too: NPC count / remaining task count / hints, stacked in the right
column below the Sanctuary box - grouped with the round/inventory
boxes only because they share the same "framed info readout" styling
and box-layout helpers, not because they're positioned anywhere near them.

Thin rendering layer, not itself unit tested, matching priority_ui.py's
precedent.
"""

from __future__ import annotations

import math

import pygame

import text_wrap
from constants import WINDOW_WIDTH
from sprites import resource_sprite

_MARGIN = 10
_PAD = 10
LEFT_W = 170  # public: magic_panel matches its outer box to this exactly
_LEFT_MIN_H = 150  # tall enough for the left box's round/phase/ring stack
_MIDDLE_GAP = 8
_RIGHT_COL_W = 150  # matches top_buttons._BUTTON_W / SanctuaryUI's width
_MAX_HINT_ROWS = 5  # keeps the side hint box's height bounded - see render_side_info

_ROW_H = 22
_ITEM_ROW_H = 28  # inventory rows are taller: they carry an icon
_ICON = 22
_ITEM_GAP = 24  # horizontal gap between inventory items sharing a row

_BOX_BG = (24, 26, 32)
_BOX_BORDER = (70, 74, 86)
_ROUND_COLOR = (220, 220, 225)
_LABEL = (225, 225, 230)
_EMPTY_COLOR = (120, 120, 130)

# Tip box gets its own warm-yellow styling (border + tinted background) so
# it visually stands out from the plain NPC/Tasks boxes above it - it's
# meant to catch the eye, not blend in.
_HINT_BOX_BG = (48, 40, 16)
_HINT_BOX_BORDER = (255, 214, 100)
_HINT_TEXT = (255, 224, 140)

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


def left_box_bottom() -> int:
    """The round/phase/countdown box's bottom y - fixed, so magic_panel can
    anchor to it for both click hit-testing (before render() runs each
    frame) and drawing, without needing render()'s return value first."""
    return _MARGIN + _LEFT_MIN_H


def _box(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, _BOX_BG, rect, border_radius=8)
    pygame.draw.rect(surface, _BOX_BORDER, rect, 2, border_radius=8)


from render_celestial import render_celestial_dial


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
    round_number: int,
    phase_label: str,
    remaining_seconds: float,
    duration_seconds: float,
    phase_color: tuple[int, int, int],
    inventory_items: list[tuple[str, int]],
    big_font: pygame.font.Font | None = None,
    timer: float | None = None,
) -> int:
    """Draws the celestial dial and the inventory box. Returns the left box's own
    bottom y - the magic panel starts there, not at the (possibly taller)
    inventory box's bottom, since it shares the left box's x-range but not
    the middle column's."""
    left_rect = pygame.Rect(_MARGIN, _MARGIN, LEFT_W, _LEFT_MIN_H)
    if timer is None:
        timer = max(0.0, duration_seconds - remaining_seconds)
    if big_font is None:
        big_font = font
    render_celestial_dial(
        surface, left_rect, font, big_font,
        phase=phase_label, round_number=round_number,
        timer=timer, duration=duration_seconds,
    )

    middle_x = left_rect.right + _MARGIN
    middle_w = WINDOW_WIDTH - middle_x - _MARGIN - _RIGHT_COL_W - _MARGIN

    inv_rows = _layout_inventory_rows(inventory_items, font, middle_w - _PAD * 2)
    inv_h = _PAD * 2 + max(1, len(inv_rows)) * _ITEM_ROW_H
    inv_rect = pygame.Rect(middle_x, _MARGIN, middle_w, inv_h)
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

    return left_rect.bottom


def _wrapped_hint_rows(
    hint_lines: list[tuple[str, tuple[int, int, int]]], font: pygame.font.Font, max_width: int
) -> list[tuple[str, tuple[int, int, int]]]:
    rows = []
    for text, color in hint_lines:
        if not text:
            continue
        for line in text_wrap.wrap(text, font, max_width):
            rows.append((line, color))
    return rows


def render_side_info(
    surface: pygame.Surface,
    font: pygame.font.Font,
    npc_count: int,
    task_count: int,
    hint_lines: list[tuple[str, tuple[int, int, int]]],
    top_y: int,
) -> int:
    """Right column below the Sanctuary box: NPC count, remaining task
    count, then hints - narrow (matches Sanctuary's width), so hint text
    wraps rather than running off the edge."""
    x = WINDOW_WIDTH - _MARGIN - _RIGHT_COL_W
    y = top_y

    npc_rect = pygame.Rect(x, y, _RIGHT_COL_W, _PAD * 2 + _ROW_H)
    _box(surface, npc_rect)
    surface.blit(font.render(f"NPC: {npc_count}  [N]", True, _LABEL), (npc_rect.x + _PAD, npc_rect.y + _PAD))
    y = npc_rect.bottom + _MIDDLE_GAP

    task_rect = pygame.Rect(x, y, _RIGHT_COL_W, _PAD * 2 + _ROW_H)
    _box(surface, task_rect)
    surface.blit(font.render(f"Tasks: {task_count}", True, _LABEL), (task_rect.x + _PAD, task_rect.y + _PAD))
    y = task_rect.bottom + _MIDDLE_GAP

    rows = _wrapped_hint_rows(hint_lines, font, _RIGHT_COL_W - _PAD * 2)
    if len(rows) > _MAX_HINT_ROWS:
        # This narrow column wraps aggressively - two or three simultaneous
        # hud_lines (e.g. an onboarding tip plus a blocked-build warning)
        # could otherwise grow tall enough to run into the build bar below.
        # A fixed cap keeps this box's height (and therefore everything
        # below it) predictable regardless of how much text is active.
        rows = rows[: _MAX_HINT_ROWS - 1] + [("...", _EMPTY_COLOR)]
    hint_h = _PAD * 2 + max(1, len(rows)) * _ROW_H
    hint_rect = pygame.Rect(x, y, _RIGHT_COL_W, hint_h)
    pygame.draw.rect(surface, _HINT_BOX_BG, hint_rect, border_radius=8)
    pygame.draw.rect(surface, _HINT_BOX_BORDER, hint_rect, 2, border_radius=8)
    hy = hint_rect.y + _PAD
    for text, _ in (rows or [("(nothing to report)", _EMPTY_COLOR)]):
        # "..." (truncation) and the no-hint fallback stay muted; actual
        # tip text always renders in the box's own warm-yellow tone,
        # regardless of whatever color the caller happened to pass in.
        color = _EMPTY_COLOR if text in ("...", "(nothing to report)") else _HINT_TEXT
        surface.blit(font.render(text, True, color), (hint_rect.x + _PAD, hy))
        hy += _ROW_H

    return hint_rect.bottom
