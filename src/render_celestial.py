from __future__ import annotations

import math
import time
import pygame

from constants import DAY_SECONDS, NIGHT_SECONDS


from sprites import cloud_sprite, moon_sprite, sun_sprite



def get_celestial_position(rect: pygame.Rect, progress: float) -> tuple[float, float]:
    """Calculates the parabolic arc (x, y) coordinates for the Sun or Moon
    across the celestial skybox based on phase progress (0.0 to 1.0)."""
    p = max(0.0, min(1.0, progress))
    x_start = rect.x + 24.0
    x_end = rect.right - 24.0
    cur_x = x_start + p * (x_end - x_start)
    # Peak elevation in the middle of the phase
    apex_y = rect.bottom - 42.0
    cur_y = apex_y - math.sin(p * math.pi) * 36.0
    return cur_x, cur_y


def _draw_paper_cloud(
    surface: pygame.Surface,
    cx: float,
    cy: float,
    scale: float = 1.0,
    alpha: int = 210,
    cloud_index: int = 0,
) -> None:
    """Draws the cloud using cached cloud PNG sprite #cloud_index with scaling and alpha."""
    cw = max(16, int(48 * scale))
    c_surf = cloud_sprite(index=cloud_index, width=cw, alpha=alpha)
    if c_surf is not None:
        surface.blit(c_surf, c_surf.get_rect(center=(int(cx), int(cy))))





_TIMER_FONT: pygame.font.Font | None = None


def _get_timer_font() -> pygame.font.Font:
    global _TIMER_FONT
    if _TIMER_FONT is None:
        _TIMER_FONT = pygame.font.Font(None, 50)
    return _TIMER_FONT


