import math

from app.domain import ExperimentResult
from app.exceptions import InsufficientDataError


def evaluate_binary_experiment(
    control_conversions: int,
    control_visitors: int,
    treatment_conversions: int,
    treatment_visitors: int,
    confidence_z: float = 1.96,
) -> ExperimentResult:
    """Evaluate a two-arm conversion experiment using an unpooled Wald interval."""
    if min(control_visitors, treatment_visitors) < 30:
        raise InsufficientDataError("Each experiment arm requires at least 30 visitors")
    if not 0 <= control_conversions <= control_visitors:
        raise ValueError("control conversions must be between zero and visitors")
    if not 0 <= treatment_conversions <= treatment_visitors:
        raise ValueError("treatment conversions must be between zero and visitors")
    control_rate = control_conversions / control_visitors
    treatment_rate = treatment_conversions / treatment_visitors
    lift = treatment_rate - control_rate
    standard_error = math.sqrt(
        control_rate * (1 - control_rate) / control_visitors
        + treatment_rate * (1 - treatment_rate) / treatment_visitors
    )
    z_score = lift / standard_error if standard_error else 0.0
    return ExperimentResult(
        control_rate=control_rate,
        treatment_rate=treatment_rate,
        absolute_lift=lift,
        relative_lift=lift / control_rate if control_rate else math.inf,
        standard_error=standard_error,
        ci_low=lift - confidence_z * standard_error,
        ci_high=lift + confidence_z * standard_error,
        z_score=z_score,
        statistically_significant=abs(z_score) >= confidence_z,
    )
