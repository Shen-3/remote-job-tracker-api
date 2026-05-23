from __future__ import annotations

from jobtracker.schemas import Status


ALLOWED_STATUS_TRANSITIONS: dict[Status, set[Status]] = {
    Status.planned: {Status.applied},
    Status.applied: {Status.recruiter_reply, Status.rejected},
    Status.recruiter_reply: {Status.test_task, Status.interview, Status.rejected},
    Status.test_task: {Status.interview, Status.rejected},
    Status.interview: {Status.offer, Status.rejected},
}


def is_valid_status_transition(current: Status, target: Status) -> bool:
    if current == target:
        return True
    return target in ALLOWED_STATUS_TRANSITIONS.get(current, set())


def status_transition_error(current: Status, target: Status) -> str:
    return f"invalid status transition: {current.value} -> {target.value}"
