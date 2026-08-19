"""Bottom-of-screen building palette.

Unlike every other task type, "what to build" can't be inferred from the
tile you clicked (any claimed empty tile accepts all 5 buildings), so
building stays a two-step pick-then-place flow. Selecting a button arms
placement mode; game.py then queues that Build task on the next map click.

Thin rendering/hit-test layer over tile_actions.py + build_task's cost
registry - not itself unit tested, matching priority_ui.py's precedent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import ui_tooltip
from build_task import build_cost
from constants import WINDOW_HEIGHT, WINDOW_WIDTH
from sprites import building_icon, resource_sprite
from tile_actions import build_task_types, building_label

if TYPE_CHECKING:
    from world import World

_BUTTON_W = 230  # wide enough for two materials as "icon + amount + name" side by side (e.g. AnimalPen's wood + raw_stone)
_BUTTON_H = 64
_GAP = 12
_MARGIN_BOTTOM = 10
_ICON = 26
_COST_ICON = 16
_COST_GAP = 12  # horizontal gap between materials on the cost line

_OUTER_PAD = 10
_HEADER_H = 22
_DESC_H = 18

_BG = (24, 26, 32)
_OUTER_BG = (18, 20, 26)
_OUTER_BORDER = (60, 64, 76)
_BORDER = (70, 74, 86)
_BORDER_SELECTED = (255, 214, 100)
_LABEL = (225, 225, 230)
_COST_OK = (150, 190, 140)
_COST_SHORT = (215, 110, 110)
_KEY_HINT = (130, 130, 140)
_HEADER_COLOR = (255, 214, 100)
_DESC_COLOR = (150, 150, 158)

_HEADER_TEXT = "Building"
_DESC_TEXT = "Needs enough materials in inventory before it can be built"
_DESCRIPTIONS = {
    "Wall": "Blocks monster movement",
    "Tower": "Auto-attacks monsters within range",
    "House": "+1 max colonist population",
    "Farmland": "Grows crop over time - harvest it once ready",
    "AnimalPen": "Homes a tamed animal, producing meat over time",
}


class BuildBar:
    def __init__(self):
        self.selected: str | None = None  # a Build* task type, or None

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self.selected = None

    def toggle(self, task_type: str) -> None:
        """Clicking the armed button again disarms it, so there's always a
        way back to plain click-to-assign without a separate cancel button."""
        self.selected = None if self.selected == task_type else task_type

    def select_index(self, index: int) -> None:
        types = build_task_types()
        if 0 <= index < len(types):
            self.toggle(types[index])

    def cycle(self) -> None:
        types = build_task_types()
        if not types:
            return
        if self.selected not in types:
            self.selected = types[0]
            return
        nxt = types.index(self.selected) + 1
        self.selected = types[nxt] if nxt < len(types) else None  # wraps back to "nothing armed"

    # ------------------------------------------------------------------
    # Layout / input
    # ------------------------------------------------------------------

    def _outer_rect(self) -> pygame.Rect:
        types = build_task_types()
        if not types:
            return pygame.Rect(0, 0, 0, 0)
        total_w = len(types) * _BUTTON_W + (len(types) - 1) * _GAP
        width = total_w + _OUTER_PAD * 2
        height = _OUTER_PAD * 2 + _HEADER_H + _DESC_H + _BUTTON_H
        return pygame.Rect((WINDOW_WIDTH - width) // 2, WINDOW_HEIGHT - height - _MARGIN_BOTTOM, width, height)

    def panel_top(self) -> int:
        """The outer panel's own top y - so other bottom-left widgets (the
        minimap) can anchor directly above it without reaching into private
        layout details."""
        return self._outer_rect().top

    def _buttons(self) -> list[tuple[str, pygame.Rect]]:
        types = build_task_types()
        if not types:
            return []
        outer = self._outer_rect()
        x = outer.x + _OUTER_PAD
        y = outer.y + _OUTER_PAD + _HEADER_H + _DESC_H
        buttons = []
        for i, task_type in enumerate(types):
            rect = pygame.Rect(x + i * (_BUTTON_W + _GAP), y, _BUTTON_W, _BUTTON_H)
            buttons.append((task_type, rect))
        return buttons

    def is_hovering(self, pos: tuple[int, int]) -> bool:
        return any(rect.collidepoint(pos) for _, rect in self._buttons())

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Returns True if the click landed on the bar (so the caller must
        not also treat it as a map click)."""
        for task_type, rect in self._buttons():
            if rect.collidepoint(pos):
                self.toggle(task_type)
                return True
        return False

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface, font: pygame.font.Font, world: "World") -> None:
        outer = self._outer_rect()
        if outer.width == 0:
            return
        pygame.draw.rect(surface, _OUTER_BG, outer, border_radius=8)
        pygame.draw.rect(surface, _OUTER_BORDER, outer, 2, border_radius=8)

        font.set_bold(True)
        header_surf = font.render(_HEADER_TEXT, True, _HEADER_COLOR)
        font.set_bold(False)
        surface.blit(header_surf, (outer.x + _OUTER_PAD, outer.y + _OUTER_PAD - 2))
        desc_surf = font.render(_DESC_TEXT, True, _DESC_COLOR)
        surface.blit(desc_surf, (outer.x + _OUTER_PAD, outer.y + _OUTER_PAD + _HEADER_H - 4))

        mouse_pos = pygame.mouse.get_pos()
        hovered_rect = None
        hovered_label = None
        for i, (task_type, rect) in enumerate(self._buttons(), start=1):
            pygame.draw.rect(surface, _BG, rect, border_radius=6)
            selected = task_type == self.selected
            pygame.draw.rect(
                surface,
                _BORDER_SELECTED if selected else _BORDER,
                rect,
                3 if selected else 1,
                border_radius=6,
            )

            label = building_label(task_type)
            icon = building_icon(label, _ICON)
            if icon is not None:
                surface.blit(icon, icon.get_rect(topleft=(rect.x + 10, rect.y + 6)))

            surface.blit(font.render(label, True, _LABEL), (rect.x + 10 + _ICON + 10, rect.y + 9))
            surface.blit(font.render(f"[{i}]", True, _KEY_HINT), (rect.right - 30, rect.y + 9))

            cost = build_cost(task_type)
            if cost:
                # Each material gets its own icon and is colored by its own
                # sufficiency - short on just one of two materials no longer
                # paints the whole line red, since that used to hide which
                # specific material was the actual problem.
                cx = rect.x + 10
                cy = rect.y + 38
                for res, amt in cost.items():
                    icon = resource_sprite(res)
                    if icon is not None:
                        small = pygame.transform.smoothscale(icon, (_COST_ICON, _COST_ICON))
                        surface.blit(small, (cx, cy + 2))
                        cx += _COST_ICON + 4
                    amt_text = f"{amt} {res}"
                    affordable = world.inventory.get(res) >= amt
                    color = _COST_OK if affordable else _COST_SHORT
                    amt_surf = font.render(amt_text, True, color)
                    surface.blit(amt_surf, (cx, cy + 2))
                    cx += amt_surf.get_width() + _COST_GAP

            if rect.collidepoint(mouse_pos):
                hovered_rect = rect
                hovered_label = label

        if hovered_label is not None:
            # Anchored to the whole panel's top, not just the button's - the
            # button row sits close under the header/description text, so
            # "above the button" would cover that instead of clearing it.
            above_anchor = pygame.Rect(hovered_rect.x, outer.top, hovered_rect.width, 0)
            ui_tooltip.render(surface, font, _DESCRIPTIONS[hovered_label], above_anchor, placement="above")
