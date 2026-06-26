"""
Business registration, inventory, and mission dispatch for the Serrurier job.

States
------
UNREGISTERED  →  [R] register (200 € perso)
ACTIVE        →  can buy kit [K], stock [B], office [L], accept leads [A]

Stock
-----
Each completed mission consumes 1 barillet.
Without office: max 5 barillets. With office: unlimited.

Office / Atelier
----------------
Unlocks unlimited stock. Rent = 500 €/month (every 30 game days), charged to Pro.
"""

from dataclasses import dataclass
from enum import Enum, auto

from .jobs import Lead, LeadGenerator, MISSION_DURATION_MINUTES


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

REGISTRATION_COST:       float = 200.0
KIT_COST:                float = 500.0
BARILLET_COST:           float = 30.0
BARILLET_BUY_QTY:        int   = 5       # units bought per [B] press
MAX_STOCK_WITHOUT_OFFICE: int  = 5
OFFICE_RENT:             float = 500.0
RENT_PERIOD_DAYS:        int   = 30


# ------------------------------------------------------------------
# Enums & dataclasses
# ------------------------------------------------------------------

class BusinessState(Enum):
    UNREGISTERED = "Non enregistrée"
    ACTIVE       = "En activité"


class MissionState(Enum):
    IDLE           = auto()
    LEAD_INCOMING  = auto()


@dataclass
class Notification:
    text: str
    positive: bool = True


# ------------------------------------------------------------------
# BusinessManager
# ------------------------------------------------------------------

class BusinessManager:
    def __init__(self) -> None:
        self.state:            BusinessState = BusinessState.UNREGISTERED
        self.has_kit:          bool          = False
        self.stock_barillets:  int           = 0
        self.has_office:       bool          = False
        self.mission_state:    MissionState  = MissionState.IDLE
        self.current_lead:     "Lead | None" = None

        self._lead_gen         = LeadGenerator()
        self._days_since_rent: int           = 0
        self._pending:         list[Notification] = []

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def max_stock(self) -> int:
        return 999 if self.has_office else MAX_STOCK_WITHOUT_OFFICE

    @property
    def stock_low(self) -> bool:
        return 0 < self.stock_barillets <= 2

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------

    def update(self, dt: float, hour: int, lead_rate: float = 1.0) -> None:
        """Poll for new leads.  lead_rate comes from MarketingManager."""
        if self.state != BusinessState.ACTIVE:
            return
        if not self.has_kit:
            return
        if self.mission_state != MissionState.IDLE:
            return

        lead = self._lead_gen.update(dt, hour, lead_rate)
        if lead:
            self.mission_state = MissionState.LEAD_INCOMING
            self.current_lead  = lead

    # ------------------------------------------------------------------
    # Midnight hook
    # ------------------------------------------------------------------

    def on_midnight(self, eco_mgr) -> None:
        """Charge monthly office rent if applicable."""
        if not self.has_office:
            return
        self._days_since_rent += 1
        if self._days_since_rent >= RENT_PERIOD_DAYS:
            eco_mgr.business -= OFFICE_RENT
            self._days_since_rent = 0
            self._push(f"-{OFFICE_RENT:.0f} € loyer atelier (mensuel)", positive=False)

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def register(self, eco_mgr) -> bool:
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

    def buy_barillets(self, eco_mgr) -> bool:
        """Buy BARILLET_BUY_QTY barillets at once."""
        if self.state != BusinessState.ACTIVE:
            self._push("Enregistrez d'abord votre entreprise [R].", positive=False)
            return False
        qty  = BARILLET_BUY_QTY
        cost = qty * BARILLET_COST
        if self.stock_barillets + qty > self.max_stock:
            space = self.max_stock - self.stock_barillets
            if space <= 0:
                self._push(f"Stock max atteint ({self.max_stock} unités max sans atelier).", positive=False)
                return False
            qty  = space
            cost = qty * BARILLET_COST
        if eco_mgr.business < cost:
            self._push(f"Fonds Pro insuffisants — il faut {cost:.0f} € pour {qty} barillet(s).", positive=False)
            return False
        eco_mgr.business      -= cost
        self.stock_barillets  += qty
        self._push(f"+{qty} barillet(s) achetés ({cost:.0f} €)  |  Stock : {self.stock_barillets}", positive=True)
        return True

    def rent_office(self, eco_mgr) -> bool:
        if self.has_office:
            self._push("Vous louez déjà un atelier.", positive=False)
            return False
        if eco_mgr.business < OFFICE_RENT:
            self._push(f"Fonds Pro insuffisants — premier loyer : {OFFICE_RENT:.0f} €.", positive=False)
            return False
        eco_mgr.business  -= OFFICE_RENT
        self.has_office    = True
        self._days_since_rent = 0
        self._push("Atelier loué ! Stock illimité. Prochain loyer dans 30 jours.", positive=True)
        return True

    def accept_lead(self, eco_mgr, time_mgr) -> bool:
        if self.mission_state != MissionState.LEAD_INCOMING:
            return False
        if not self.has_kit:
            self._push("Kit de crochetage requis — achetez-le avec [K].", positive=False)
            return False
        if self.stock_barillets <= 0:
            self._push("Stock de barillets épuisé — commandez avec [B].", positive=False)
            return False

        lead = self.current_lead
        eco_mgr.business     -= lead.travel_cost
        self.stock_barillets -= 1
        time_mgr.advance_minutes(MISSION_DURATION_MINUTES)
        eco_mgr.business     += lead.payment

        self._push(
            f"Mission OK ! +{lead.payment:.0f} € − {lead.travel_cost:.2f} € carburant"
            f" = {lead.net_gain:.2f} € net  |  Stock : {self.stock_barillets}",
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
