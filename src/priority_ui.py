"""Priority table UI overlay (ticket 05).

Press P to toggle the overlay. When open:
- Lists every alive NPC with their task-type priority ranking
- Arrow keys (Up/Down) select a task row for the highlighted NPC
- Arrow keys (Left/Right) or +/- swap the selected task's priority
- Tab switches between NPCs
- P or Escape closes the overlay

Writes directly to each NPC's .priority list — the same data structure
TaskQueue.claim_for() already reads, so changes take effect immediately.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_TEXT,
)
from task import TASK_TYPES

if TYPE_CHECKING:
    from npc import NPC


# --- Colours ---
_BG = (20, 22, 28, 210)          # semi-transparent panel background
_HEADER_COLOR = (255, 214, 100)  # yellow header
_NPC_ACTIVE = (100, 180, 255)    # selected NPC highlight
_NPC_INACTIVE = (160, 160, 170)  # unselected NPC
_ROW_SELECTED = (50, 60, 80)     # selected task row background
_ROW_HOVER = (35, 40, 55)        # alternating row
_TASK_TEXT = (220, 220, 220)     # task name text
_RANK_TEXT = (140, 140, 140)     # rank number text
_HINT_TEXT = (110, 110, 120)     # hint text at bottom


class PriorityTableUI:
    """In-game overlay for reordering each NPC's task-type priority."""

    def __init__(self):
        self.visible = False
        self.selected_npc_index = 0
        self.selected_task_index = 0

    # ------------------------------------------------------------------
    # Public API called by Game
    # ------------------------------------------------------------------

    def toggle(self) -> None:
        self.visible = not self.visible
        if self.visible:
            self.selected_npc_index = 0
            self.selected_task_index = 0

    def handle_key(self, key: int, npcs: list["NPC"]) -> bool:
        """Handle a keypress while the overlay is open.
        Returns True if the key was consumed (so Game doesn't process it further)."""
        if not self.visible or not npcs:
            return False

        if key in (pygame.K_p, pygame.K_ESCAPE):
            self.visible = False
            return True

        # Switch NPC
        if key == pygame.K_TAB:
            self.selected_npc_index = (self.selected_npc_index + 1) % len(npcs)
            self.selected_task_index = 0
            return True

        npc = npcs[self._clamped_npc_index(npcs)]
        priority = self._ensure_priority(npc)
        task_count = len(priority)
        if task_count == 0:
            return False

        # Navigate task rows
        if key == pygame.K_UP:
            self.selected_task_index = (self.selected_task_index - 1) % task_count
            return True
        if key == pygame.K_DOWN:
            self.selected_task_index = (self.selected_task_index + 1) % task_count
            return True

        # Move task priority (Left/Right or -/+)
        if key in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
            self._swap_priority(priority, self.selected_task_index, -1)
            npc.priority = priority
            return True
        if key in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_KP_PLUS,
                   pygame.K_EQUALS):  # = key (unshifted +)
            self._swap_priority(priority, self.selected_task_index, +1)
            npc.priority = priority
            return True

        return False

    def render(self, surface: pygame.Surface, font: pygame.font.Font,
               npcs: list["NPC"]) -> None:
        """Draw the priority table overlay."""
        if not self.visible or not npcs:
            return

        # Semi-transparent background
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(_BG)
        surface.blit(overlay, (0, 0))

        # Layout constants
        panel_w = 440
        panel_h = min(500, WINDOW_HEIGHT - 40)
        panel_x = (WINDOW_WIDTH - panel_w) // 2
        panel_y = (WINDOW_HEIGHT - panel_h) // 2
        pad = 16
        row_h = 28

        # Panel border
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (30, 32, 40), panel_rect)
        pygame.draw.rect(surface, (80, 80, 90), panel_rect, 1)

        y = panel_y + pad

        # Title
        title = font.render("NPC Priority Table  [P to close]", True, _HEADER_COLOR)
        surface.blit(title, (panel_x + pad, y))
        y += title.get_height() + 12

        # NPC tabs
        npc_idx = self._clamped_npc_index(npcs)
        tab_x = panel_x + pad
        for i, npc in enumerate(npcs):
            label = f"NPC {npc.id}"
            color = _NPC_ACTIVE if i == npc_idx else _NPC_INACTIVE
            tab_surf = font.render(label, True, color)
            if i == npc_idx:
                # Underline active tab
                underline_rect = pygame.Rect(
                    tab_x, y + tab_surf.get_height() + 1,
                    tab_surf.get_width(), 2
                )
                pygame.draw.rect(surface, _NPC_ACTIVE, underline_rect)
            surface.blit(tab_surf, (tab_x, y))
            tab_x += tab_surf.get_width() + 20

        y += row_h + 8

        # Column headers
        header = font.render("Rank    Task Type                  ◄ ► to reorder", True, _HINT_TEXT)
        surface.blit(header, (panel_x + pad, y))
        y += row_h

        # Task rows
        npc = npcs[npc_idx]
        priority = self._ensure_priority(npc)

        for rank, task_name in enumerate(priority):
            is_selected = (rank == self.selected_task_index)

            # Row background
            row_rect = pygame.Rect(panel_x + 4, y, panel_w - 8, row_h)
            if is_selected:
                pygame.draw.rect(surface, _ROW_SELECTED, row_rect)
                pygame.draw.rect(surface, _NPC_ACTIVE, row_rect, 1)
            elif rank % 2 == 1:
                pygame.draw.rect(surface, _ROW_HOVER, row_rect)

            # Rank number
            rank_text = font.render(f"  {rank + 1}.", True, _RANK_TEXT)
            surface.blit(rank_text, (panel_x + pad, y + 4))

            # Task name
            task_text = font.render(task_name, True, _TASK_TEXT)
            surface.blit(task_text, (panel_x + pad + 60, y + 4))

            # Selection indicator
            if is_selected:
                arrow = font.render("▸", True, _NPC_ACTIVE)
                surface.blit(arrow, (panel_x + 6, y + 4))

            y += row_h

        # Bottom hints
        y = panel_y + panel_h - row_h - pad
        hints = "[Tab] switch NPC   [↑↓] select task   [←→] change priority"
        hint_surf = font.render(hints, True, _HINT_TEXT)
        surface.blit(hint_surf, (panel_x + pad, y))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _clamped_npc_index(self, npcs: list["NPC"]) -> int:
        if not npcs:
            return 0
        return min(self.selected_npc_index, len(npcs) - 1)

    @staticmethod
    def _ensure_priority(npc: "NPC") -> list[str]:
        """If the NPC has no explicit priority, initialize it from the
        current TASK_TYPES registration order. This is the same fallback
        TaskQueue.claim_for() uses, but materialized so the UI has a
        concrete list to display and reorder."""
        if npc.priority is None:
            npc.priority = list(TASK_TYPES.keys())
        return npc.priority

    @staticmethod
    def _swap_priority(priority: list[str], index: int, direction: int) -> None:
        """Swap the task at *index* with its neighbor in *direction*
        (-1 = move up / higher priority, +1 = move down / lower priority).
        Wraps around at boundaries."""
        if len(priority) < 2:
            return
        target = (index + direction) % len(priority)
        priority[index], priority[target] = priority[target], priority[index]
