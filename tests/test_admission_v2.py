import pytest

from typellm.admission_v2 import StateAwareAdmissionController


def test_rejects_busy_workers():
    controller = StateAwareAdmissionController()

    decision = controller.evaluate(
        worker_available_in=[1, 1, 1, 1, 1],
        estimated_service_time=2,
        deadline_seconds=2.5,
    )

    assert decision.accepted is False
    assert decision.estimated_completion == 3.0


def test_accepts_available_worker():
    controller = StateAwareAdmissionController()

    decision = controller.evaluate(
        worker_available_in=[0, 1, 1, 1, 1],
        estimated_service_time=2,
        deadline_seconds=2.5,
    )

    assert decision.accepted is True
    assert decision.estimated_completion == 2.0

def test_uses_earliest_worker_without_mutating_snapshot():
    available = [5.0, 1.0, 3.0]
    decision = StateAwareAdmissionController().evaluate(available, 2.0, 3.0)

    assert decision.accepted is True
    assert decision.estimated_start == 1.0
    assert decision.estimated_completion == 3.0
    assert available == [5.0, 1.0, 3.0]


def test_rejects_service_that_exceeds_deadline_on_idle_worker():
    decision = StateAwareAdmissionController().evaluate([0.0], 2.0, 1.0)

    assert decision.accepted is False
    assert decision.estimated_completion == 2.0


@pytest.mark.parametrize("available,service", [([], 1.0), ([-1.0], 1.0), ([0.0], 0.0), ([0.0], -1.0)])
def test_rejects_invalid_inputs(available, service):
    with pytest.raises(ValueError):
        StateAwareAdmissionController().evaluate(available, service, 3.0)


@pytest.mark.parametrize("deadline", [0.0, -1.0])
def test_rejects_expired_deadline(deadline):
    decision = StateAwareAdmissionController().evaluate([0.0], 1.0, deadline)

    assert decision.accepted is False
    assert decision.reason == "Deadline expired"
