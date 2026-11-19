
import asyncio

import pytest

from typellm.usage import UsageCounter


@pytest.mark.asyncio
async def test_concurrent_usage_is_correct():
    counter = UsageCounter()

    await asyncio.gather(
        *(counter.record(100) for _ in range(100))
    )

    assert counter.total == 10_000


@pytest.mark.asyncio
async def test_invalid_usage_is_rejected():
    counter = UsageCounter()

    with pytest.raises(ValueError):
        await counter.record(-5)

    assert counter.total == 0


@pytest.mark.asyncio
async def test_sequential_usage():
    counter = UsageCounter()

    await counter.record(50)
    await counter.record(100)

    assert counter.total == 150
