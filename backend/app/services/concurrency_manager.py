"""Per-key concurrency manager with independent budgets.

Manages concurrent request budgets per API key. Each key has its own
concurrency limit that stacks independently from other keys.
"""

from __future__ import annotations

from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ApiKey


class ConcurrencyBudget:
    """Tracks concurrent request budget for a single key."""

    def __init__(self, limit: Optional[int], used: int = 0):
        self.limit = limit  # None means unlimited
        self.used = used

    @property
    def available(self) -> int:
        if self.limit is None:
            return float("inf")
        return max(0, self.limit - self.used)

    def reserve(self, delta: int = 1) -> bool:
        """Reserve delta slots. Returns True if allowed."""
        if self.limit is None:
            return True
        if self.used + delta > self.limit:
            return False
        self.used += delta
        return True

    def release(self, delta: int = 1):
        """Release delta slots."""
        if self.limit is None:
            return
        self.used = max(0, self.used - delta)


class ConcurrencyManager:
    """Manages per-key concurrency budgets.

    Budgets are independent per key. A key's concurrency limit does
    not affect other keys.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        # In-memory cache: key_id -> ConcurrencyBudget
        self._budgets: Dict[int, ConcurrencyBudget] = {}
        # Track which keys we've loaded
        self._loaded: set[int] = set()

    async def _ensure_loaded(self, key_id: int):
        """Ensure budget is loaded from DB for the given key."""
        if key_id in self._loaded:
            return
        stmt = select(ApiKey).where(ApiKey.id == key_id)
        result = await self.db.execute(stmt)
        key = result.scalar_one_or_none()
        if key is not None:
            self._budgets[key_id] = ConcurrencyBudget(
                limit=key.concurrency_limit,
            )
        self._loaded.add(key_id)

    async def check_and_reserve(self, key_id: int, delta: int = 1) -> bool:
        """Check if delta slots are available and reserve them.

        Returns True if the reservation succeeded (within budget),
        False if the key is at/consumed its limit.
        """
        await self._ensure_loaded(key_id)
        budget = self._budgets.get(key_id)
        if budget is None:
            # No concurrency limit configured; allow
            return True
        return budget.reserve(delta)

    async def release(self, key_id: int, delta: int = 1):
        """Release delta slots for the given key."""
        await self._ensure_loaded(key_id)
        budget = self._budgets.get(key_id)
        if budget is not None:
            budget.release(delta)

    async def get_budget(self, key_id: int) -> Optional[ConcurrencyBudget]:
        """Return the current budget for a key, loading from DB if needed."""
        await self._ensure_loaded(key_id)
        return self._budgets.get(key_id)

    async def refresh_all(self):
        """Refresh all budgets from the database."""
        stmt = select(ApiKey)
        result = await self.db.execute(stmt)
        keys = result.scalars().all()
        self._budgets = {}
        self._loaded = set()
        for key in keys:
            self._budgets[key.id] = ConcurrencyBudget(limit=key.concurrency_limit)
            self._loaded.add(key.id)
