
import asyncio

from typellm.usage import UsageCounter


async def main():
    counter = UsageCounter()

    await asyncio.gather(
        *(counter.record(100) for _ in range(100))
    )

    print("Expected tokens:", 10_000)
    print("Actual tokens:", counter.total)


if __name__ == "__main__":
    asyncio.run(main())
