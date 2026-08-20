def is_wall_blocked(buildings, x: int, y: int) -> bool:
    """True if a Wall building occupies (x, y). Shared by NPC and monster
    pathfinding (ticket 07) - dependency-free so neither task.py nor
    monster.py risk a circular import pulling it in."""
    return any(b.type == "Wall" and b.x == x and b.y == y for b in buildings)


def is_mountain_blocked(grid, x: int, y: int) -> bool:
    """True if (x, y) is on mountain terrain, which is naturally impassable."""
    if grid is None or not grid.in_bounds(x, y):
        return False
    return getattr(grid.get(x, y), "terrain", None) == "mountain"

