import asyncio
from dataclasses import dataclass

@dataclass(frozen=True)
class AdmissionDecision:
    accepted:bool
    worker_id:int|None
    estimated_completion:float

class AdmissionController:
    """Reserve estimated worker time atomically within one event loop.

    Arrival, worker availability, and deadline use the same absolute time base.
    Reservations are predictions and are not reconciled with actual execution.
    """

    def __init__(self,worker_count:int):
        if worker_count<1:
            raise ValueError("Need at least one worker")

        self._available_at=[0.0]*worker_count
        self._lock=asyncio.Lock()

    async def admit(
            self,
            arrival_time:float,
            service_time:float,
            deadline:float,
    )-> AdmissionDecision:
        if service_time<=0:
            raise ValueError("Invalid service time")
        async with self._lock:

            # 1. Read the latest scheduling state

            worker_id=min(
                range(len(self._available_at)),
                key=lambda i:self._available_at[i],
            )

            # 2. Predict completion time

            start=max(
                arrival_time,
                self._available_at[worker_id],
            )
            completion=start+service_time

            # 3. Reject or reserve

            if completion > deadline:
                return AdmissionDecision(
                    accepted=False,
                    worker_id=None,
                    estimated_completion=completion,
                )

            self._available_at[worker_id] = completion

            return AdmissionDecision(
                accepted=True,
                worker_id=worker_id,
                estimated_completion=completion,
            )