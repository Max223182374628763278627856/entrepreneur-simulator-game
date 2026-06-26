"""
Business registration and mission dispatch for the Serrurier job.

States
------
UNREGISTERED  →  player presses [R] (costs 200 € perso)
REGISTERED    →  player can buy kit [K] (costs 500 € pro) and accept leads
"""

from dataclasses import dataclass
from enum import Enum, auto

from .jobs import Lead, LeadGenerator, MISSION_DURATION_MINUTES


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

REGISTRATION_COST: float = 200.0   # deducted from personal
KIT_COST:          float = 500.0   # deducted from business


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class BusinessState(Enum):
    UNREGISTERED = "Non enregistrée"
    ACTIVE       = "En activité"


class MissionState(Enum):
    IDLE           = auto()
    LEAD_INCOMING  = auto()


# ------------------------------------------------------------------
# Shared notification object (duck-type compatible with EconomyManager)
# ------------------------------------------------------------------

@dataclass
class Notification:
    text: str
    positive: bool = True


# ------------------------------------------------------------------
# BusinessManager
# ------------------------------------------------------------------

class BusinessManager:
    def __init__(self) -> None:
        self.state:         BusinessState = BusinessState.UNREGISTERED
        self.has_kit:       bool          = False
        self.mission_state: MissionState  = MissionState.IDLE
        self.current_lead:  "Lead | None" = None

        self._lead_gen    = LeadGenerator()
        self._pending:    list[Notification] = []

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------

    def update(self, dt: float, hour: int) -> None:
        """Poll for new leads. Only when active, kit owned, and currently idle."""
        if self.state != BusinessState.ACTIVE:
            return
        if not self.has_kit:
            return
        if self.mission_state != MissionState.IDLE:
            return

        lead = self._lead_gen.update(dt, hour)
        if lead:
            self.mission_state = MissionState.LEAD_INCOMING
            self.current_lead  = lead

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def register(self, eco_mgr) -> bool:
        """Register the business. Cost: 200 € from personal account."""
        if self.state == BusinessState.ACTIVE:
            self._push("Entreprise déjà enregistrée.", positive=False)
            return False
        if eco_mgr.personal < REGISTRATION_COST:
            self._push(f"Fonds perso insuffisants — il faut {REGISTRATION_COST:.0f} €.", positive=False)
            return False
        eco_mgr.personal -= REGISTRATION_COST
        self.state = BusinessState.ACTIVE
        self._push("Entreprise enregistrée ! Bienvenue entrepreneur.", positive=True)
        return True

    def buy_kit(self, eco_mgr) -> bool:
        """Purchase the lockpick kit. Cost: 500 € from business account."""
        if self.state != BusinessState.ACTIVE:
            self._push("Enregistrez d'abord votre entreprise [R].", positive=False)
            return False
        if self.has_kit:
            self._push("Vous possédez déjà le kit de crochetage.", positive=False)
            return False
        if eco_mgr.business < KIT_COST:
            self._push(f"Fonds Pro insuffisants — il faut {KIT_COST:.0f} €.", positive=False)
            return False
        eco_mgr.business -= KIT_COST
        self.has_kit = True
        self._push("Kit de crochetage acheté ! Vous êtes prêt à travailler.", positive=True)
        return True

    def accept_lead(self, eco_mgr, time_mgr) -> bool:
        """
        Resolve the current lead:
          - Deduct travel costs from business.
          - Advance game time by 2h (fires midnight callbacks if applicable).
          - Credit payment to business.
        """
        if self.mission_state != MissionState.LEAD_INCOMING:
            return False
        if not self.has_kit:
            self._push("Kit de crochetage requis — achetez-le avec [K].", positive=False)
            return False

        lead = self.current_lead
        eco_mgr.business -= lead.travel_cost
        time_mgr.advance_minutes(MISSION_DURATION_MINUTES)
        eco_mgr.business += lead.payment

        self._push(
            f"Mission terminée !  +{lead.payment:.0f} €  −{lead.travel_cost:.2f} € carburant"
            f"  =  {lead.net_gain:.2f} € net",
            positive=True,
        )

        self._close_lead()
        return True

    def refuse_lead(self) -> None:
        if self.mission_state != MissionState.LEAD_INCOMING:
            return
        self._push("Mission refusée.")
        self._close_lead()

    # ------------------------------------------------------------------
    # Notification queue
    # ------------------------------------------------------------------

    def pop_notifications(self) -> list[Notification]:
        out = self._pending[:]
        self._pending.clear()
        return out

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _close_lead(self) -> None:
        self.mission_state = MissionState.IDLE
        self.current_lead  = None

    def _push(self, text: str, positive: bool = True) -> None:
        self._pending.append(Notification(text=text, positive=positive))
