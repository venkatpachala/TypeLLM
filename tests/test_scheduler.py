import asyncio
import pytest
from typellm.scheduler import Scheduler, Status

class Clock:
    def __init__(self): self.value = 0.0
    def __call__(self): return self.value

@pytest.mark.asyncio
async def test_twelve_simultaneous_submissions_admit_only_six():
    clock = Clock()
    s = Scheduler(3, clock)

    decisions = await asyncio.gather(
        *(s.submit(f'r{i}', 2, 5) for i in range(12))
    )

    assert sum(d.accepted for d in decisions) == 6
    assert sum(not d.accepted for d in decisions) == 6

@pytest.mark.asyncio
async def test_cancel_compacts_fifo_prediction():
    clock = Clock()
    s = Scheduler(1, clock)
    await s.submit('A', 2, 10)
    await s.submit('B', 2, 10)
    await s.submit('C', 2, 10)
    assert (await s.get('C')).predicted_finish == 6
    assert (await s.claim_next(0)).request_id == 'A'
    clock.value = 1
    assert await s.cancel('B') == Status.CANCELLED
    assert (await s.get('C')).predicted_finish == 4

@pytest.mark.asyncio
async def test_overrun_expires_queued_job_on_dispatch():
    clock = Clock()
    s = Scheduler(1, clock)
    await s.submit('A', 2, 10)
    await s.submit('C', 2, 5)
    assert (await s.claim_next(0)).request_id == 'A'
    clock.value = 3.5
    await s.finish('A')
    assert await s.claim_next(0) is None
    assert (await s.get('C')).status == Status.EXPIRED

@pytest.mark.asyncio
async def test_running_cancellation_keeps_worker_until_cleanup():
    clock = Clock()
    s = Scheduler(1, clock)
    await s.submit('A', 2, 10)
    await s.submit('B', 2, 10)
    await s.claim_next(0)
    assert await s.cancel('A') == Status.CANCELLING
    assert await s.claim_next(0) is None
    assert await s.finish('A', cancelled=True) == Status.CANCELLED
    assert (await s.claim_next(0)).request_id == 'B'

@pytest.mark.asyncio
async def test_duplicate_request_does_not_reserve_twice():
    s = Scheduler(1, Clock())
    assert (await s.submit('A', 2, 3)).accepted
    assert (await s.submit('A', 2, 3)).reason == 'duplicate_request_id'

@pytest.mark.asyncio
async def test_late_request_not_admitted():
    s = Scheduler(1, Clock())
    decision = await s.submit('A', 2, 1)
    assert decision.reason == 'predicted_deadline_miss'
