
import asyncio
import time

from typellm.engine import InferenceEngine, EngineConfig
from typellm.fake_provider import FakeProvider


async def run_benchmark(limit: int):
    provider = FakeProvider(delay=0.2)

    engine = InferenceEngine(
        provider=provider,
        config=EngineConfig(
            max_in_flight=limit,
            admission_timeout=10.0,
            execution_timeout=5.0,
        ),
    )

    start = time.perf_counter()

    results = await asyncio.gather(
        *(
            engine.generate(f"Prompt {i}")
            for i in range(10)
        )
    )

    elapsed = time.perf_counter() - start

    print(f"\nConcurrency limit: {limit}")
    print(f"Completed requests: {len(results)}")
    print(f"Time taken: {elapsed:.3f} seconds")
    print(f"Peak active calls: {provider.peak_active}")


async def main():
    for limit in [1, 2, 5, 10]:
        await run_benchmark(limit)


if __name__ == "__main__":
    asyncio.run(main())
