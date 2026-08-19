"""Left-side magic spell panel: Fire / Lightning / Freeze, clickable and
hotkey-labeled (F1/F2/F3 stay working too - both paths call the exact same
game.py cast functions). Each button fills from empty (just cast) to full
(ready) as its cooldown counts down, like a measuring cup - a plain bottom-
up rect wipe rather than a radial, cheapest to draw and reads fine at this
size.

Sits directly below the top bar's round/phase/countdown box - `y` is that
box's own bottom (top_bar.render()'s return value), not the whole bar's,
since the middle/right columns can end up taller without pushing this
panel down (different x-range, no overlap either way). The outer box's
width matches top_bar.LEFT_W exactly, so it lines up with that box above
it and never encroaches on the middle column beside it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import top_bar
import ui_tooltip
from constants import FIRE_COOLDOWN, FREEZE_COOLDOWN, LIGHTNING_COOLDOWN

if TYPE_CHECKING:
    from world import World

_MARGIN = 10
_BUTTON_H = 56
_GAP = 8

_OUTER_PAD = 10
_HEADER_H = 22
_DESC_LINE_H = 16
_WIDTH = top_bar.LEFT_W - _OUTER_PAD * 2  # button content width, box matches top_bar's left box exactly

_BG = (24, 26, 32)
_OUTER_BG = (18, 20, 26)
_OUTER_BORDER = (60, 64, 76)
_BORDER = (70, 74, 86)
_LABEL = (225, 225, 230)
_KEY_HINT = (130, 130, 140)
_HEADER_COLOR = (255, 214, 100)
_DESC_COLOR = (150, 150, 158)

_HEADER_TEXT = "Magic"
_DESC_TEXT = "Auto-targets the nearest monster - click or press the hotkey to cast"

_ORDER = ("Fire", "Lightning", "Freeze")
_HOTKEYS = {"Fire": "F1", "Lightning": "F2", "Freeze": "F3"}
_DESCRIPTIONS = {
    "Fire": "Direct hit plus burn damage over time",
    "Lightning": "One high-damage direct strike",
    "Freeze": "Stops every monster in a small area from moving - no damage",
}
# Darker/more saturated than the spell's flash color elsewhere (COLOR_FIRE_
# FLASH etc.) on purpose - a pale fill would wash out the white label text
# once the gauge is full.
_COLORS = {"Fire": (195, 90, 30), "Lightning": (195, 165, 40), "Freeze": (55, 135, 185)}
_MAX_COOLDOWN = {"Fire": FIRE_COOLDOWN, "Lightning": LIGHTNING_COOLDOWN, "Freeze": FREEZE_COOLDOWN}


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Greedy word-wrap: packs words onto a line until the next one would
    overflow max_width, then starts a new line."""
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _desc_lines(font: pygame.font.Font) -> list[str]:
    return _wrap_text(_DESC_TEXT, font, _WIDTH)


def _outer_rect(y: int, font: pygame.font.Font) -> pygame.Rect:
    desc_h = len(_desc_lines(font)) * _DESC_LINE_H
    height = _OUTER_PAD * 2 + _HEADER_H + desc_h + len(_ORDER) * _BUTTON_H + (len(_ORDER) - 1) * _GAP
    return pygame.Rect(_MARGIN, y + _MARGIN, top_bar.LEFT_W, height)


def _rects(y: int, font: pygame.font.Font) -> dict[str, pygame.Rect]:
    outer = _outer_rect(y, font)
    desc_h = len(_desc_lines(font)) * _DESC_LINE_H
    rects = {}
    top = outer.y + _OUTER_PAD + _HEADER_H + desc_h
    for spell in _ORDER:
        rects[spell] = pygame.Rect(outer.x + _OUTER_PAD, top, _WIDTH, _BUTTON_H)
        top += _BUTTON_H + _GAP
    return rects


def is_hovering(pos: tuple[int, int], y: int, font: pygame.font.Font) -> bool:
    return any(rect.collidepoint(pos) for rect in _rects(y, font).values())


def handle_click(pos: tuple[int, int], y: int, font: pygame.font.Font) -> str | None:
    """Returns the spell name clicked, or None - caller checks readiness
    and casts (same as pressing its hotkey)."""
    for spell, rect in _rects(y, font).items():
        if rect.collidepoint(pos):
            return spell
    return None


def render(surface: pygame.Surface, font: pygame.font.Font, world: "World", y: int) -> int:
    """Returns the panel's bottom y."""
    outer = _outer_rect(y, font)
    pygame.draw.rect(surface, _OUTER_BG, outer, border_radius=8)
    pygame.draw.rect(surface, _OUTER_BORDER, outer, 2, border_radius=8)

    font.set_bold(True)
    header_surf = font.render(_HEADER_TEXT, True, _HEADER_COLOR)
    font.set_bold(False)
    surface.blit(header_surf, (outer.x + _OUTER_PAD, outer.y + _OUTER_PAD - 2))

    dy = outer.y + _OUTER_PAD + _HEADER_H - 4
    for line in _desc_lines(font):
        surface.blit(font.render(line, True, _DESC_COLOR), (outer.x + _OUTER_PAD, dy))
        dy += _DESC_LINE_H

    mouse_pos = pygame.mouse.get_pos()
    hovered_rect = None
    hovered_spell = None
    for spell, rect in _rects(y, font).items():
        pygame.draw.rect(surface, _BG, rect, border_radius=6)

        remaining = world.spellbook.remaining(spell)
        ready_ratio = 1.0 - min(1.0, remaining / _MAX_COOLDOWN[spell])
        # Fill rises bottom-up in the spell's own color as cooldown drains -
        # button reads mostly-dark right after casting, mostly-bright again
        # by the time it's ready, like a measuring cup filling up.
        if ready_ratio > 0:
            fill_h = int(rect.height * ready_ratio)
            fill_rect = pygame.Rect(rect.x, rect.bottom - fill_h, rect.width, fill_h)
            pygame.draw.rect(surface, _COLORS[spell], fill_rect, border_radius=6)

        pygame.draw.rect(surface, _BORDER, rect, 2, border_radius=6)

        surface.blit(font.render(spell, True, _LABEL), (rect.x + 10, rect.y + 8))
        hint = font.render(f"[{_HOTKEYS[spell]}]", True, _KEY_HINT)
        surface.blit(hint, (rect.right - hint.get_width() - 8, rect.y + 8))
        status = "ready" if remaining <= 0 else f"{remaining:.0f}s"
        surface.blit(font.render(status, True, _LABEL), (rect.x + 10, rect.y + 30))

        if rect.collidepoint(mouse_pos):
            hovered_rect = rect
            hovered_spell = spell

    if hovered_spell is not None:
        ui_tooltip.render(surface, font, _DESCRIPTIONS[hovered_spell], hovered_rect)

    return outer.bottom
