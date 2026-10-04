"""SEE alert schema: one alert per detected suspicious pattern."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json


@dataclass(frozen=True)
class Alert:
    """A single suspicious-activity alert.

    ``alert_id`` is deterministically derived from (rule_id, account, evidence)
    so the same inputs always produce the same id.  ``score`` is in [0, 100]
    where higher means more suspicious; it is a heuristic lead, never proof.
    """

    alert_id: str
    rule_id: str
    rule_name: str
    account: str
    score: int
    window_start: str  # ISO timestamp
    window_end: str    # ISO timestamp
    evidence_txn_ids: tuple[str, ...]
    explanation: str
    disclaimer: str = (
        "This alert is an investigative lead only, not proof of wrongdoing."
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["evidence_txn_ids"] = list(self.evidence_txn_ids)
        return d

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, **kwargs)


# Column order when converting a list[Alert] to a DataFrame.
ALERT_COLUMNS: list[str] = [
    "alert_id", "rule_id", "rule_name", "account", "score",
    "window_start", "window_end", "evidence_txn_ids", "explanation", "disclaimer",
]
