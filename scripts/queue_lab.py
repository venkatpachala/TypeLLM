import asyncio

async def worker(
        name:str,
        queue:asyncio.Queue[str],
):
    while True:
        job=await queue.get() # when the queue is empty the worker
        # suspends at await
        try:
            print(f"{name}: processing {job}")
            await asyncio.sleep(0.5)

        finally:
            queue.task_done()

async def main():
    queue=asyncio.Queue[str](maxsize=3)

    workers=[
        asyncio.create_task(worker("Worker-A", queue)),
        asyncio.create_task(worker("Worker-B", queue)),
    ]

    try:
        for i in range(10):
            job=f"Request-{i}"

            try:
                await asyncio.wait_for(
                    queue.put(job),
                    timeout=0.1,
                )

                print(f"Accepted: {job} ")

            except TimeoutError:
                print(f"Rejected: {job} (queue full)")

        await queue.join()
    finally:
        for task in workers:
            task.cancel()

        await asyncio.gather(
            *workers,
            return_exceptions=True
        )

if __name__=="__main__":
    asyncio.run(main())
