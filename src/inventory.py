from collections import defaultdict


class Inventory:
    def __init__(self):
        self._counts: dict[str, int] = defaultdict(int)

    def get(self, resource: str) -> int:
        return self._counts[resource]

    def add(self, resource: str, amount: int) -> None:
        self._counts[resource] += amount

    def spend(self, resource: str, amount: int) -> bool:
        if self._counts[resource] < amount:
            return False
        self._counts[resource] -= amount
        return True

    def items(self) -> dict[str, int]:
        return dict(self._counts)
