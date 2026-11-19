import asyncio

import pytest

from scripts.cancellation_lab import worker
from scripts.task_lifecycle import run_gather, run_taskgroup


@pytest.mark.asyncio
async def test_cancelled_waiter_preserves_capacity():
    semaphore = asyncio.Semaphore(1)
    hold = asyncio.Event()
    await semaphore.acquire()
    waiting = asyncio.create_task(worker("waiting", semaphore, hold))
    try:
        await asyncio.sleep(0)
        assert not waiting.done()
        waiting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiting
        assert semaphore.locked()
    finally:
        semaphore.release()
        waiting.cancel()
        await asyncio.gather(waiting, return_exceptions=True)

    hold.set()
    await asyncio.wait_for(worker("next", semaphore, hold), timeout=1.0)
    assert not semaphore.locked()


@pytest.mark.asyncio
async def test_cancelled_active_worker_releases_capacity():
    semaphore = asyncio.Semaphore(1)
    hold = asyncio.Event()
    active = asyncio.create_task(worker("active", semaphore, hold))
    try:
        await asyncio.sleep(0)
        assert semaphore.locked()
        active.cancel()
        with pytest.raises(asyncio.CancelledError):
            await active
        assert not semaphore.locked()
    finally:
        active.cancel()
        await asyncio.gather(active, return_exceptions=True)

    hold.set()
    await asyncio.wait_for(worker("next", semaphore, hold), timeout=1.0)


@pytest.mark.asyncio
async def test_gather_allows_siblings_to_complete(capsys):
    await run_gather()
    output = capsys.readouterr().out

    assert "Gather caught: B failed" in output
    assert "A: completed" in output
    assert "C: completed" in output
    assert all(f"{name}: cleanup" in output for name in "ABC")


@pytest.mark.asyncio
async def test_taskgroup_cancels_siblings_and_cleans_up(capsys):
    await run_taskgroup()
    output = capsys.readouterr().out

    assert "TaskGroup caught:" in output
    assert "A: cancelled" in output
    assert "C: cancelled" in output
    assert all(f"{name}: cleanup" in output for name in "ABC")
