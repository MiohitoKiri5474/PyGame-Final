from constants import WAVE_FULL_CLEAR_POINTS, WAVE_PARTIAL_CLEAR_KILLS_PER_POINT


def evaluate_wave(no_monsters_remain: bool, killed_count: int) -> int:
    """Skill points earned for the night that just ended. Full clear is
    judged by whether any monster is still alive at day start, not by
    comparing spawn/kill counts for that night specifically - monsters have
    no despawn-at-dawn mechanic, so a monster that survived from an earlier
    night would otherwise let killing it wrongly count toward "this night's"
    tally and trigger a false full-clear bonus."""
    if no_monsters_remain and killed_count > 0:
        return WAVE_FULL_CLEAR_POINTS
    return killed_count // WAVE_PARTIAL_CLEAR_KILLS_PER_POINT
