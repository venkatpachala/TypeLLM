from dataclasses import dataclass

@dataclass(frozen=True)
class AdmissionDecision:
    accepted:bool
    estimated_start:float
    estimated_completion:float
    reason:str

class StateAwareAdmissionController:
    """Evaluate a snapshot of worker availability expressed in seconds from now."""

    def evaluate(
            self,worker_available_in:list[float],
            estimated_service_time:float,
            deadline_seconds:float
    )-> AdmissionDecision:

        if not worker_available_in:
            raise ValueError("At least one worker required")
        if any(t<0 for t in worker_available_in):
            raise ValueError("Negative availability time")

        if estimated_service_time<=0:
            raise ValueError("Invalid service time")
        if deadline_seconds<=0:
            return AdmissionDecision(
                False,0.0,0.0,"Deadline expired"
            )

        # Find the earliest available worker
        earliest=min(worker_available_in)

        estimated_completion=(
            earliest+estimated_service_time
        )

        accepted=estimated_completion<=deadline_seconds

        return AdmissionDecision(
            accepted=accepted,
            estimated_start=earliest,
            estimated_completion=estimated_completion,
            reason=(
                "Within estimated deadline"
                if accepted
                else "Predicted deadline miss"
            ),
        )