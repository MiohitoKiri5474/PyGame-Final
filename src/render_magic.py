import math
import pygame

from extensions import register_fx_overlay


def draw_magic_fx(surface: pygame.Surface, world, camera) -> None:
    """Draws rich Paper Mario styled origami magic spell visual effects."""
    if not hasattr(world, "spellbook") or not hasattr(world.spellbook, "flashes"):
        return

    for flash in world.spellbook.flashes:
        x, y = flash["position"]
        screen_x = int(x - camera.x)
        screen_y = int(y - camera.y)
        prog = max(0.0, min(1.0, flash["timer"] / flash["duration"]))  # 1.0 -> 0.0
        spell = flash.get("spell", "")
        color = flash.get("color", (255, 255, 255))
        alpha = int(255 * prog)

        if spell == "Lightning" or color == (255, 255, 100):
            # ── 1. Paper Mario Origami Lightning Bolt ────────────────────
            bolt_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            sky_y = max(0, screen_y - 220)

            points = [
                (screen_x + 8, sky_y),
                (screen_x - 14, sky_y + 45),
                (screen_x + 16, sky_y + 90),
                (screen_x - 10, sky_y + 140),
                (screen_x + 12, sky_y + 180),
                (screen_x, screen_y),
            ]

            bolt_col_outer = (255, 235, 80, min(255, int(255 * prog * 1.2)))
            bolt_col_inner = (255, 255, 255, min(255, int(255 * prog * 1.5)))

            if len(points) >= 2:
                pygame.draw.lines(bolt_surf, bolt_col_outer, False, points, 6)
                pygame.draw.lines(bolt_surf, bolt_col_inner, False, points, 3)

            impact_radius = int((1.0 - prog) * 42) + 8
            pygame.draw.circle(bolt_surf, (255, 250, 150, int(220 * prog)), (screen_x, screen_y), impact_radius, 3)

            star_sz = int(24 * prog)
            if star_sz > 2:
                for angle_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
                    rad = math.radians(angle_deg)
                    ex = screen_x + int(math.cos(rad) * star_sz * 1.4)
                    ey = screen_y + int(math.sin(rad) * star_sz * 1.4)
                    pygame.draw.line(bolt_surf, (255, 255, 220, int(240 * prog)), (screen_x, screen_y), (ex, ey), 3)

            surface.blit(bolt_surf, (0, 0))

        elif spell == "Fire" or color == (255, 100, 50):
            # ── 2. Paper Mario Origami Flame Vortex ──────────────────────
            fire_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            center = (40, 40)

            time_offset = (1.0 - prog) * 12.0
            flame_colors = [
                (255, 60, 30, int(230 * prog)),    # Red flame
                (255, 140, 40, int(240 * prog)),   # Orange flame
                (255, 230, 70, int(255 * prog)),   # Yellow flame core
            ]

            for i, f_col in enumerate(flame_colors):
                petal_angle = time_offset + i * (math.pi * 2 / 3)
                px = center[0] + int(math.cos(petal_angle) * (14 - i * 3))
                py = center[1] + int(math.sin(petal_angle) * (14 - i * 3)) - int((1.0 - prog) * 16)
                rad = max(4, int((12 - i * 2) * prog))
                pygame.draw.circle(fire_surf, f_col, (px, py), rad)
                top_point = (px, py - int(rad * 1.8))
                left_point = (px - rad, py)
                right_point = (px + rad, py)
                pygame.draw.polygon(fire_surf, f_col, [left_point, top_point, right_point])

            burst_r = max(4, int((1.0 - prog) * 36))
            pygame.draw.circle(fire_surf, (255, 180, 50, int(180 * prog)), center, burst_r, 2)
            surface.blit(fire_surf, (screen_x - 40, screen_y - 40))

        elif spell == "Freeze" or color == (100, 200, 255):
            # ── 3. Paper Mario Origami Crystal Snowflake Seal ────────────
            ice_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            center = (40, 40)

            rot = (1.0 - prog) * 90.0
            ice_col_outer = (120, 220, 255, int(240 * prog))
            ice_col_inner = (240, 255, 255, int(255 * prog))

            arm_len = int(22 * prog) + 6
            if arm_len > 2:
                for i in range(6):
                    angle = math.radians(rot + i * 60)
                    ax = center[0] + int(math.cos(angle) * arm_len)
                    ay = center[1] + int(math.sin(angle) * arm_len)
                    pygame.draw.line(ice_surf, ice_col_outer, center, (ax, ay), 3)
                    pygame.draw.line(ice_surf, ice_col_inner, center, (ax, ay), 1)

                    bx = center[0] + int(math.cos(angle) * arm_len * 0.6)
                    by = center[1] + int(math.sin(angle) * arm_len * 0.6)
                    pygame.draw.circle(ice_surf, (220, 250, 255, int(230 * prog)), (bx, by), 3)

            cube_w = int(26 * prog) + 6
            cube_h = int(32 * prog) + 6
            cube_rect = pygame.Rect(center[0] - cube_w // 2, center[1] - cube_h // 2, cube_w, cube_h)
            pygame.draw.rect(ice_surf, (160, 230, 255, int(90 * prog)), cube_rect, border_radius=4)
            pygame.draw.rect(ice_surf, (220, 250, 255, int(220 * prog)), cube_rect, 2, border_radius=4)

            surface.blit(ice_surf, (screen_x - 40, screen_y - 40))
        else:
            fx = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.circle(fx, (*color, alpha), (24, 24), 20, 3)
            surface.blit(fx, (screen_x - 24, screen_y - 24))


register_fx_overlay(draw_magic_fx)

