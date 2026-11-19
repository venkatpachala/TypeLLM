
import asyncio


async def worker(
    name: str,
    semaphore: asyncio.Semaphore,
    hold: asyncio.Event,
):
    acquired = False

    try:
        print(f"{name}: waiting for capacity")

        await semaphore.acquire()
        acquired = True

        print(f"{name}: acquired permit")

        await hold.wait()

        print(f"{name}: finished")

    except asyncio.CancelledError:
        print(f"{name}: cancelled")
        raise

    finally:
        if acquired:
            semaphore.release()
            print(f"{name}: released permit")


async def main():
    semaphore = asyncio.Semaphore(1)
    hold = asyncio.Event()

    task_a = asyncio.create_task(
        worker("A", semaphore, hold)
    )

    await asyncio.sleep(0.05)

    task_b = asyncio.create_task(
        worker("B", semaphore, hold)
    )

    await asyncio.sleep(0.05)

    print("\nCancelling B while it waits...")
    task_b.cancel()

    try:
        await task_b
    except asyncio.CancelledError:
        pass

    print("\nReleasing A...")
    hold.set()

    await task_a

    print("\nStarting C...")
    task_c = asyncio.create_task(
        worker("C", semaphore, hold)
    )

    await task_c


if __name__ == "__main__":
    asyncio.run(main())
