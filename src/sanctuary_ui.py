import math
import time
import pygame

from constants import (
    COLOR_BAR_BG,
    COLOR_HUNGER_BAR,
    NPC_MAX_HUNGER,
    ROLE_FARMER,
    ROLE_KNIGHT,
    ROLE_MAGE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from sprites import npc_sprite

_MARGIN = 10
_WIDTH = 150
_PANEL_X = WINDOW_WIDTH - _MARGIN - _WIDTH
_PANEL_Y = 144
_PANEL_HEIGHT = 264

_BG = (24, 26, 32)
_BORDER = (70, 74, 86)
_BORDER_DRAG = (80, 220, 120)
_LABEL = (225, 225, 230)
_SLOT_BG = (32, 35, 44)
_SLOT_BORDER = (55, 60, 72)
_EMPTY_LABEL = (120, 124, 136)


class SanctuaryUI:
    """Right-side Healing Sanctuary Box aligned with top buttons."""

    PANEL_WIDTH = _WIDTH
    PANEL_HEIGHT = _PANEL_HEIGHT
    PANEL_X = _PANEL_X
    PANEL_Y = _PANEL_Y

    def __init__(self):
        self.rect = pygame.Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_WIDTH, self.PANEL_HEIGHT)

    def is_hovering(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def handle_click(self, pos: tuple[int, int], world) -> object | None:
        """Handles clicks on deploy buttons for resting NPCs."""
        if not self.rect.collidepoint(pos):
            return None

        resting = [npc for npc in world.npcs if getattr(npc, "is_resting", False)]
        slot_y = self.PANEL_Y + 38
        slot_h = 72

        for i, npc in enumerate(resting):
            btn_rect = pygame.Rect(self.PANEL_X + self.PANEL_WIDTH - 58, slot_y + i * slot_h + 40, 52, 22)
            if btn_rect.collidepoint(pos):
                return npc
        return None

    def render(self, screen: pygame.Surface, font: pygame.font.Font, world, is_dragging_over: bool = False) -> None:
        resting_npcs = [npc for npc in world.npcs if getattr(npc, "is_resting", False)]
        time_s = time.monotonic()

        # 1. Main Background Box (Matching top buttons dark slate style)
        pygame.draw.rect(screen, _BG, self.rect, border_radius=6)
        border_col = _BORDER_DRAG if is_dragging_over else _BORDER
        border_w = 2 if is_dragging_over else 1
        pygame.draw.rect(screen, border_col, self.rect, border_w, border_radius=6)

        # Header: Green cross icon + Sanctuary Title
        cross_cx = self.PANEL_X + 16
        cross_cy = self.PANEL_Y + 18
        pygame.draw.rect(screen, (50, 220, 90), pygame.Rect(cross_cx - 1, cross_cy - 6, 3, 13), border_radius=1)
        pygame.draw.rect(screen, (50, 220, 90), pygame.Rect(cross_cx - 6, cross_cy - 1, 13, 3), border_radius=1)

        title_text = f"Sanctuary ({len(resting_npcs)}/3)"
        title_surf = font.render(title_text, True, _LABEL)
        # Panel is narrow (150px, minus the cross icon) - shrink to match the
        # scaled-down labels used throughout the rest of this box below.
        title_scaled = pygame.transform.scale(
            title_surf, (int(title_surf.get_width() * 0.82), int(title_surf.get_height() * 0.82))
        )
        screen.blit(title_scaled, (self.PANEL_X + 28, self.PANEL_Y + 10))

        # 2. Render 3 Compact Resting Slots
        slot_y = self.PANEL_Y + 36
        slot_h = 72

        for i in range(3):
            cur_sy = slot_y + i * slot_h
            slot_rect = pygame.Rect(self.PANEL_X + 6, cur_sy, self.PANEL_WIDTH - 12, slot_h - 6)

            if i < len(resting_npcs):
                npc = resting_npcs[i]
                # Filled Slot Card
                pygame.draw.rect(screen, _SLOT_BG, slot_rect, border_radius=4)
                pygame.draw.rect(screen, (60, 140, 80) if is_dragging_over else _SLOT_BORDER, slot_rect, 1, border_radius=4)

                # NPC Paper Sprite with subtle healing float
                float_offset = math.sin(time_s * 3.5 + i) * 2.0
                sprite = npc_sprite(npc.role)
                if sprite is not None:
                    icon_surf = pygame.transform.smoothscale(sprite, (22, 22))
                    screen.blit(icon_surf, (self.PANEL_X + 10, cur_sy + 8 + int(float_offset)))

                # Role Label
                role_col = (110, 215, 120) if npc.role == ROLE_FARMER else ((110, 160, 245) if npc.role == ROLE_KNIGHT else (205, 120, 255))
                role_name = npc.role or "Villager"
                role_surf = font.render(role_name, True, role_col)
                # Scale role text slightly to fit cleanly
                role_scaled = pygame.transform.scale(role_surf, (int(role_surf.get_width() * 0.85), int(role_surf.get_height() * 0.85)))
                screen.blit(role_scaled, (self.PANEL_X + 36, cur_sy + 6))

                # Health Bar
                bar_x = self.PANEL_X + 36
                bar_y = cur_sy + 22
                bar_w = 50
                bar_h = 5
                pygame.draw.rect(screen, COLOR_BAR_BG, pygame.Rect(bar_x, bar_y, bar_w, bar_h), border_radius=2)
                hp_ratio = max(0.0, min(1.0, npc.health / npc.max_health))
                hp_fill_w = int(bar_w * hp_ratio)
                if hp_fill_w > 0:
                    pygame.draw.rect(screen, (65, 210, 85), pygame.Rect(bar_x, bar_y, hp_fill_w, bar_h), border_radius=2)

                hp_text = f"{int(npc.health)}/{int(npc.max_health)}"
                hp_lbl = font.render(hp_text, True, (160, 220, 170))
                hp_lbl_scaled = pygame.transform.scale(hp_lbl, (int(hp_lbl.get_width() * 0.70), int(hp_lbl.get_height() * 0.70)))
                screen.blit(hp_lbl_scaled, (bar_x + bar_w + 4, bar_y - 2))

                # Hunger Bar
                hunger_y = cur_sy + 32
                pygame.draw.rect(screen, COLOR_BAR_BG, pygame.Rect(bar_x, hunger_y, bar_w, bar_h), border_radius=2)
                hg_ratio = max(0.0, min(1.0, npc.hunger / NPC_MAX_HUNGER))
                hg_fill_w = int(bar_w * hg_ratio)
                if hg_fill_w > 0:
                    pygame.draw.rect(screen, COLOR_HUNGER_BAR, pygame.Rect(bar_x, hunger_y, hg_fill_w, bar_h), border_radius=2)

                # Deploy Button
                btn_rect = pygame.Rect(self.PANEL_X + self.PANEL_WIDTH - 58, cur_sy + 40, 50, 20)
                pygame.draw.rect(screen, (36, 75, 48), btn_rect, border_radius=3)
                pygame.draw.rect(screen, (75, 160, 95), btn_rect, 1, border_radius=3)
                btn_surf = font.render("Deploy", True, (215, 255, 220))
                btn_scaled = pygame.transform.scale(btn_surf, (int(btn_surf.get_width() * 0.75), int(btn_surf.get_height() * 0.75)))
                screen.blit(btn_scaled, (btn_rect.centerx - btn_scaled.get_width() // 2, btn_rect.centery - btn_scaled.get_height() // 2))

            else:
                # Empty Slot Card
                pygame.draw.rect(screen, (28, 30, 38), slot_rect, border_radius=4)
                pygame.draw.rect(screen, (45, 48, 58), slot_rect, 1, border_radius=4)
                if i == len(resting_npcs):
                    empty_lbl = font.render("Drag NPC here", True, _EMPTY_LABEL)
                    empty_scaled = pygame.transform.scale(empty_lbl, (int(empty_lbl.get_width() * 0.8), int(empty_lbl.get_height() * 0.8)))
                    screen.blit(empty_scaled, (slot_rect.centerx - empty_scaled.get_width() // 2, slot_rect.centery - empty_scaled.get_height() // 2))
                else:
                    empty_lbl = font.render("-- Empty --", True, (80, 84, 96))
                    empty_scaled = pygame.transform.scale(empty_lbl, (int(empty_lbl.get_width() * 0.8), int(empty_lbl.get_height() * 0.8)))
                    screen.blit(empty_scaled, (slot_rect.centerx - empty_scaled.get_width() // 2, slot_rect.centery - empty_scaled.get_height() // 2))
