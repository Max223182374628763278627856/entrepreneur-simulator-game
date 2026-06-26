"""
Dual-account economy system.

Personal account  — rent, food, leisure. Reaching zero means game over.
Business account  — client revenue, charges, stock, office. Negative balance
                    triggers daily overdraft fees (agios).
"""

from dataclasses import dataclass, field


DAILY_LIVING_COST: float = 30.0       # €/day deducted from personal at midnight
OVERDRAFT_FEE_RATE: float = 0.005     # 0.5 % of the negative balance
OVERDRAFT_FEE_MIN: float = 5.0        # minimum daily fee when in overdraft


@dataclass
class Notification:
    text: str
    positive: bool = True             # True → green, False → red/orange


class EconomyManager:
    def __init__(self, personal: float = 2_000.0, business: float = 5_000.0) -> None:
        self.personal: float = personal
        self.business: float = business
        self.game_over: bool = False

        self._pending: list[Notification] = []

    # ------------------------------------------------------------------
    # Midnight hook (called by TimeManager)
    # ------------------------------------------------------------------

    def on_midnight(self) -> None:
        self._deduct_personal(DAILY_LIVING_COST, "Vie quotidienne")

        if self.personal <= 0:
            self.game_over = True

        if self.business < 0:
            fee = max(abs(self.business) * OVERDRAFT_FEE_RATE, OVERDRAFT_FEE_MIN)
            self.business -= fee
            self._push(f"-{fee:.2f} € agios découvert", positive=False)

    # ------------------------------------------------------------------
    # Transfers
    # ------------------------------------------------------------------

    def transfer_salary(self, amount: float) -> bool:
        """Move money from business → personal. Returns False if insufficient funds."""
        if self.business < amount:
            return False
        self.business -= amount
        self.personal += amount
        self._push(f"+{amount:.0f} € virement perso ← pro", positive=True)
        return True

    # ------------------------------------------------------------------
    # General debit / credit helpers
    # ------------------------------------------------------------------

    def credit_business(self, amount: float, label: str = "Encaissement") -> None:
        self.business += amount
        self._push(f"+{amount:.0f} € {label}", positive=True)

    def debit_business(self, amount: float, label: str = "Dépense pro") -> None:
        """Overdraft is allowed — triggers agios at next midnight."""
        self.business -= amount
        self._push(f"-{amount:.0f} € {label}", positive=False)

    def debit_personal(self, amount: float, label: str = "Dépense perso") -> bool:
        if self.personal < amount:
            return False
        self.personal -= amount
        self._push(f"-{amount:.0f} € {label}", positive=False)
        return True

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

    def _deduct_personal(self, amount: float, label: str) -> None:
        self.personal -= amount
        self._push(f"-{amount:.0f} € {label}", positive=False)

    def _push(self, text: str, *, positive: bool) -> None:
        self._pending.append(Notification(text=text, positive=positive))
