
import asyncio

import pytest


@pytest.mark.asyncio
async def test_bounded_queue_rejects_overload():
    queue = asyncio.Queue(maxsize=1)

    await queue.put("request-A")

    assert queue.full()

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(
            queue.put("request-B"),
            timeout=0.01,
        )

    assert queue.qsize() == 1

    item = await queue.get()

    assert item == "request-A"

    queue.task_done()
    await queue.join()


@pytest.mark.asyncio
async def test_cancelled_queue_waiter_does_not_insert():
    queue = asyncio.Queue(maxsize=1)

    await queue.put("request-A")

    waiting = asyncio.create_task(
        queue.put("request-B")
    )

    await asyncio.sleep(0)

    assert not waiting.done()

    waiting.cancel()

    with pytest.raises(asyncio.CancelledError):
        await waiting

    assert queue.qsize() == 1

    item = await queue.get()
    assert item == "request-A"

    queue.task_done()
    await queue.join()

    assert queue.empty()
