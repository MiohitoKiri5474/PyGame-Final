class GameOverState:
    def __init__(self):
        self.is_over = False
        self.score = 0

    def check(self, npcs: list, round_number: int) -> bool:
        """Call once per tick, after death is resolved for the tick (combat
        and/or starvation). Returns True the tick game-over first triggers;
        no-ops on every call after that so the recorded score doesn't move."""
        if self.is_over:
            return False
        if not npcs:
            self.is_over = True
            self.score = round_number
            return True
        return False
