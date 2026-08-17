"""Magic spell visual effects, cooldown tick hook, and HUD status overlay (tickets 18, 19, 20).

Registers via extensions.py:
- register_tick: ticks spellbook cooldowns and VFX timers
- register_hud_line: shows spell availability and cooldown timers
- register_overlay: renders active spell visual effects
"""

import pygame

from constants import TILE_SIZE
from extensions import register_hud_line, register_overlay, register_tick

# Active visual effects: list of dict(x=float, y=float, type=str, timer=float, max_timer=float)
_active_vfx: list[dict] = []


def trigger_vfx(x: float, y: float, vfx_type: str, duration: float = 0.3) -> None:
    """Spawn a visual effect at world coordinates (x, y)."""
    _active_vfx.append({
        "x": x,
        "y": y,
        "type": vfx_type,
        "timer": duration,
        "max_timer": duration,
    })


def _tick_magic(world, dt: float) -> None:
    if hasattr(world, "spellbook") and world.spellbook is not None:
        world.spellbook.tick(dt)

    for vfx in _active_vfx:
        vfx["timer"] -= dt
    _active_vfx[:] = [vfx for vfx in _active_vfx if vfx["timer"] > 0]


def _magic_hud_line(world) -> str:
    if not hasattr(world, "spellbook") or world.spellbook is None:
        return ""

    sb = world.spellbook
    spells = [
        ("F1", "Fire", "fire"),
        ("F2", "Lightning", "lightning"),
        ("F3", "Freeze", "freeze"),
    ]
    parts = []
    for hotkey, name, key in spells:
        rem = sb.remaining(key)
        if rem <= 0:
            status = "Ready"
        else:
            status = f"{rem:.0f}s"
        parts.append(f"[{hotkey}] {name}: {status}")

    return "Spells: " + "  ".join(parts)


def _draw_magic_vfx(surface: pygame.Surface, world, camera) -> None:
    for vfx in _active_vfx:
        sx = int(vfx["x"] - camera.x)
        sy = int(vfx["y"] - camera.y)
        progress = vfx["timer"] / vfx["max_timer"]
        alpha = int(255 * progress)

        if vfx["type"] == "lightning":
            # Bright yellow-white electric bolt / circle
            radius = int(TILE_SIZE * (1.5 - 0.5 * progress))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 200, alpha), (radius, radius), radius)
            pygame.draw.circle(s, (255, 255, 255, min(255, alpha + 50)), (radius, radius), max(2, radius // 2))
            surface.blit(s, (sx - radius, sy - radius))

        elif vfx["type"] == "fire":
            # Fiery orange-red burst
            radius = int(TILE_SIZE * (1.8 - 0.8 * progress))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 100, 30, alpha), (radius, radius), radius)
            pygame.draw.circle(s, (255, 220, 50, min(255, alpha + 40)), (radius, radius), max(2, radius // 2))
            surface.blit(s, (sx - radius, sy - radius))

        elif vfx["type"] == "freeze":
            # Cyan icy frost shockwave
            radius = int(TILE_SIZE * 2.5 * (1.0 - 0.3 * progress))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 220, 255, alpha // 2), (radius, radius), radius)
            pygame.draw.circle(s, (200, 245, 255, alpha), (radius, radius), radius, 3)
            surface.blit(s, (sx - radius, sy - radius))


register_tick(_tick_magic)
register_hud_line(_magic_hud_line)
register_overlay(_draw_magic_vfx)
