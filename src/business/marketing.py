"""
Marketing / lead-acquisition manager.

Daily budget controls how often job leads appear:

  0 €/day  →  rate 0.0  →  no leads at all
 10 €/day  →  rate 0.2  →  rare  (5× slower than baseline)
 50 €/day  →  rate 1.0  →  normal frequency  (baseline)
100 €/day  →  rate 2.0  →  double frequency

The daily budget is deducted from the business account at each midnight.
"""

from dataclasses import dataclass

BUDGET_STEP:         float = 10.0
MAX_BUDGET:          float = 100.0
_NORMAL_RATE_BUDGET: float = 50.0   # budget at which lead_rate == 1.0


@dataclass
class Notification:
    text: str
    positive: bool = True


class MarketingManager:
    def __init__(self, daily_budget: float = 0.0) -> None:
        self.daily_budget: float = daily_budget

    # ------------------------------------------------------------------
    # Read-only computed properties
    # ------------------------------------------------------------------

    @property
    def lead_rate(self) -> float:
        """Multiplier passed to LeadGenerator: 0 = no leads, 1 = normal, 2 = fast."""
        return self.daily_budget / _NORMAL_RATE_BUDGET

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def increase(self) -> None:
        self.daily_budget = min(self.daily_budget + BUDGET_STEP, MAX_BUDGET)

    def decrease(self) -> None:
        self.daily_budget = max(self.daily_budget - BUDGET_STEP, 0.0)

    # ------------------------------------------------------------------
    # Midnight hook
    # ------------------------------------------------------------------

    def on_midnight(self, eco_mgr) -> list[Notification]:
        """Deduct daily marketing budget from business account."""
        if self.daily_budget <= 0:
            return []
        eco_mgr.business -= self.daily_budget
        return [Notification(text=f"-{self.daily_budget:.0f} € pub/marketing", positive=False)]
