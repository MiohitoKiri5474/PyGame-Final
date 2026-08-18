"""Skill upgrade UI overlay (ticket 23).

Press K to toggle the overlay. When open:
- Lists all 6 skills with their current global level
- Up/Down selects a skill
- Right arrow / Enter / + spends one available point on the selected skill
- K or Escape closes the overlay

Thin rendering layer over skills.py's tested logic - not itself unit
tested, matching priority_ui.py's precedent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from constants import SKILL_NAMES, WINDOW_HEIGHT, WINDOW_WIDTH
from skills import spend_point

if TYPE_CHECKING:
    from world import World

_BG = (20, 22, 28, 210)
_HEADER_COLOR = (255, 214, 100)
_ROW_SELECTED = (50, 60, 80)
_ROW_HOVER = (35, 40, 55)
_SKILL_TEXT = (220, 220, 220)
_LEVEL_TEXT = (140, 200, 140)
_HINT_TEXT = (110, 110, 120)
_POINTS_TEXT = (255, 214, 100)


class SkillUI:
    """In-game overlay for spending global skill points."""

    def __init__(self):
        self.visible = False
        self.selected_index = 0

    def toggle(self) -> None:
        self.visible = not self.visible
        if self.visible:
            self.selected_index = 0

    def handle_key(self, key: int, world: "World", points_available: int) -> int:
        """Process a key event when the UI is visible. Returns the
        (possibly decremented) points_available for the caller to store."""
        if key in (pygame.K_k, pygame.K_ESCAPE):
            self.visible = False
            return points_available

        if key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(SKILL_NAMES)
        elif key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(SKILL_NAMES)
        elif key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            skill = SKILL_NAMES[self.selected_index]
            points_available, _ = spend_point(world, points_available, skill)

        return points_available

    def render(self, surface: pygame.Surface, font: pygame.font.Font, world: "World", points_available: int) -> None:
        if not self.visible:
            return

        panel_w = 420
        panel_h = 280
        panel_x = (WINDOW_WIDTH - panel_w) // 2
        panel_y = (WINDOW_HEIGHT - panel_h) // 2

        overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        overlay.fill(_BG)
        surface.blit(overlay, (panel_x, panel_y))
        pygame.draw.rect(surface, _HEADER_COLOR, pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

        pad = 16
        row_h = 26
        y = panel_y + pad

        title_surf = font.render("Skill Upgrades", True, _HEADER_COLOR)
        surface.blit(title_surf, (panel_x + pad, y))
        points_surf = font.render(f"Points available: {points_available}", True, _POINTS_TEXT)
        surface.blit(points_surf, (panel_x + panel_w - pad - points_surf.get_width(), y))
        y += row_h + 8

        for i, skill in enumerate(SKILL_NAMES):
            row_rect = pygame.Rect(panel_x + pad, y, panel_w - pad * 2, row_h)
            if i == self.selected_index:
                pygame.draw.rect(surface, _ROW_SELECTED, row_rect)
            elif i % 2 == 0:
                pygame.draw.rect(surface, _ROW_HOVER, row_rect)

            name_surf = font.render(skill, True, _SKILL_TEXT)
            level_surf = font.render(f"Lv {world.skills[skill]}", True, _LEVEL_TEXT)
            surface.blit(name_surf, (panel_x + pad + 8, y + 2))
            surface.blit(level_surf, (panel_x + panel_w - pad - level_surf.get_width() - 8, y + 2))
            y += row_h + 2

        y = panel_y + panel_h - row_h - pad
        hint_surf = font.render("[Up/Down] select   [Enter/Right] spend point   [K/Esc] close", True, _HINT_TEXT)
        surface.blit(hint_surf, (panel_x + pad, y))
