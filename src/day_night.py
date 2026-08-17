from constants import DAY_SECONDS, NIGHT_SECONDS

DAY = "day"
NIGHT = "night"


class DayNightCycle:
    def __init__(self):
        self.phase = DAY
        self.timer = 0.0
        self.round_number = 1

    def duration(self) -> float:
        return DAY_SECONDS if self.phase == DAY else NIGHT_SECONDS

    def update(self, dt: float) -> bool:
        """Advance the clock; returns True the tick a phase transition fires."""
        self.timer += dt
        if self.timer >= self.duration():
            self.timer = 0.0
            if self.phase == DAY:
                self.phase = NIGHT
            else:
                self.phase = DAY
                self.round_number += 1
            return True
        return False

    def remaining(self) -> float:
        return max(0.0, self.duration() - self.timer)
