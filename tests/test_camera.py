from camera import (
    Camera,
    GRID_MAX_OFFSET_X,
    GRID_MAX_OFFSET_Y,
    MIN_OFFSET_X,
    MAX_OFFSET_X,
    MIN_OFFSET_Y,
    MAX_OFFSET_Y,
)
from constants import CAMERA_MARGIN_BOTTOM, CAMERA_MARGIN_LEFT, CAMERA_MARGIN_RIGHT, CAMERA_MARGIN_TOP


def test_new_camera_centers_over_the_map_ignoring_hud_margins():
    # Initial view should center on the grid itself, not the margin-widened
    # pan range - otherwise a fresh game would open already off-center.
    camera = Camera()
    assert camera.x == GRID_MAX_OFFSET_X // 2
    assert camera.y == GRID_MAX_OFFSET_Y // 2


def test_pan_left_stops_past_the_map_edge_by_the_left_margin():
    camera = Camera()
    camera.pan(dx=-1, dy=0, dt=1000.0)  # huge dt: slam into the clamp
    assert camera.x == -CAMERA_MARGIN_LEFT
    assert camera.x == MIN_OFFSET_X


def test_pan_right_stops_past_the_map_edge_by_the_right_margin():
    camera = Camera()
    camera.pan(dx=1, dy=0, dt=1000.0)
    assert camera.x == GRID_MAX_OFFSET_X + CAMERA_MARGIN_RIGHT
    assert camera.x == MAX_OFFSET_X


def test_pan_up_stops_past_the_map_edge_by_the_top_margin():
    camera = Camera()
    camera.pan(dx=0, dy=-1, dt=1000.0)
    assert camera.y == -CAMERA_MARGIN_TOP
    assert camera.y == MIN_OFFSET_Y


def test_pan_down_stops_past_the_map_edge_by_the_bottom_margin():
    camera = Camera()
    camera.pan(dx=0, dy=1, dt=1000.0)
    assert camera.y == GRID_MAX_OFFSET_Y + CAMERA_MARGIN_BOTTOM
    assert camera.y == MAX_OFFSET_Y


def test_pan_is_a_no_op_past_either_clamp():
    camera = Camera()
    camera.pan(dx=-1, dy=-1, dt=1000.0)
    x_at_clamp, y_at_clamp = camera.x, camera.y
    camera.pan(dx=-1, dy=-1, dt=1000.0)
    assert (camera.x, camera.y) == (x_at_clamp, y_at_clamp)
