from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from constants import FOOD_SHELF_LIFE


@dataclass
class PerishableBatch:
    resource: str
    expires_in: float
    amount: int


class Inventory:
    def __init__(self):
        self._counts: dict[str, int] = defaultdict(int)
        self.ledger: list[PerishableBatch] = []

    def get(self, resource: str) -> int:
        return self._counts[resource]

    def add(self, resource: str, amount: int, shelf_life: float | None = None) -> None:
        if amount <= 0:
            return
        self._counts[resource] += amount
        if resource in FOOD_SHELF_LIFE:
            duration = shelf_life if shelf_life is not None else FOOD_SHELF_LIFE[resource]
            self.ledger.append(PerishableBatch(resource=resource, expires_in=duration, amount=amount))

    def spend(self, resource: str, amount: int) -> bool:
        if self._counts[resource] < amount or amount <= 0:
            return False
        self._counts[resource] -= amount
        if resource in FOOD_SHELF_LIFE:
            remaining_to_deduct = amount
            matching_batches = sorted(
                [b for b in self.ledger if b.resource == resource],
                key=lambda b: b.expires_in,
            )
            for batch in matching_batches:
                if remaining_to_deduct <= 0:
                    break
                deduct = min(batch.amount, remaining_to_deduct)
                batch.amount -= deduct
                remaining_to_deduct -= deduct
            self.ledger = [b for b in self.ledger if b.amount > 0]
        return True

    def spend_all(self, costs: dict[str, int]) -> bool:
        """Atomic multi-resource spend: either every resource in costs is
        affordable and all get deducted, or nothing is spent."""
        if any(self._counts[res] < amount for res, amount in costs.items()):
            return False
        for res, amount in costs.items():
            self.spend(res, amount)
        return True

    def consume_soonest_food(self, amount: int = 1) -> str | None:
        """Find and consume the food unit closest to expiration across all food types.
        Returns the resource name of the consumed food, or None if no food available."""
        if amount <= 0:
            return None
        food_batches = sorted(self.ledger, key=lambda b: b.expires_in)
        for batch in food_batches:
            if batch.amount >= amount:
                batch.amount -= amount
                self._counts[batch.resource] -= amount
                consumed_type = batch.resource
                self.ledger = [b for b in self.ledger if b.amount > 0]
                return consumed_type

        # Fallback: check flat counts for any food type if ledger is empty (e.g. legacy save)
        for food_type in ("crop", "meat", "mushrooms", "berries"):
            if self._counts[food_type] >= amount:
                self._counts[food_type] -= amount
                return food_type

        return None

    def tick_spoilage(self, dt: float) -> dict[str, int]:
        """Decrement expiry timers and discard spoiled food batches.
        Returns a dict of discarded {resource: amount}."""
        spoiled: dict[str, int] = defaultdict(int)
        remaining_batches = []
        for batch in self.ledger:
            batch.expires_in -= dt
            if batch.expires_in <= 0:
                spoiled[batch.resource] += batch.amount
                self._counts[batch.resource] = max(0, self._counts[batch.resource] - batch.amount)
            else:
                remaining_batches.append(batch)
        self.ledger = remaining_batches
        return dict(spoiled)

    def items(self) -> dict[str, int]:
        return dict(self._counts)

