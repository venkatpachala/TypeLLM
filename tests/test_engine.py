import asyncio
import pytest

from typellm.engine import EngineConfig, InferenceEngine
from typellm.fake_provider import FakeProvider


@pytest.mark.asyncio
async def test_bounded_concurrency():
    provider = FakeProvider(delay=0.02)

    engine = InferenceEngine(
        provider,
        EngineConfig(
            max_in_flight=2,
            admission_timeout=1,
        ),
    )

    results = await asyncio.gather(
        *(engine.generate(str(i)) for i in range(12))
    )

    assert len(results) == 12
    assert provider.peak_active == 2
    assert provider.active == 0