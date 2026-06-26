"""
Status panel — top-left corner below the HUD.
Shows business state, equipment, stock, marketing budget, and office.
"""

import pygame
from ui.hud import BAR_HEIGHT

_BG      = (18, 18, 30, 210)
_BORDER  = (55, 55, 80)
_NEUTRAL = (200, 200, 215)
_GREEN   = (72, 214, 110)
_RED     = (220, 75, 75)
_AMBER   = (220, 175, 50)
_BLUE    = (90, 160, 230)
_DIM     = (100, 100, 120)

_PAD  = 12
_W    = 268
_X    = 20
_Y    = BAR_HEIGHT + 10
_LINE = 18   # pixels per row


class StatusPanel:
    def __init__(self) -> None:
        self._title_font = pygame.font.SysFont("consolas", 15, bold=True)
        self._body_font  = pygame.font.SysFont("consolas", 14)
        self._hint_font  = pygame.font.SysFont("consolas", 12)

    def draw(self, surface: pygame.Surface, biz_mgr, marketing_mgr) -> None:
        from business.manager import BusinessState, MAX_STOCK_WITHOUT_OFFICE

        rows = self._build_rows(biz_mgr, marketing_mgr, BusinessState, MAX_STOCK_WITHOUT_OFFICE)
        h    = _PAD + 21 + len(rows) * _LINE + _PAD   # title + rows + padding
        card = pygame.Surface((_W, h), pygame.SRCALPHA)
        card.fill(_BG)
        pygame.draw.rect(card, _BORDER, (0, 0, _W, h), 1)
        surface.blit(card, (_X, _Y))

        x, y = _X + _PAD, _Y + _PAD

        # Title
        title = self._title_font.render("SERRURIER", True, _AMBER)
        surface.blit(title, (x, y))
        y += title.get_height() + 6

        for icon, label, color, hint_text in rows:
            line = f"{icon} {label}"
            surf = self._body_font.render(line, True, color)
            surface.blit(surf, (x, y))
            if hint_text:
                hint = self._hint_font.render(hint_text, True, _DIM)
                surface.blit(hint, (x + surf.get_width() + 8, y + 2))
            y += _LINE

    # ------------------------------------------------------------------

    def _build_rows(self, biz_mgr, mkt_mgr, BusinessState, MAX_STOCK_WITHOUT_OFFICE):
        rows = []
        active = biz_mgr.state == BusinessState.ACTIVE

        # -- State -------------------------------------------------------
        dot  = "●" if active else "○"
        col  = _GREEN if active else _RED
        hint = None if active else "[R] Enregistrer (200 € perso)"
        rows.append((dot, biz_mgr.state.value, col, hint))

        # -- Kit ---------------------------------------------------------
        kit_col  = _GREEN if biz_mgr.has_kit else _DIM
        kit_mark = "[v]" if biz_mgr.has_kit else "[ ]"
        kit_hint = None if biz_mgr.has_kit else "[K] Acheter (500 € pro)"
        rows.append((kit_mark, "Kit de crochetage", kit_col, kit_hint))

        # -- Stock -------------------------------------------------------
        if active and biz_mgr.has_kit:
            s = biz_mgr.stock_barillets
            mx = biz_mgr.max_stock
            if s == 0:
                s_col, s_hint = _RED, "[B] Commander barillets (150 €)"
            elif biz_mgr.stock_low:
                s_col, s_hint = _AMBER, "[B] Restock bientot"
            else:
                s_col, s_hint = _GREEN, None
            cap = "inf" if biz_mgr.has_office else str(MAX_STOCK_WITHOUT_OFFICE)
            rows.append(("  ", f"Stock : {s} / {cap}", s_col, s_hint))

        # -- Marketing ---------------------------------------------------
        if active:
            budget = mkt_mgr.daily_budget
            b_col  = _DIM if budget == 0 else _BLUE
            b_hint = "[+/-] Ajuster" if budget == 0 else None
            rows.append(("  ", f"Pub : {budget:.0f} €/j", b_col, b_hint))

        # -- Office ------------------------------------------------------
        if active:
            if biz_mgr.has_office:
                rows.append(("[v]", "Atelier loue", _GREEN, None))
            else:
                rows.append(("[ ]", "Pas d'atelier", _DIM, "[L] Louer (500 €/mois)"))

        return rows
