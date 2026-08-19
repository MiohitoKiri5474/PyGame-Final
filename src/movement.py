import math

from coords import tile_center


def step_toward_path(
    x: float, y: float, path: list[tuple[int, int]], speed: float, dt: float
) -> tuple[float, float, list[tuple[int, int]]]:
    """Advance (x, y) one tick toward path[0]; pops the waypoint on arrival.
    Shared by NPC and Monster since both use continuous pixel movement over
    an A* tile path (per the "same movement system" decision)."""
    if not path:
        return x, y, path

    target_x, target_y = tile_center(*path[0])
    dx, dy = target_x - x, target_y - y
    dist = math.hypot(dx, dy)
    step = speed * dt

    if dist <= step:
        return target_x, target_y, path[1:]
    return x + dx / dist * step, y + dy / dist * step, path


def step_toward_point(
    x: float, y: float, target_x: float, target_y: float, speed: float, dt: float
) -> tuple[float, float]:
    """Advance (x, y) one tick straight toward an arbitrary pixel point - no
    tile grid, no obstacle awareness. For a follower trailing a moving leader
    (e.g. a tamed animal chasing its owner's recent position) where retracing
    the leader's already-valid path makes real pathfinding unnecessary."""
    dx, dy = target_x - x, target_y - y
    dist = math.hypot(dx, dy)
    step = speed * dt

    if dist <= step:
        return target_x, target_y
    return x + dx / dist * step, y + dy / dist * step
