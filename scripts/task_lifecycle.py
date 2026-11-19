import asyncio

async def worker(name:str,delay:float,fail=False):
    print(f"{name}: started")

    try:
        await asyncio.sleep(delay)

        if fail:
            raise RuntimeError(f"{name} failed")

        print(f"{name}: completed")
        return name

    except asyncio.CancelledError:
        print(f"{name}: cancelled")
        raise

    finally:
        print(f"{name}: cleanup")

# gather() - Here even if one of the sibiling fails others continue

async def run_gather():
    print("\nRunning gather")

    tasks = [
        asyncio.create_task(worker("A", 1)),
        asyncio.create_task(worker("B", 0.2, fail=True)),
        asyncio.create_task(worker("C", 2)),
    ]

    try:
        await asyncio.gather(*tasks)

    except RuntimeError as error:
        print("Gather caught:", error)

    # Observe whether the other tasks keep running.
    await asyncio.sleep(2.5)


async def run_taskgroup():
    print("\nRunning taskgroup")

    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(worker("A", 1))
            group.create_task(worker("B", 0.2,fail=True))
            group.create_task(worker("C",2))

    except* RuntimeError as errors:
        print("TaskGroup caught:", errors)

# asyncio.run(run_taskgroup())

async def main():
    await run_gather()
    await run_taskgroup()


if __name__ == "__main__":
    asyncio.run(main())
