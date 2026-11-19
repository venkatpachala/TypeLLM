from dataclasses import dataclass

### Capacity Estimation

@dataclass(frozen=True)

# Stores the result

class AdmissionDecision:
    accepted: bool
    estimated_completion: float
    reason: str

# Makes the decision

class AdmissionController:
    """Estimate completion in full batches, counting unfinished jobs as pending."""

    def __init__(
            self, workers:int,service_time:float,
    ):
        if workers<=0 or service_time<=0:
            raise ValueError("Invalid Configuration")
        self.workers=workers
        self.service_time=service_time

    def evaluate(
            self, pending_jobs:int,deadline_seconds:float,
    )-> AdmissionDecision:
        if pending_jobs<0:
            raise ValueError("Pending_jobs cannot be negative")
        if deadline_seconds<=0:
            return AdmissionDecision(
                False,0.0,"Deadline expired"
            )

        batches_ahead=pending_jobs//self.workers

        estimated_wait=(
            batches_ahead*self.service_time
        )

        estimated_completion=(
            estimated_wait+self.service_time
        )

        accepted=estimated_completion<=deadline_seconds

        return AdmissionDecision(
            accepted=accepted,
            estimated_completion=estimated_completion,
            reason=(
                "Within estimated deadline"
                if accepted
                else "Predicted deadline miss"
            ),
        )