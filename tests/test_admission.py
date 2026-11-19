import pytest

from typellm.admission import AdmissionController


def test_rejects_when_completion_exceeds_deadline():
    controller = AdmissionController(workers=2, service_time=2.0)

    decision = controller.evaluate(pending_jobs=2, deadline_seconds=3.0)

    assert decision.accepted is False
    assert decision.estimated_completion == 4.0


def test_rejects_when_service_alone_exceeds_deadline():
    controller = AdmissionController(workers=2, service_time=2.0)

    decision = controller.evaluate(pending_jobs=0, deadline_seconds=1.0)

    assert decision.accepted is False
    assert decision.estimated_completion == 2.0


def test_accepts_completion_exactly_at_deadline():
    controller = AdmissionController(workers=2, service_time=2.0)

    decision = controller.evaluate(pending_jobs=2, deadline_seconds=4.0)

    assert decision.accepted is True
    assert decision.estimated_completion == 4.0


def test_uses_free_capacity_before_adding_a_batch():
    controller = AdmissionController(workers=2, service_time=2.0)

    decision = controller.evaluate(pending_jobs=1, deadline_seconds=2.0)

    assert decision.accepted is True
    assert decision.estimated_completion == 2.0


@pytest.mark.parametrize("workers,service_time", [(0, 1), (-1, 1), (1, 0), (1, -1)])
def test_rejects_invalid_configuration(workers, service_time):
    with pytest.raises(ValueError):
        AdmissionController(workers=workers, service_time=service_time)


def test_rejects_negative_pending_jobs():
    controller = AdmissionController(workers=1, service_time=1.0)

    with pytest.raises(ValueError):
        controller.evaluate(pending_jobs=-1, deadline_seconds=1.0)


@pytest.mark.parametrize("deadline", [0.0, -1.0])
def test_rejects_expired_deadline(deadline):
    controller = AdmissionController(workers=1, service_time=1.0)

    decision = controller.evaluate(pending_jobs=0, deadline_seconds=deadline)

    assert decision.accepted is False
    assert decision.reason == "Deadline expired"
