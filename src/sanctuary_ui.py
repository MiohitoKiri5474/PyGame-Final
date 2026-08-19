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


class SanctuaryUI:
    """Right-side Paper Mario style Healing Sanctuary Box for injured colonists."""

    PANEL_WIDTH = 224
    PANEL_HEIGHT = 280
    PANEL_X = WINDOW_WIDTH - 240
    PANEL_Y = 120

    def __init__(self):
        self.rect = pygame.Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_WIDTH, self.PANEL_HEIGHT)

    def is_hovering(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def handle_click(self, pos: tuple[int, int], world) -> object | None:
        """Handles clicks on deploy/return buttons for resting NPCs."""
        if not self.rect.collidepoint(pos):
            return None

        resting = [npc for npc in world.npcs if getattr(npc, "is_resting", False)]
        slot_y = self.PANEL_Y + 42
        slot_h = 74

        for i, npc in enumerate(resting):
            btn_rect = pygame.Rect(self.PANEL_X + self.PANEL_WIDTH - 76, slot_y + i * slot_h + 40, 68, 22)
            if btn_rect.collidepoint(pos):
                return npc
        return None

    def render(self, screen: pygame.Surface, font: pygame.font.Font, world, is_dragging_over: bool = False) -> None:
        resting_npcs = [npc for npc in world.npcs if getattr(npc, "is_resting", False)]
        time_s = time.monotonic()

        # 1. Parchment Panel Background
        panel_surf = pygame.Surface((self.PANEL_WIDTH, self.PANEL_HEIGHT), pygame.SRCALPHA)
        bg_col = (250, 245, 230, 235) if not is_dragging_over else (235, 255, 235, 245)
        pygame.draw.rect(panel_surf, bg_col, pygame.Rect(0, 0, self.PANEL_WIDTH, self.PANEL_HEIGHT), border_radius=10)

        # Border (Pulses green when dragging over)
        border_col = (75, 185, 75) if is_dragging_over else (115, 80, 45)
        border_w = 3 if is_dragging_over else 2
        pygame.draw.rect(panel_surf, border_col, pygame.Rect(0, 0, self.PANEL_WIDTH, self.PANEL_HEIGHT), border_w, border_radius=10)

        # Header Bar
        header_rect = pygame.Rect(0, 0, self.PANEL_WIDTH, 34)
        header_col = (60, 140, 70) if is_dragging_over else (85, 60, 35)
        pygame.draw.rect(panel_surf, header_col, header_rect, border_top_left_radius=10, border_top_right_radius=10)

        screen.blit(panel_surf, (self.PANEL_X, self.PANEL_Y))

        # Header Text & Green Cross
        cross_cx = self.PANEL_X + 18
        cross_cy = self.PANEL_Y + 17
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(cross_cx - 2, cross_cy - 7, 5, 15), border_radius=2)
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(cross_cx - 7, cross_cy - 2, 15, 5), border_radius=2)
        pygame.draw.rect(screen, (50, 220, 90), pygame.Rect(cross_cx - 1, cross_cy - 6, 3, 13))
        pygame.draw.rect(screen, (50, 220, 90), pygame.Rect(cross_cx - 6, cross_cy - 1, 13, 3))

        title_text = f"療傷休養所 ({len(resting_npcs)}/3)"
        title_surf = font.render(title_text, True, (255, 255, 255))
        screen.blit(title_surf, (self.PANEL_X + 32, self.PANEL_Y + 8))

        # 2. Render Slots
        slot_y = self.PANEL_Y + 42
        slot_h = 74

        for i in range(3):
            cur_sy = slot_y + i * slot_h
            slot_rect = pygame.Rect(self.PANEL_X + 8, cur_sy, self.PANEL_WIDTH - 16, slot_h - 6)

            if i < len(resting_npcs):
                npc = resting_npcs[i]
                # Filled Slot Card
                pygame.draw.rect(screen, (240, 235, 220), slot_rect, border_radius=6)
                pygame.draw.rect(screen, (160, 210, 160), slot_rect, 1, border_radius=6)

                # NPC Paper Sprite with subtle healing float
                float_offset = math.sin(time_s * 3.5 + i) * 2.0
                sprite = npc_sprite(npc.role)
                if sprite is not None:
                    icon_surf = pygame.transform.smoothscale(sprite, (26, 26))
                    screen.blit(icon_surf, (self.PANEL_X + 12, cur_sy + 8 + int(float_offset)))

                # Role & Healing Text
                role_col = (40, 120, 50) if npc.role == ROLE_FARMER else ((60, 100, 180) if npc.role == ROLE_KNIGHT else (130, 60, 170))
                role_surf = font.render(f"{npc.role or 'Colonist'}", True, role_col)
                screen.blit(role_surf, (self.PANEL_X + 44, cur_sy + 6))

                # Health Bar
                bar_x = self.PANEL_X + 44
                bar_y = cur_sy + 24
                bar_w = 92
                bar_h = 6
                pygame.draw.rect(screen, COLOR_BAR_BG, pygame.Rect(bar_x, bar_y, bar_w, bar_h), border_radius=3)
                hp_ratio = max(0.0, min(1.0, npc.health / npc.max_health))
                hp_fill_w = int(bar_w * hp_ratio)
                if hp_fill_w > 0:
                    pygame.draw.rect(screen, (65, 210, 85), pygame.Rect(bar_x, bar_y, hp_fill_w, bar_h), border_radius=3)

                hp_text = f"{int(npc.health)}/{int(npc.max_health)}"
                hp_lbl = font.render(hp_text, True, (45, 80, 45))
                screen.blit(pygame.transform.scale(hp_lbl, (int(hp_lbl.get_width() * 0.75), int(hp_lbl.get_height() * 0.75))), (bar_x + bar_w + 4, bar_y - 2))

                # Hunger Bar
                hunger_y = cur_sy + 36
                pygame.draw.rect(screen, COLOR_BAR_BG, pygame.Rect(bar_x, hunger_y, bar_w, bar_h), border_radius=3)
                hg_ratio = max(0.0, min(1.0, npc.hunger / NPC_MAX_HUNGER))
                hg_fill_w = int(bar_w * hg_ratio)
                if hg_fill_w > 0:
                    pygame.draw.rect(screen, COLOR_HUNGER_BAR, pygame.Rect(bar_x, hunger_y, hg_fill_w, bar_h), border_radius=3)

                # Deploy / Return Button
                btn_rect = pygame.Rect(self.PANEL_X + self.PANEL_WIDTH - 76, cur_sy + 40, 68, 22)
                pygame.draw.rect(screen, (70, 150, 80), btn_rect, border_radius=4)
                pygame.draw.rect(screen, (40, 100, 50), btn_rect, 1, border_radius=4)
                btn_surf = font.render("出擊", True, (255, 255, 255))
                screen.blit(btn_surf, (btn_rect.centerx - btn_surf.get_width() // 2, btn_rect.centery - btn_surf.get_height() // 2))

            else:
                # Empty Slot
                pygame.draw.rect(screen, (230, 225, 210, 180), slot_rect, border_radius=6)
                pygame.draw.rect(screen, (180, 175, 160), slot_rect, 1, border_radius=6)
                if i == len(resting_npcs):
                    empty_lbl = font.render("📥 拖曳小人至此", True, (140, 135, 120))
                    screen.blit(empty_lbl, (slot_rect.centerx - empty_lbl.get_width() // 2, slot_rect.centery - empty_lbl.get_height() // 2))
                else:
                    empty_lbl = font.render("--- 空位 ---", True, (170, 165, 150))
                    screen.blit(empty_lbl, (slot_rect.centerx - empty_lbl.get_width() // 2, slot_rect.centery - empty_lbl.get_height() // 2))
