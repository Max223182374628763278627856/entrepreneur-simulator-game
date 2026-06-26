"""
Lead panel — modal card for incoming job calls.
Shows mission details, barillet requirement, and [A]/[D] prompts.
"""

import pygame
from business.jobs import Urgency

_CARD_W  = 540
_CARD_H  = 260

_BG_CARD   = (22, 22, 38, 230)
_BORDER    = (80, 80, 110)
_HEADER_BG = (30, 30, 50)
_NEUTRAL   = (200, 200, 215)
_GREEN     = (72, 214, 110)
_RED       = (220, 75, 75)
_AMBER     = (220, 175, 50)
_DIM       = (110, 110, 130)
_ORANGE    = (230, 130, 50)

_URGENCY_COLOR = {
    Urgency.LOW:    (100, 200, 120),
    Urgency.MEDIUM: (220, 175, 50),
    Urgency.HIGH:   (220, 75,  75),
}


class LeadPanel:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self._sw = screen_w
        self._sh = screen_h
        self._title_font  = pygame.font.SysFont("consolas", 16, bold=True)
        self._detail_font = pygame.font.SysFont("consolas", 14)
        self._key_font    = pygame.font.SysFont("consolas", 16, bold=True)
        self._warn_font   = pygame.font.SysFont("consolas", 13)

    def draw(self, surface: pygame.Surface, lead, stock: int) -> None:
        cx = (self._sw - _CARD_W) // 2
        cy = (self._sh - _CARD_H) // 2

        # Background card
        card = pygame.Surface((_CARD_W, _CARD_H), pygame.SRCALPHA)
        card.fill(_BG_CARD)
        surface.blit(card, (cx, cy))
        pygame.draw.rect(surface, _BORDER, (cx, cy, _CARD_W, _CARD_H), 2)

        # Header strip
        pygame.draw.rect(surface, _HEADER_BG, (cx, cy, _CARD_W, 36))
        urgency_color = _URGENCY_COLOR.get(lead.urgency, _AMBER)
        header = self._title_font.render(
            "  APPEL  —  " + lead.description.upper(), True, urgency_color
        )
        surface.blit(header, (cx + 14, cy + 10))
        pygame.draw.line(surface, _BORDER, (cx, cy + 36), (cx + _CARD_W, cy + 36), 1)

        # Detail rows
        lx = cx + 28
        y  = cy + 50
        rows = [
            ("Distance",        f"{lead.distance} km"),
            ("Remuneration",    f"{lead.payment:.0f} €"),
            ("Frais carburant", f"-{lead.travel_cost:.2f} €"),
            ("Net estime",      f"{lead.net_gain:.2f} €"),
            ("Consommable",     "1 barillet"),
            ("Duree mission",   "~2 h"),
        ]
        for label, value in rows:
            ls = self._detail_font.render(f"{label:<18}", True, _DIM)
            vs = self._detail_font.render(value, True, _NEUTRAL)
            surface.blit(ls, (lx, y))
            surface.blit(vs, (lx + ls.get_width(), y))
            y += ls.get_height() + 3

        # Stock warning banner
        if stock == 0:
            warn_bg = pygame.Surface((_CARD_W - 4, 22), pygame.SRCALPHA)
            warn_bg.fill((60, 20, 20, 180))
            surface.blit(warn_bg, (cx + 2, cy + _CARD_H - 68))
            warn = self._warn_font.render(
                "  Stock epuise — achetez des barillets [B] pour accepter", True, _ORANGE
            )
            surface.blit(warn, (cx + 8, cy + _CARD_H - 66))

        # Divider & action buttons
        btn_y = cy + _CARD_H - 34
        pygame.draw.line(surface, _BORDER,
                         (cx, btn_y - 10), (cx + _CARD_W, btn_y - 10), 1)
        accept_col = _GREEN if stock > 0 else _DIM
        accept = self._key_font.render("[A]  Accepter", True, accept_col)
        refuse = self._key_font.render("[D]  Refuser",  True, _RED)
        surface.blit(accept, (cx + 60, btn_y))
        surface.blit(refuse, (cx + _CARD_W - refuse.get_width() - 60, btn_y))
