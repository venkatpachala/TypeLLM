
import asyncio
import time


async def nonblocking_request(i):
    await asyncio.sleep(1)
    print(f"Completed request {i}")


async def blocking_request(i):
    time.sleep(1)
    print(f"Completed request {i}")


async def main():
    start = time.perf_counter()

    await asyncio.gather(
        *(nonblocking_request(i) for i in range(5))
    )

    print("Non-blocking:", time.perf_counter() - start)

    start = time.perf_counter()

    await asyncio.gather(
        *(blocking_request(i) for i in range(5))
    )

    print("Blocking:", time.perf_counter() - start)


asyncio.run(main())
