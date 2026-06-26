"""
Locksmith job system.

Leads are generated randomly during business hours (08:00–20:00).
Each lead has a description, distance, urgency tier, and payment.
Travel cost = 0.50 €/km, deducted from business account on acceptance.

The lead_rate multiplier (supplied by MarketingManager) scales cooldown speed:
  0.0  → no leads       |  1.0 → normal  |  2.0 → twice as fast
"""

import random
from dataclasses import dataclass
from enum import Enum


TRAVEL_COST_PER_KM:    float = 0.50
MISSION_DURATION_MINUTES: int = 120  # 2 game hours


class Urgency(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# (urgency, label, weight, dist_range_km, pay_range_€)
_LEAD_TABLE = [
    (Urgency.LOW,    "Serrure grippée",         0.35, (5.0, 20.0), (80,  135)),
    (Urgency.MEDIUM, "Porte claquée",            0.45, (2.0, 15.0), (120, 200)),
    (Urgency.HIGH,   "Urgence : enfant enfermé", 0.20, (1.0,  8.0), (200, 360)),
]


@dataclass
class Lead:
    description: str
    urgency: Urgency
    distance: float   # km
    payment: float    # €

    @property
    def travel_cost(self) -> float:
        return round(self.distance * TRAVEL_COST_PER_KM, 2)

    @property
    def net_gain(self) -> float:
        return round(self.payment - self.travel_cost, 2)


def _pick_lead() -> Lead:
    r = random.random()
    cumulative = 0.0
    for urgency, label, weight, dist_range, pay_range in _LEAD_TABLE:
        cumulative += weight
        if r <= cumulative:
            dist    = round(random.uniform(*dist_range), 1)
            payment = float(random.randint(*pay_range))
            return Lead(description=label, urgency=urgency, distance=dist, payment=payment)
    dist = round(random.uniform(2.0, 15.0), 1)
    return Lead(description="Porte claquée", urgency=Urgency.MEDIUM,
                distance=dist, payment=float(random.randint(120, 200)))


class LeadGenerator:
    """
    Emits one Lead per cooldown period during business hours.

    The cooldown ticks down at a speed proportional to `rate`:
      rate=0  → frozen, never fires
      rate=1  → normal (90–240 real-second cooldown)
      rate=2  → twice as fast (effectively 45–120 s cooldown)
    """

    _INITIAL_COOLDOWN: float = 25.0
    _MIN_COOLDOWN:     float = 90.0
    _MAX_COOLDOWN:     float = 240.0

    def __init__(self) -> None:
        self._cooldown: float = self._INITIAL_COOLDOWN

    def update(self, dt: float, hour: int, rate: float = 1.0) -> "Lead | None":
        """Return a Lead when one fires, else None."""
        if rate <= 0.0:
            return None
        if not (8 <= hour < 20):
            return None

        self._cooldown -= dt * rate
        if self._cooldown > 0:
            return None

        self._cooldown = random.uniform(self._MIN_COOLDOWN, self._MAX_COOLDOWN)
        return _pick_lead()
