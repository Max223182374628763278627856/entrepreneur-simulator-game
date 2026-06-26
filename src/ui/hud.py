"""
Head-Up Display — top bar showing time and dual account balances.
Notification toasts appear below the bar and fade out over time.
"""

import pygame

# Colours
_BG         = (18, 18, 30)
_SEPARATOR  = (55, 55, 75)
_NEUTRAL    = (200, 200, 215)
_GREEN      = (72, 214, 110)
_RED        = (220, 75, 75)
_AMBER      = (220, 175, 50)
_DIM        = (75, 75, 95)

BAR_HEIGHT  = 52
_TOAST_TTL  = 3.5   # seconds a toast stays visible


class HUD:
    def __init__(self, screen_width: int) -> None:
        self.width = screen_width
        self._font      = pygame.font.SysFont("consolas", 22, bold=True)
        self._hint_font = pygame.font.SysFont("consolas", 14)
        self._toasts: list[dict] = []   # [{text, color, ttl}]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push_toast(self, text: str, positive: bool = True) -> None:
        self._toasts.append({
            "text":  text,
            "color": _GREEN if positive else _RED,
            "ttl":   _TOAST_TTL,
        })

    def update(self, dt: float) -> None:
        for t in self._toasts:
            t["ttl"] -= dt
        self._toasts = [t for t in self._toasts if t["ttl"] > 0]

    def draw(self, surface: pygame.Surface, time_mgr, eco_mgr) -> None:
        self._draw_bar(surface, time_mgr, eco_mgr)
        self._draw_toasts(surface)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _draw_bar(self, surface, time_mgr, eco_mgr) -> None:
        pygame.draw.rect(surface, _BG, (0, 0, self.width, BAR_HEIGHT))
        pygame.draw.line(surface, _SEPARATOR, (0, BAR_HEIGHT), (self.width, BAR_HEIGHT), 1)

        y = BAR_HEIGHT // 2 - self._font.get_height() // 2

        # -- Time (left) ------------------------------------------------
        time_color = _AMBER if time_mgr.is_paused else _NEUTRAL
        label = time_mgr.format_time()
        if time_mgr.is_paused:
            label += "  ⏸ PAUSE"
        self._blit(surface, self._font, label, time_color, x=20, y=y)

        # -- Personal balance (centre-left) -----------------------------
        perso_color = _RED if eco_mgr.personal < 300 else _GREEN
        perso_label = f"Perso : {eco_mgr.personal:>9,.0f} €".replace(",", " ")
        self._blit(surface, self._font, perso_label, perso_color,
                   x=self.width // 2 - 260, y=y)

        # -- Separator dot ----------------------------------------------
        pygame.draw.circle(surface, _SEPARATOR, (self.width // 2, BAR_HEIGHT // 2), 3)

        # -- Business balance (centre-right) ----------------------------
        pro_color = _RED if eco_mgr.business < 0 else _GREEN
        pro_label = f"Pro   : {eco_mgr.business:>9,.0f} €".replace(",", " ")
        self._blit(surface, self._font, pro_label, pro_color,
                   x=self.width // 2 + 20, y=y)

        # -- Key hints (right edge, small) ------------------------------
        hint = "[R] Enregistrer  [K] Kit  [S] Virement  [P] Pause"
        hint_surf = self._hint_font.render(hint, True, _DIM)
        surface.blit(hint_surf, (self.width - hint_surf.get_width() - 16,
                                  BAR_HEIGHT // 2 - hint_surf.get_height() // 2))

    def _draw_toasts(self, surface) -> None:
        x = self.width - 20
        y = BAR_HEIGHT + 12
        for toast in reversed(self._toasts[-6:]):          # newest on top, max 6
            alpha = min(255, int(toast["ttl"] / _TOAST_TTL * 255 * 2.5))
            surf = self._hint_font.render(toast["text"], True, toast["color"])
            surf.set_alpha(alpha)
            surface.blit(surf, (x - surf.get_width(), y))
            y += surf.get_height() + 4

    @staticmethod
    def _blit(surface, font, text, color, x, y) -> None:
        surface.blit(font.render(text, True, color), (x, y))
