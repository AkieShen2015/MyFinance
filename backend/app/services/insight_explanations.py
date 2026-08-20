from typing import Protocol

from app.schemas.finance import AiInsightPayloadRead


class InsightExplanationProvider(Protocol):
    """Boundary for an optional provider that only receives aggregated analytics."""

    def explain(self, payload: AiInsightPayloadRead) -> str: ...


class DeterministicInsightExplanationProvider:
    def explain(self, payload: AiInsightPayloadRead) -> str:
        direction = "increased" if payload.expense_change_amount > 0 else "decreased"
        amount = abs(payload.expense_change_amount)
        return (
            f"Expenses {direction} by ${amount:,.2f} compared with the prior period. "
            f"There are {payload.anomaly_count} unusual transactions to review."
        )
