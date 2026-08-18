"""Per-NPC stats panel, toggled by N.

Split out of the always-visible top bar since a growing roster (population
cap rises with House count) would otherwise push the corner text taller
forever - open this on demand instead, same precedent as P/K's overlays.
Read-only: lists every alive NPC's role, HP, hunger, attack/defense, and
current task in a table. Thin rendering layer, not itself unit tested,
matching priority_ui.py's precedent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from constants import NPC_MAX_HUNGER, WINDOW_HEIGHT, WINDOW_WIDTH

if TYPE_CHECKING:
    from npc import NPC

_BG = (20, 22, 28, 220)
_HEADER_COLOR = (255, 214, 100)
_TEXT = (220, 220, 220)
_ROW_ALT = (32, 36, 48)
_HEALTH_COLOR = (210, 110, 110)
_HUNGER_COLOR = (220, 160, 40)
_HINT_TEXT = (110, 110, 120)

_PANEL_W = 560
_ROW_H = 26
_COLS = (("NPC", 0, 56), ("Role", 56, 90), ("HP", 146, 90), ("Hunger", 236, 100), ("Atk/Def", 336, 90), ("Task", 426, 120))


class NpcStatusUI:
    def __init__(self):
        self.visible = False

    def toggle(self) -> None:
        self.visible = not self.visible

    def close(self) -> None:
        self.visible = False

    def render(self, surface: pygame.Surface, font: pygame.font.Font, npcs: list["NPC"]) -> None:
        if not self.visible:
            return

        alive = [n for n in npcs if not n.is_dead]
        pad = 16
        header_h = 32
        hint_h = 28  # reserved row for the "[N]/[Esc] to close" hint below the table
        panel_h = header_h + (max(1, len(alive)) + 1) * _ROW_H + hint_h + pad * 2
        panel_x = (WINDOW_WIDTH - _PANEL_W) // 2
        panel_y = (WINDOW_HEIGHT - panel_h) // 2

        overlay = pygame.Surface((_PANEL_W, panel_h), pygame.SRCALPHA)
        overlay.fill(_BG)
        surface.blit(overlay, (panel_x, panel_y))
        pygame.draw.rect(surface, _HEADER_COLOR, pygame.Rect(panel_x, panel_y, _PANEL_W, panel_h), 2)

        x0 = panel_x + pad
        y = panel_y + pad
        surface.blit(font.render("NPC Status", True, _HEADER_COLOR), (x0, y))
        y += header_h

        for label, col_x, _ in _COLS:
            surface.blit(font.render(label, True, _HINT_TEXT), (x0 + col_x, y))
        y += _ROW_H

        if not alive:
            surface.blit(font.render("No alive NPCs", True, _TEXT), (x0, y))
            y += _ROW_H
        else:
            for i, npc in enumerate(alive):
                if i % 2 == 1:
                    row_rect = pygame.Rect(x0 - 4, y - 2, _PANEL_W - pad * 2 + 8, _ROW_H)
                    pygame.draw.rect(surface, _ROW_ALT, row_rect)

                task_text = npc.task.type if npc.task else "idle"
                cells = [
                    (f"#{npc.id}", _TEXT),
                    (npc.role or "-", _TEXT),
                    (f"{int(npc.health)}/{int(npc.max_health)}", _HEALTH_COLOR),
                    (f"{int(npc.hunger)}/{int(NPC_MAX_HUNGER)}", _HUNGER_COLOR),
                    (f"{npc.attack}/{npc.defense}", _TEXT),
                    (task_text, _TEXT),
                ]
                for (text, color), (_, col_x, _w) in zip(cells, _COLS):
                    surface.blit(font.render(text, True, color), (x0 + col_x, y))
                y += _ROW_H

        hint = font.render("[N] or [Esc] to close", True, _HINT_TEXT)
        surface.blit(hint, (x0, panel_y + panel_h - pad - hint.get_height()))
