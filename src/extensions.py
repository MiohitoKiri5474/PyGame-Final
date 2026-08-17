"""Render/HUD extension points so later tickets (buildings, HUD panels)
never need to edit game.py - they register a callback here instead."""

from typing import Any, Callable

# Any, not pygame.Surface/World, to keep this module pygame-free per the
# project's test seam - it only ever forwards these values, never inspects them.
_hud_line_providers: list[Callable[..., str]] = []
_overlay_renderers: list[Callable[..., None]] = []


def register_hud_line(provider: Callable[..., str]) -> None:
    _hud_line_providers.append(provider)


def hud_lines(world: Any) -> list[str]:
    return [provider(world) for provider in _hud_line_providers]


def register_overlay(renderer: Callable[..., None]) -> None:
    _overlay_renderers.append(renderer)


def render_overlays(surface: Any, world: Any, camera: Any) -> None:
    for renderer in _overlay_renderers:
        renderer(surface, world, camera)
