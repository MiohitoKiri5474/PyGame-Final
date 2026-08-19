import os
import pygame
import pytest

from constants import TILE_SIZE
from render_celestial import get_celestial_position, render_celestial_dial
from render_fog import render_fog_tile


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def test_get_celestial_position_arc():
    rect = pygame.Rect(10, 10, 170, 112)
    # Start of phase (progress 0.0) -> left side near horizon
    x0, y0 = get_celestial_position(rect, 0.0)
    assert x0 == rect.x + 24.0
    assert y0 == rect.bottom - 42.0

    # Mid of phase (progress 0.5) -> center, highest peak (apex)
    x_mid, y_mid = get_celestial_position(rect, 0.5)
    assert x_mid == rect.centerx
    assert y_mid < y0  # Peak is higher vertically (smaller y in screen space)
    assert y_mid == (rect.bottom - 42.0) - 36.0

    # End of phase (progress 1.0) -> right side near horizon
    x1, y1 = get_celestial_position(rect, 1.0)
    assert x1 == rect.right - 24.0
    assert y1 == rect.bottom - 42.0


def test_render_celestial_dial_day_and_night_renders_without_error():
    surface = pygame.Surface((300, 200))
    rect = pygame.Rect(10, 10, 170, 112)
    font = pygame.font.Font(None, 20)
    big_font = pygame.font.Font(None, 28)

    # Test day render at dawn, noon, dusk
    render_celestial_dial(surface, rect, font, big_font, "day", round_number=1, timer=10.0, duration=120.0)
    render_celestial_dial(surface, rect, font, big_font, "day", round_number=1, timer=60.0, duration=120.0)
    render_celestial_dial(surface, rect, font, big_font, "day", round_number=1, timer=110.0, duration=120.0)

    # Test night render at nightfall, midnight, dawn
    render_celestial_dial(surface, rect, font, big_font, "night", round_number=2, timer=5.0, duration=60.0)
    render_celestial_dial(surface, rect, font, big_font, "night", round_number=2, timer=30.0, duration=60.0)
    render_celestial_dial(surface, rect, font, big_font, "night", round_number=2, timer=55.0, duration=60.0)


def test_render_fog_tile_renders_without_error():
    surface = pygame.Surface((100, 100))
    rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)

    # Interior fog tile
    render_fog_tile(surface, rect, col=5, row=8, time_s=12.34, has_revealed_neighbor=False)

    # Frontier fog tile with revealed neighbor (border cloud scalloping)
    render_fog_tile(surface, rect, col=2, row=3, time_s=56.78, has_revealed_neighbor=True)


def test_render_drifting_fog_layer_renders_without_error():
    from world import World
    from camera import Camera
    from render_fog import render_drifting_fog_layer

    world = World(npc_count=1)
    camera = Camera()
    surface = pygame.Surface((800, 600))

    render_drifting_fog_layer(surface, world.grid, camera, time_s=10.5)



