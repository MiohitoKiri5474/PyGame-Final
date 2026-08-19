from constants import WAVE_FULL_CLEAR_POINTS, WAVE_PARTIAL_CLEAR_KILLS_PER_POINT


def evaluate_wave(no_monsters_remain: bool, killed_count: int) -> int:
    """Skill points earned for the night that just ended. Full clear is
    judged by whether any monster is still alive right at day start - the
    caller must check this *before* clearing survivors out for their dawn
    retreat to their nest, otherwise every dawn would look like a full
    clear regardless of whether anything was actually killed."""
    if no_monsters_remain and killed_count > 0:
        return WAVE_FULL_CLEAR_POINTS
    return killed_count // WAVE_PARTIAL_CLEAR_KILLS_PER_POINT
