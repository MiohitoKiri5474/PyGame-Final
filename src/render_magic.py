import math
import pygame

from extensions import register_fx_overlay


def draw_magic_fx(surface: pygame.Surface, world, camera) -> None:
    """Draws ultra magnificent Paper Mario styled origami magic spell visual effects."""
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
            # ── 2. Paper Mario Ultra Magnificent Origami Phoenix Fire Vortex ───
            fire_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            cx, cy = 60, 60

            # (1) Ground Rotating Flame Mandala / Blazing Seal (12 flame teeth)
            seal_rot = (1.0 - prog) * 160.0
            seal_r = int(32 * (1.0 - prog * 0.3)) + 4
            mandala_pts = []
            for i in range(12):
                ang = math.radians(seal_rot + i * 30)
                r = seal_r if i % 2 == 0 else int(seal_r * 0.6)
                mandala_pts.append((cx + int(math.cos(ang) * r), cy + 10 + int(math.sin(ang) * (r * 0.55))))
            if len(mandala_pts) >= 3:
                pygame.draw.polygon(fire_surf, (255, 50, 20, int(150 * prog)), mandala_pts)
                pygame.draw.lines(fire_surf, (255, 220, 50, int(220 * prog)), True, mandala_pts, 2)

            # (2) Multi-layered Spiraling Origami Flame Dragons (4 Spiral Arms)
            spiral_time = (1.0 - prog) * 16.0
            flame_layers = [
                ((230, 25, 20, int(220 * prog)), 24, 45, 12),   # Deep Crimson
                ((255, 110, 25, int(235 * prog)), 18, 48, 10),  # Volcanic Orange
                ((255, 215, 40, int(250 * prog)), 12, 52, 8),   # Solar Yellow
                ((255, 255, 230, int(255 * prog)), 6, 56, 5),   # Searing White Core
            ]

            for layer_col, arm_dist, reach_h, flame_w in flame_layers:
                for arm in range(3):
                    arm_angle = spiral_time + arm * (math.pi * 2 / 3)
                    bx = cx + int(math.cos(arm_angle) * (arm_dist * prog))
                    by = cy + int(math.sin(arm_angle) * (arm_dist * 0.6 * prog))
                    tx = cx + int(math.cos(arm_angle + 0.8) * (arm_dist * 0.4 * prog))
                    ty = by - int(reach_h * prog)

                    p_left = (bx - flame_w, by)
                    p_right = (bx + flame_w, by)
                    p_tip = (tx, ty)
                    pygame.draw.polygon(fire_surf, layer_col, [p_left, p_tip, p_right])
                    pygame.draw.circle(fire_surf, layer_col, (bx, by), flame_w)

            # (3) Central Blazing Starburst Flare
            star_flare_sz = max(4, int(22 * prog))
            for ang_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
                rad = math.radians(ang_deg)
                fx = cx + int(math.cos(rad) * star_flare_sz * (1.3 if ang_deg % 90 == 0 else 0.8))
                fy = cy - 10 + int(math.sin(rad) * star_flare_sz * (1.3 if ang_deg % 90 == 0 else 0.8))
                pygame.draw.line(fire_surf, (255, 255, 240, int(250 * prog)), (cx, cy - 10), (fx, fy), 2)

            # (4) 8 Orbiting Ember Paper Confetti Sparks
            for i in range(8):
                e_ang = spiral_time * 1.5 + i * (math.pi / 4)
                e_r = (14 + i * 2) * prog
                ex = cx + int(math.cos(e_ang) * e_r)
                ey = cy - int((1.0 - prog) * 45) - i * 3 + int(math.sin(e_ang) * (e_r * 0.4))
                e_sz = max(2, int(4 * prog))
                pygame.draw.rect(fire_surf, (255, 230, 80, int(240 * prog)), pygame.Rect(ex - e_sz // 2, ey - e_sz // 2, e_sz, e_sz + 2))

            surface.blit(fire_surf, (screen_x - 60, screen_y - 60))

        elif spell == "Freeze" or color == (100, 200, 255):
            # ── 3. Paper Mario Ultra Magnificent Diamond Frost Hexagram & 3D Spires ───
            ice_surf = pygame.Surface((130, 130), pygame.SRCALPHA)
            cx, cy = 65, 65

            # (1) Grand Hexagram Snowflake Mandala Ground Seal
            seal_rot = (1.0 - prog) * 120.0
            outer_r = int(42 * (1.0 - prog * 0.25)) + 4

            tri1 = []
            tri2 = []
            for i in range(3):
                a1 = math.radians(seal_rot + i * 120)
                a2 = math.radians(seal_rot + 60 + i * 120)
                tri1.append((cx + int(math.cos(a1) * outer_r), cy + int(math.sin(a1) * (outer_r * 0.6))))
                tri2.append((cx + int(math.cos(a2) * outer_r), cy + int(math.sin(a2) * (outer_r * 0.6))))

            pygame.draw.lines(ice_surf, (90, 210, 255, int(220 * prog)), True, tri1, 2)
            pygame.draw.lines(ice_surf, (160, 240, 255, int(240 * prog)), True, tri2, 2)
            pygame.draw.circle(ice_surf, (120, 225, 255, int(160 * prog)), (cx, cy), outer_r, 2)

            # (2) 6 Fractal Ice Branches spreading with diamond nodes
            for i in range(6):
                ang = math.radians(seal_rot + i * 60)
                bx = cx + int(math.cos(ang) * outer_r)
                by = cy + int(math.sin(ang) * (outer_r * 0.6))
                pygame.draw.line(ice_surf, (220, 250, 255, int(230 * prog)), (cx, cy), (bx, by), 2)
                node_sz = max(2, int(4 * prog))
                node_pts = [
                    (bx, by - node_sz),
                    (bx + node_sz, by),
                    (bx, by + node_sz),
                    (bx - node_sz, by),
                ]
                pygame.draw.polygon(ice_surf, (255, 255, 255, int(250 * prog)), node_pts)

            # (3) Five Rising 3D Faceted Origami Ice Crystal Spires
            spire_configs = [
                (0, 4, 46, 12),     # Giant Center Spire
                (-16, -2, 34, 9),   # Left Spire
                (16, -2, 34, 9),    # Right Spire
                (-10, 10, 28, 8),   # Front-Left Spire
                (10, 10, 28, 8),    # Front-Right Spire
            ]

            for ox, oy, max_h, max_w in spire_configs:
                sh = int(max_h * (0.4 + 0.6 * prog))
                sw = int(max_w * (0.5 + 0.5 * prog))
                sx_base = cx + ox
                sy_base = cy + oy
                sy_tip = sy_base - sh

                left_pts = [(sx_base, sy_base), (sx_base - sw, sy_base - sh // 3), (sx_base, sy_tip)]
                right_pts = [(sx_base, sy_base), (sx_base + sw, sy_base - sh // 3), (sx_base, sy_tip)]

                pygame.draw.polygon(ice_surf, (40, 130, 215, int(210 * prog)), left_pts)
                pygame.draw.polygon(ice_surf, (110, 225, 255, int(240 * prog)), right_pts)
                pygame.draw.line(ice_surf, (255, 255, 255, int(255 * prog)), (sx_base, sy_base), (sx_base, sy_tip), 2)
                pygame.draw.lines(ice_surf, (220, 250, 255, int(230 * prog)), True, left_pts + [(sx_base + sw, sy_base - sh // 3)], 1)

            # (4) 12 Orbiting Diamond Frost Sparkle Stars
            for i in range(12):
                star_ang = (1.0 - prog) * 8.0 + i * (math.pi / 6)
                star_r = (20 + (i % 3) * 6) * prog
                st_x = cx + int(math.cos(star_ang) * star_r)
                st_y = cy - 12 + int(math.sin(star_ang) * (star_r * 0.7)) - int((1.0 - prog) * 20)
                st_sz = max(2, int(4 * (0.6 + 0.4 * math.sin(prog * 10.0 + i))))
                st_pts = [
                    (st_x, st_y - st_sz),
                    (st_x + st_sz // 2, st_y),
                    (st_x, st_y + st_sz),
                    (st_x - st_sz // 2, st_y),
                ]
                pygame.draw.polygon(ice_surf, (240, 255, 255, int(245 * prog)), st_pts)

            surface.blit(ice_surf, (screen_x - 65, screen_y - 65))
        else:
            fx = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.circle(fx, (*color, alpha), (24, 24), 20, 3)
            surface.blit(fx, (screen_x - 24, screen_y - 24))


register_fx_overlay(draw_magic_fx)


