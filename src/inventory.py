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

    def spend_all(self, costs: dict[str, int]) -> bool:
        """Atomic multi-resource spend: either every resource in costs is
        affordable and all get deducted, or nothing is spent."""
        if any(self._counts[res] < amount for res, amount in costs.items()):
            return False
        for res, amount in costs.items():
            self._counts[res] -= amount
        return True
