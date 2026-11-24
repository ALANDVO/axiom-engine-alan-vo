"""Tests for per-key concurrency manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.concurrency_manager import ConcurrencyBudget, ConcurrencyManager


class TestConcurrencyBudget:
    def test_unlimited(self):
        budget = ConcurrencyBudget(limit=None)
        assert budget.available == float("inf")
        assert budget.reserve(1) is True
        assert budget.reserve(999) is True
        budget.release(1)

    def test_limited(self):
        budget = ConcurrencyBudget(limit=5)
        assert budget.available == 5
        assert budget.reserve(1) is True
        assert budget.available == 4
        assert budget.reserve(5) is False  # would exceed limit
        assert budget.available == 4  # unchanged after failed reserve
        budget.release(1)
        assert budget.available == 5

    def test_exact_limit(self):
        budget = ConcurrencyBudget(limit=3)
        assert budget.reserve(1) is True
        assert budget.reserve(1) is True
        assert budget.reserve(1) is True
        assert budget.reserve(1) is False  # 4th exceeds 3
        budget.release(1)
        assert budget.reserve(1) is True  # now allowed again


class TestConcurrencyManager:
    @pytest.mark.asyncio
    async def test_unlimited_key(self):
        """Key with no concurrency limit should always allow requests."""
        db = AsyncMock(spec=AsyncSession)
        # Setup: key 1 has no concurrency limit (limit=None)
        model = MagicMock()
        model.id = 1
        model.platform = "openai"
        model.key_name = "test"
        model.is_enabled = True
        model.concurrency_limit = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model]
        mock_result.scalar_one_or_none.return_value = model  # CRITICAL: make it return the model
        db.execute.return_value = mock_result

        manager = ConcurrencyManager(db)

        result = await manager.check_and_reserve(key_id=1, delta=1)
        assert result is True

        result = await manager.check_and_reserve(key_id=1, delta=100)
        assert result is True

        await manager.release(key_id=1, delta=1)

    @pytest.mark.asyncio
    async def test_limited_key_blocks_when_exhausted(self):
        """Key with limit=2 should block on 3rd request."""
        db = AsyncMock(spec=AsyncSession)
        # Key 1 has limit=2
        model = MagicMock()
        model.id = 1
        model.platform = "openai"
        model.key_name = "test"
        model.is_enabled = True
        model.concurrency_limit = 2

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model]
        mock_result.scalar_one_or_none.return_value = model  # CRITICAL
        db.execute.return_value = mock_result

        manager = ConcurrencyManager(db)

        assert await manager.check_and_reserve(key_id=1, delta=1) is True
        assert await manager.check_and_reserve(key_id=1, delta=1) is True
        assert await manager.check_and_reserve(key_id=1, delta=1) is False  # 3rd blocked
        assert await manager.check_and_reserve(key_id=1, delta=1) is False  # 4th also blocked

        await manager.release(key_id=1, delta=1)
        assert await manager.check_and_reserve(key_id=1, delta=1) is True  # 1 allowed after release

    @pytest.mark.asyncio
    async def test_independent_keys(self):
        """Key 1's budget should not affect key 2."""
        db = AsyncMock(spec=AsyncSession)
        # Key 1 limited to 1, key 2 unlimited
        model1 = MagicMock()
        model1.id = 1
        model1.platform = "openai"
        model1.key_name = "test1"
        model1.is_enabled = True
        model1.concurrency_limit = 1

        model2 = MagicMock()
        model2.id = 2
        model2.platform = "openai"
        model2.key_name = "test2"
        model2.is_enabled = True
        model2.concurrency_limit = None

        # scalar_one_or_none returns different models based on what's needed
        # For key_id=1, return model1; for key_id=2, return model2
        call_count = 0
        def side_effect():
            nonlocal call_count
            call_count += 1
            return model1 if call_count == 1 else model2

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model1, model2]
        mock_result.scalar_one_or_none.side_effect = side_effect
        db.execute.return_value = mock_result

        manager = ConcurrencyManager(db)

        # Key 1 exhausted (reserve 2 slots: 1st allowed, 2nd blocks)
        assert await manager.check_and_reserve(key_id=1, delta=1) is True  # 1st
        assert await manager.check_and_reserve(key_id=1, delta=1) is False  # 2nd blocked

        # Key 2 still allowed (unlimited)
        assert await manager.check_and_reserve(key_id=2, delta=1) is True

    @pytest.mark.asyncio
    async def test_refresh_all_loads_from_db(self):
        """refresh_all should load budgets from the DB."""
        db = AsyncMock(spec=AsyncSession)
        key1 = MagicMock()
        key1.id = 1
        key1.concurrency_limit = 3

        key2 = MagicMock()
        key2.id = 2
        key2.concurrency_limit = 7

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [key1, key2]
        db.execute.return_value = mock_result

        manager = ConcurrencyManager(db)
        await manager.refresh_all()

        assert 1 in manager._budgets
        assert 2 in manager._budgets
        assert manager._budgets[1].limit == 3
        assert manager._budgets[2].limit == 7