def render_celestial_dial(

    surface: pygame.Surface,
    rect: pygame.Rect,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
    phase: str,
    round_number: int,
    timer: float,
    duration: float,
) -> None:
    """Draws the Paper Mario style Celestial Skybox with Sun/Moon rising arc,
    daytime drifting clouds, twinkling night stars, and countdown timer."""
    p = max(0.0, min(1.0, timer / max(1.0, duration)))
    remaining = max(0.0, duration - timer)
    time_s = time.monotonic()
    is_day = (phase.lower() == "day")

    # 1. Skybox Background with elegant semi-transparency (no color shift over time)
    sky_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    if is_day:
        # Clean, steady, semi-transparent sky blue
        sky_bg = (40, 105, 180, 160)
    else:
        # Deep midnight indigo
        sky_bg = (14, 18, 36, 185)

    pygame.draw.rect(sky_surf, sky_bg, pygame.Rect(0, 0, rect.width, rect.height), border_radius=8)


    # 2. Celestial Atmosphere Details (Night Stars or Background Cloud Wisps)
    if not is_day:
        # Twinkling Paper Stars
        star_positions = [
            (22, 28, 0.0), (45, 18, 1.2), (72, 34, 2.5),
            (105, 20, 3.7), (135, 30, 4.8), (148, 16, 0.9),
            (32, 48, 2.1), (120, 48, 3.3),
        ]
        for sx, sy, seed in star_positions:
            twinkle = 0.5 + 0.5 * math.sin(time_s * 4.0 + seed)
            star_sz = 2 if twinkle > 0.65 else 1
            star_alpha = int(160 + 95 * twinkle)
            pygame.draw.circle(sky_surf, (240, 245, 255, star_alpha), (sx, sy), star_sz)
            if twinkle > 0.85:
                # Faint cross shine
                pygame.draw.line(sky_surf, (255, 255, 255, int(180 * twinkle)), (sx - 2, sy), (sx + 2, sy), 1)
                pygame.draw.line(sky_surf, (255, 255, 255, int(180 * twinkle)), (sx, sy - 2), (sx, sy + 2), 1)

    surface.blit(sky_surf, rect.topleft)

    # 3. Daytime Background Cloud Layer (Behind Sun)
    if is_day:
        # Distant background cloud drifting gently
        c3_x = rect.x + ((time_s * 5.0 + rect.width * 0.7) % (rect.width + 50)) - 25
        c3_y = rect.y + 36 + math.sin(time_s * 1.2 + 1.0) * 1.5
        _draw_paper_cloud(surface, c3_x, c3_y, scale=0.70, alpha=150, cloud_index=2)

    # 4. Sun / Moon Trajectory & Celestial Body
    cx, cy = get_celestial_position(rect, p)

    if is_day:
        # 1. Radiant Solar Aura & Rotating Corona Rays (Behind the Sun)
        corona_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
        corona_center = (35, 35)

        pulse = 1.0 + 0.07 * math.sin(time_s * 2.8)
        aura_r1 = int(24 * pulse)
        aura_r2 = int(18 * pulse)
        pygame.draw.circle(corona_surf, (255, 230, 90, 70), corona_center, aura_r1)
        pygame.draw.circle(corona_surf, (255, 245, 140, 110), corona_center, aura_r2)

        # 8 Rotating Radiant Solar Ray Spikes
        ray_rot = time_s * 1.5
        for i in range(8):
            ang = ray_rot + i * (math.pi / 4.0)
            r_in = 14.0 * pulse
            r_out = (21.0 + math.sin(time_s * 3.2 + i) * 3.0) * pulse
            p1 = (corona_center[0] + math.cos(ang) * r_out, corona_center[1] + math.sin(ang) * r_out)
            p2 = (corona_center[0] + math.cos(ang - 0.20) * r_in, corona_center[1] + math.sin(ang - 0.20) * r_in)
            p3 = (corona_center[0] + math.cos(ang + 0.20) * r_in, corona_center[1] + math.sin(ang + 0.20) * r_in)
            pygame.draw.polygon(corona_surf, (255, 220, 65, 200), [p1, p2, p3])

        surface.blit(corona_surf, (int(cx - 35), int(cy - 35)))

        # 2. Main Sun Body (with smooth breathing scale & gentle sway tilt)
        cur_sun_sz = max(32, int(46 * pulse))
        custom_sun = sun_sprite(cur_sun_sz)
        sway_angle = math.sin(time_s * 1.6) * 5.0  # gentle breathing tilt

        if custom_sun is not None:
            rot_sun = pygame.transform.rotate(custom_sun, sway_angle)
            surface.blit(rot_sun, rot_sun.get_rect(center=(int(cx), int(cy))))
        else:
            # Fallback procedural sun core
            sun_surf = pygame.Surface((44, 44), pygame.SRCALPHA)
            pygame.draw.circle(sun_surf, (255, 235, 70), (22, 22), 11)
            pygame.draw.circle(sun_surf, (255, 165, 30), (22, 22), 11, 2)
            pygame.draw.circle(sun_surf, (255, 255, 255), (19, 19), 3)
            rot_sun = pygame.transform.rotate(sun_surf, sway_angle)
            surface.blit(rot_sun, rot_sun.get_rect(center=(int(cx), int(cy))))

        # 3. Twinkling Golden Sun Glints / Sparkles
        for i in range(3):
            sp_ang = time_s * 1.8 + i * (2.0 * math.pi / 3.0)
            sp_dist = 24.0 + math.sin(time_s * 2.5 + i) * 3.0
            sp_x = cx + math.cos(sp_ang) * sp_dist
            sp_y = cy + math.sin(sp_ang) * sp_dist
            sp_alpha = int(140 + 115 * math.sin(time_s * 4.0 + i * 2.0))
            if sp_alpha > 50:
                sp_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.line(sp_surf, (255, 255, 240, sp_alpha), (4, 1), (4, 7), 1)
                pygame.draw.line(sp_surf, (255, 255, 240, sp_alpha), (1, 4), (7, 4), 1)
                surface.blit(sp_surf, (int(sp_x - 4), int(sp_y - 4)))

        # 4. Daytime Foreground Drifting Clouds (In Front of Sky and Sun)
        # Cloud 1 (Upper sky drifting)
        c1_x = rect.x + ((time_s * 11.0 + 15) % (rect.width + 60)) - 30
        c1_y = rect.y + 28 + math.sin(time_s * 1.4) * 2.0
        _draw_paper_cloud(surface, c1_x, c1_y, scale=0.88, alpha=220, cloud_index=0)

        # Cloud 2 (Middle/lower sky drifting at a relaxed pace)
        c2_x = rect.x + ((time_s * 7.5 + rect.width * 0.45) % (rect.width + 70)) - 35
        c2_y = rect.y + 52 + math.cos(time_s * 1.0) * 2.5
        _draw_paper_cloud(surface, c2_x, c2_y, scale=1.05, alpha=235, cloud_index=5)


    else:
        custom_moon = moon_sprite(38)
        if custom_moon is not None:
            surface.blit(custom_moon, custom_moon.get_rect(center=(int(cx), int(cy))))
        else:
            # Silver-Cyan Crescent Moon
            moon_surf = pygame.Surface((38, 38), pygame.SRCALPHA)
            moon_center = (19, 19)
            # Lunar halo
            pygame.draw.circle(moon_surf, (140, 200, 255, 60), moon_center, 17)
            pygame.draw.circle(moon_surf, (200, 235, 255, 100), moon_center, 12)

            # Crescent Moon
            pygame.draw.circle(moon_surf, (235, 245, 255), moon_center, 9)
            pygame.draw.circle(moon_surf, (170, 210, 245), moon_center, 9, 1)
            # Cutout to form crescent
            cutout_pos = (moon_center[0] + 4, moon_center[1] - 3)
            pygame.draw.circle(moon_surf, (14, 18, 36), cutout_pos, 7)
            surface.blit(moon_surf, (int(cx - 19), int(cy - 19)))



    # 6. Box Outline (Paper Mario Dark Frame)
    pygame.draw.rect(surface, (70, 74, 86), rect, 2, border_radius=8)

    # 7. Badges & Digital Countdown Text
    # Top Round Pill
    round_text = f"Round {round_number}"
    round_surf = font.render(round_text, True, (240, 240, 245))
    round_bg_w = round_surf.get_width() + 14
    round_bg_h = round_surf.get_height() + 4
    round_bg = pygame.Surface((round_bg_w, round_bg_h), pygame.SRCALPHA)
    pygame.draw.rect(round_bg, (18, 20, 28, 210), pygame.Rect(0, 0, round_bg_w, round_bg_h), border_radius=4)
    pygame.draw.rect(round_bg, (70, 74, 86, 220), pygame.Rect(0, 0, round_bg_w, round_bg_h), 1, border_radius=4)
    surface.blit(round_bg, (rect.centerx - round_bg_w // 2, rect.y + 6))
    surface.blit(round_surf, (rect.centerx - round_surf.get_width() // 2, rect.y + 8))

    # Bottom Phase & Countdown Display
    phase_label = "DAY" if is_day else "NIGHT"
    phase_col = (255, 230, 80) if is_day else (135, 220, 255)
    phase_surf = font.render(phase_label, True, phase_col)

    # High-visibility large digital countdown
    t_font = _get_timer_font()
    countdown_text = f"{int(remaining)}s"
    count_surf = t_font.render(countdown_text, True, (255, 255, 255))
    count_shadow = t_font.render(countdown_text, True, (12, 14, 20))

    bottom_y = rect.bottom - count_surf.get_height() - 4

    # Phase badge background
    phase_bg_w = phase_surf.get_width() + 10
    phase_bg_h = phase_surf.get_height() + 4
    phase_bg = pygame.Surface((phase_bg_w, phase_bg_h), pygame.SRCALPHA)
    pygame.draw.rect(phase_bg, (18, 20, 28, 200), pygame.Rect(0, 0, phase_bg_w, phase_bg_h), border_radius=4)
    pygame.draw.rect(phase_bg, (70, 74, 86, 210), pygame.Rect(0, 0, phase_bg_w, phase_bg_h), 1, border_radius=4)

    phase_y = rect.bottom - phase_bg_h - 10
    surface.blit(phase_bg, (rect.x + 10, phase_y))
    surface.blit(phase_surf, (rect.x + 15, phase_y + 2))

    # Large shadowed digital countdown
    count_x = rect.right - count_surf.get_width() - 10
    surface.blit(count_shadow, (count_x + 2, bottom_y + 2))
    surface.blit(count_surf, (count_x, bottom_y))

