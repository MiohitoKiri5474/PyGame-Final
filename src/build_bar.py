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

from build_task import build_cost
from constants import WINDOW_HEIGHT, WINDOW_WIDTH
from sprites import building_icon
from tile_actions import build_task_types, building_label

if TYPE_CHECKING:
    from world import World

_BUTTON_W = 200
_BUTTON_H = 64
_GAP = 12
_MARGIN_BOTTOM = 10
_ICON = 26

_BG = (24, 26, 32)
_BORDER = (70, 74, 86)
_BORDER_SELECTED = (255, 214, 100)
_LABEL = (225, 225, 230)
_COST_OK = (150, 190, 140)
_COST_SHORT = (215, 110, 110)
_KEY_HINT = (130, 130, 140)


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

    def _buttons(self) -> list[tuple[str, pygame.Rect]]:
        types = build_task_types()
        if not types:
            return []
        total_w = len(types) * _BUTTON_W + (len(types) - 1) * _GAP
        x = (WINDOW_WIDTH - total_w) // 2
        y = WINDOW_HEIGHT - _BUTTON_H - _MARGIN_BOTTOM
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
                affordable = all(world.inventory.get(res) >= amt for res, amt in cost.items())
                text = ", ".join(f"{amt} {res}" for res, amt in cost.items())
                color = _COST_OK if affordable else _COST_SHORT
                surface.blit(font.render(text, True, color), (rect.x + 10, rect.y + 38))
