
import asyncio
import pytest

from typellm.admission_v3 import AdmissionController

@pytest.mark.asyncio
async def test_concurrent_admission():
    controller = AdmissionController(worker_count=2)

    decisions = await asyncio.gather(
        *(
            controller.admit(
                arrival_time=0.0,
                service_time=2.0,
                deadline=3.0,
            )
            for _ in range(10)
        )
    )

    accepted = [d for d in decisions if d.accepted]
    rejected = [d for d in decisions if not d.accepted]

    assert len(accepted) == 2
    assert len(rejected) == 8
    assert {d.worker_id for d in accepted} == {0, 1}
    assert all(d.worker_id is None for d in rejected)
    assert all(d.estimated_completion == 4.0 for d in rejected)

    assert all(
        d.estimated_completion == 2.0
        for d in accepted
    )

@pytest.mark.asyncio
async def test_reserves_successive_batches_until_deadline():
    controller = AdmissionController(worker_count=2)

    decisions = await asyncio.gather(
        *(controller.admit(0.0, 2.0, 4.0) for _ in range(5))
    )

    assert [d.accepted for d in decisions] == [True, True, True, True, False]
    assert [d.estimated_completion for d in decisions] == [2.0, 2.0, 4.0, 4.0, 6.0]


@pytest.mark.asyncio
async def test_rejection_does_not_reserve_worker():
    controller = AdmissionController(worker_count=1)

    rejected = await controller.admit(0.0, 5.0, 4.0)
    accepted = await controller.admit(0.0, 2.0, 2.0)

    assert rejected.accepted is False
    assert rejected.worker_id is None
    assert accepted.accepted is True
    assert accepted.estimated_completion == 2.0


@pytest.mark.asyncio
async def test_starts_at_arrival_when_worker_has_been_idle():
    controller = AdmissionController(worker_count=1)
    await controller.admit(0.0, 2.0, 2.0)

    decision = await controller.admit(10.0, 2.0, 12.0)

    assert decision.accepted is True
    assert decision.estimated_completion == 12.0


@pytest.mark.asyncio
async def test_deadline_is_absolute():
    controller = AdmissionController(worker_count=1)

    decision = await controller.admit(10.0, 2.0, 11.0)

    assert decision.accepted is False
    assert decision.estimated_completion == 12.0


@pytest.mark.parametrize("worker_count", [0, -1])
def test_rejects_invalid_worker_count(worker_count):
    with pytest.raises(ValueError):
        AdmissionController(worker_count=worker_count)


@pytest.mark.asyncio
@pytest.mark.parametrize("service_time", [0.0, -1.0])
async def test_invalid_service_time_does_not_reserve_capacity(service_time):
    controller = AdmissionController(worker_count=1)

    with pytest.raises(ValueError):
        await controller.admit(0.0, service_time, 2.0)

    decision = await controller.admit(0.0, 2.0, 2.0)
    assert decision.accepted is True
    assert decision.estimated_completion == 2.0
