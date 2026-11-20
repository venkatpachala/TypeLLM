"""Single-process, cancellation-aware, deadline-aware FIFO scheduler lab."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Status(str, Enum):
    QUEUED = 'queued'
    RUNNING = 'running'
    CANCELLING = 'cancelling'
    SUCCEEDED = 'succeeded'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'


@dataclass
class Job:
    request_id: str
    duration: float
    deadline: float
    worker_id: int
    predicted_start: float
    predicted_finish: float
    status: Status = Status.QUEUED


@dataclass(frozen=True)
class Decision:
    accepted: bool
    reason: str
    job: Job | None = None


class Scheduler:
    def __init__(self, worker_count: int, clock: Callable[[], float] = time.monotonic):
        if worker_count < 1:
            raise ValueError('worker_count must be positive')
        self._clock = clock
        self._lock = asyncio.Lock()
        self._waiting = [deque() for _ in range(worker_count)]
        self._running: list[str | None] = [None] * worker_count
        self._jobs: dict[str, Job] = {}

    # Recalculate reservations

    def _project(self, worker_id: int, now: float) -> float:
        running_id = self._running[worker_id]
        t = now
        if running_id is not None:
            t = max(t, self._jobs[running_id].predicted_finish)
        for request_id in self._waiting[worker_id]:
            job = self._jobs[request_id]
            job.predicted_start = t
            job.predicted_finish = t + job.duration
            t = job.predicted_finish
        return t

    async def submit(self, request_id: str, duration: float, deadline: float) -> Decision:
        if not request_id or duration <= 0:
            raise ValueError('request_id and positive duration required')
        async with self._lock:
            now = self._clock()
            if request_id in self._jobs:
                return Decision(False, 'duplicate_request_id')
            if deadline <= now:
                return Decision(False, 'deadline_elapsed')
            
            #Estimate all worker schedules

            times = [self._project(i, now) for i in range(len(self._waiting))]

            # Choose the earliest-available worker
            
            worker_id = min(range(len(times)), key=times.__getitem__)
            start = times[worker_id]

            # Compare predicted completion with deadline
            finish = start + duration
            if finish > deadline:
                return Decision(False, 'predicted_deadline_miss')
            
            job = Job(request_id, duration, deadline, worker_id, start, finish)
           
           # Reserve capacity

            self._jobs[request_id] = job
            self._waiting[worker_id].append(request_id)
            return Decision(True, 'admitted', job)

    # Cancellation-aware reservations

    async def cancel(self, request_id: str) -> Status | None:
        async with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return None
            if job.status == Status.QUEUED:
                self._waiting[job.worker_id].remove(request_id)
                job.status = Status.CANCELLED
                self._project(job.worker_id, self._clock())
            elif job.status == Status.RUNNING:
                # The executing coroutine must be cancelled separately.
                # Do not release its worker until it acknowledges cleanup.
                job.status = Status.CANCELLING
            return job.status

    # Assign work to a worker

    async def claim_next(self, worker_id: int) -> Job | None:
        async with self._lock:
            if not 0 <= worker_id < len(self._waiting):
                raise ValueError('unknown worker')
            if self._running[worker_id] is not None:
                return None
            now = self._clock()
            queue = self._waiting[worker_id]
            while queue:
                request_id = queue.popleft()
                job = self._jobs[request_id]
                if now + job.duration > job.deadline:
                    job.status = Status.EXPIRED
                    continue
                job.status = Status.RUNNING
                job.predicted_start = now
                job.predicted_finish = now + job.duration
                self._running[worker_id] = request_id
                self._project(worker_id, now)
                return job
            return None

    # Release worker ownership

    async def finish(self, request_id: str, *, cancelled: bool = False) -> Status:
        async with self._lock:
            job = self._jobs[request_id]
            if job.status not in (Status.RUNNING, Status.CANCELLING):
                raise ValueError('job is not running')
            if self._running[job.worker_id] != request_id:
                raise RuntimeError('worker ownership mismatch')
            job.status = Status.CANCELLED if cancelled or job.status == Status.CANCELLING else Status.SUCCEEDED
            self._running[job.worker_id] = None
            self._project(job.worker_id, self._clock())
            return job.status

    async def get(self, request_id: str) -> Job | None:
        async with self._lock:
            return self._jobs.get(request_id)

# Limitations 

# 1. Job failures aren't represented properly.

# We have SUCCEEDED but no FAILED state. The current finish() method defaults to success unless cancellation is indicated.

# If provider inference raises an ordinary error, the executor needs a way to record failure accurately.

# 2. Running-job estimates can become stale.

# _project() uses the running job's predicted_finish, but that timestamp is not continuously updated to reflect actual progress.

# If a provider takes longer than predicted, subsequent reservations may become unrealistic.

# 3. The scheduler doesn't enforce execution deadlines.

# It predicts completion when admitting and claiming jobs, but the actual executor must implement runtime timeout and cancellation behavior.

# 4. It doesn't wake workers automatically.

# There is no asyncio.Queue, Event, or Condition signaling mechanism connected to claim_next().

# A future executor needs a reliable way to know when jobs become available.

# 5. The returned Job is mutable.

# Even though the scheduler uses a lock internally, external code can receive a Job object and modify its fields directly.