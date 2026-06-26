"""
Game clock — 1 real second equals 1 game minute.
Time stops while paused. Midnight callbacks fire once per game day.
"""


class TimeManager:
    SECONDS_PER_GAME_MINUTE: float = 1.0

    def __init__(self, start_day: int = 1, start_hour: int = 8, start_minute: int = 0) -> None:
        self.day = start_day
        self.hour = start_hour
        self.minute = start_minute

        self._accumulator: float = 0.0
        self._paused: bool = False
        self._midnight_callbacks: list = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_paused(self) -> bool:
        return self._paused

    def toggle_pause(self) -> None:
        self._paused = not self._paused

    def on_midnight(self, callback) -> None:
        """Register a zero-arg callable that fires at every game midnight."""
        self._midnight_callbacks.append(callback)

    def update(self, dt: float) -> None:
        """Advance the clock. dt is real elapsed time in seconds."""
        if self._paused:
            return

        self._accumulator += dt
        minutes_to_advance = int(self._accumulator / self.SECONDS_PER_GAME_MINUTE)
        if minutes_to_advance == 0:
            return

        self._accumulator -= minutes_to_advance * self.SECONDS_PER_GAME_MINUTE

        for _ in range(minutes_to_advance):
            self._tick_minute()

    def format_time(self) -> str:
        return f"Jour {self.day}   {self.hour:02d}:{self.minute:02d}"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _tick_minute(self) -> None:
        self.minute += 1
        if self.minute < 60:
            return

        self.minute = 0
        self.hour += 1
        if self.hour < 24:
            return

        self.hour = 0
        self.day += 1
        for cb in self._midnight_callbacks:
            cb()
