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
import task as task_module

if TYPE_CHECKING:
    from npc import NPC


# --- Colours ---
_BG = (20, 22, 28, 210)          # semi-transparent panel background
_HEADER_COLOR = (255, 214, 100)  # yellow header
_NPC_ACTIVE = (100, 180, 255)    # selected NPC highlight
_NPC_INACTIVE = (160, 160, 170)  # unselected NPC
_ROW_SELECTED = (50, 60, 80)     # selected task row background
_ROW_HOVER = (35, 40, 55)        # unselected row card fill
_BORDER = (70, 74, 86)           # unselected row card border, matches the build bar's
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

    def handle_key(self, key: int, npcs: list["NPC"]) -> None:
        """Process a key event when the UI is visible."""
        if not npcs:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.visible = False
            return

        alive_npcs = [n for n in npcs if not n.is_dead]
        if not alive_npcs:
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.visible = False
            return

        self.selected_npc_index = self._clamped_npc_index(alive_npcs)
        npc = alive_npcs[self.selected_npc_index]
        priority = self._ensure_priority(npc)

        if key in (pygame.K_p, pygame.K_ESCAPE):
            self.visible = False

        elif key == pygame.K_TAB:
            # Switch to next alive NPC
            self.selected_npc_index = (self.selected_npc_index + 1) % len(alive_npcs)
            # Re-ensure priority for the newly selected NPC
            new_npc = alive_npcs[self.selected_npc_index]
            new_pri = self._ensure_priority(new_npc)
            self.selected_task_index = min(self.selected_task_index, len(new_pri) - 1)

        elif key == pygame.K_UP:
            if priority:
                self.selected_task_index = (self.selected_task_index - 1) % len(priority)

        elif key == pygame.K_DOWN:
            if priority:
                self.selected_task_index = (self.selected_task_index + 1) % len(priority)

        elif key in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
            # Decrease priority / move down in list
            if priority and 0 <= self.selected_task_index < len(priority):
                self._swap_priority(priority, self.selected_task_index, +1)
                self.selected_task_index = (self.selected_task_index + 1) % len(priority)

        elif key in (pygame.K_RIGHT, pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            # Increase priority / move up in list
            if priority and 0 <= self.selected_task_index < len(priority):
                self._swap_priority(priority, self.selected_task_index, -1)
                self.selected_task_index = (self.selected_task_index - 1) % len(priority)

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        npcs: list["NPC"],
    ) -> None:
        """Draw the priority overlay centered on screen."""
        if not self.visible:
            return

        alive_npcs = [n for n in npcs if not n.is_dead]

        pad = 16
        row_h = 24
        row_gap = 6

        # Panel height scales with the active NPC's task-type count (task
        # types keep growing as tickets add more) instead of a fixed value -
        # a fixed 360px only fit ~9 rows and later rows/the footer hint
        # started rendering past the panel's own border once there were 11.
        self.selected_npc_index = self._clamped_npc_index(alive_npcs) if alive_npcs else 0
        row_count = len(self._ensure_priority(alive_npcs[self.selected_npc_index])) if alive_npcs else 0

        panel_w = 480
        panel_h = (
            pad * 2
            + (row_h + 8)  # title
            + (row_h + 12)  # NPC tabs
            + 8  # separator gap
            + max(1, row_count) * (row_h + row_gap)
            + (row_h + 8)  # footer hint
        )
        panel_x = (WINDOW_WIDTH - panel_w) // 2
        panel_y = max(8, (WINDOW_HEIGHT - panel_h) // 2)

        # Draw semi-transparent panel background
        overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        overlay.fill(_BG)
        surface.blit(overlay, (panel_x, panel_y))
        pygame.draw.rect(surface, _HEADER_COLOR, pygame.Rect(panel_x, panel_y, panel_w, panel_h), 2)

        y = panel_y + pad

        # Header title
        title_surf = font.render("NPC Priority Table", True, _HEADER_COLOR)
        surface.blit(title_surf, (panel_x + pad, y))
        y += row_h + 8

        if not alive_npcs:
            empty_surf = font.render("No alive NPCs", True, COLOR_TEXT)
            surface.blit(empty_surf, (panel_x + pad, y))
            return

        # NPC tabs
        tab_x = panel_x + pad
        for i, npc in enumerate(alive_npcs):
            is_active = i == self.selected_npc_index
            label = f"NPC #{npc.id}"
            color = _NPC_ACTIVE if is_active else _NPC_INACTIVE
            tab_surf = font.render(label, True, color)
            if is_active:
                # Underline active NPC
                tab_rect = tab_surf.get_rect(topleft=(tab_x, y))
                pygame.draw.rect(
                    surface,
                    _NPC_ACTIVE,
                    pygame.Rect(tab_rect.left, tab_rect.bottom + 2, tab_rect.width, 2),
                )
            surface.blit(tab_surf, (tab_x, y))
            tab_x += tab_surf.get_width() + 16

        y += row_h + 12

        # Separator line
        pygame.draw.line(
            surface,
            _ROW_HOVER,
            (panel_x + pad, y),
            (panel_x + panel_w - pad, y),
        )
        y += 8

        # Task list for active NPC
        active_npc = alive_npcs[self.selected_npc_index]
        priority = self._ensure_priority(active_npc)

        for rank, task_type in enumerate(priority, start=1):
            is_row_selected = rank - 1 == self.selected_task_index
            row_rect = pygame.Rect(panel_x + pad, y, panel_w - pad * 2, row_h)

            # Bordered card per row, matching the build bar's button style,
            # instead of a flat alternating-background list.
            pygame.draw.rect(surface, _ROW_SELECTED if is_row_selected else _ROW_HOVER, row_rect, border_radius=6)
            pygame.draw.rect(
                surface, _NPC_ACTIVE if is_row_selected else _BORDER, row_rect, 2 if is_row_selected else 1, border_radius=6
            )

            rank_surf = font.render(f"#{rank}", True, _RANK_TEXT)
            task_surf = font.render(task_type, True, _TASK_TEXT)

            surface.blit(rank_surf, (panel_x + pad + 8, y + 2))
            surface.blit(task_surf, (panel_x + pad + 48, y + 2))

            if is_row_selected:
                arrows_surf = font.render("[<- Higher]  [Lower ->]", True, _NPC_ACTIVE)
                surface.blit(
                    arrows_surf,
                    (panel_x + panel_w - pad - arrows_surf.get_width() - 8, y + 2),
                )

            y += row_h + row_gap

        # Footer hints
        y = panel_y + panel_h - row_h - pad
        hints = "[Tab] switch NPC   [Up/Down] select task   [Left/Right] change priority"
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
            npc.priority = list(task_module.TASK_TYPES.keys())
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
