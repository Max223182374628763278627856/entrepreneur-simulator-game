"""
Status panel — top-left corner below the HUD.
Shows business registration state and equipment inventory.
"""

import pygame
from ui.hud import BAR_HEIGHT

_BG        = (18, 18, 30, 210)   # RGBA — drawn on a temp surface for alpha
_BORDER    = (55, 55, 80)
_NEUTRAL   = (200, 200, 215)
_GREEN     = (72, 214, 110)
_RED       = (220, 75, 75)
_AMBER     = (220, 175, 50)
_DIM       = (100, 100, 120)

_PAD   = 12
_W     = 248
_H     = 100
_X     = 20
_Y     = BAR_HEIGHT + 10


class StatusPanel:
    def __init__(self) -> None:
        self._title_font = pygame.font.SysFont("consolas", 15, bold=True)
        self._body_font  = pygame.font.SysFont("consolas", 14)
        self._hint_font  = pygame.font.SysFont("consolas", 12)

    def draw(self, surface: pygame.Surface, biz_mgr) -> None:
        from business.manager import BusinessState

        # Semi-transparent background
        card = pygame.Surface((_W, _H), pygame.SRCALPHA)
        card.fill(_BG)
        pygame.draw.rect(card, _BORDER, (0, 0, _W, _H), 1)
        surface.blit(card, (_X, _Y))

        x, y = _X + _PAD, _Y + _PAD

        # Title
        title = self._title_font.render("SERRURIER", True, _AMBER)
        surface.blit(title, (x, y))
        y += title.get_height() + 6

        # Business state
        active = biz_mgr.state == BusinessState.ACTIVE
        dot_color = _GREEN if active else _RED
        state_label = biz_mgr.state.value
        pygame.draw.circle(surface, dot_color, (x + 5, y + 7), 5)
        state_surf = self._body_font.render(state_label, True, _NEUTRAL)
        surface.blit(state_surf, (x + 16, y))
        y += state_surf.get_height() + 4

        # Kit status
        kit_color = _GREEN if biz_mgr.has_kit else _DIM
        kit_mark  = "[✓]" if biz_mgr.has_kit else "[ ]"
        kit_label = f"{kit_mark} Kit de crochetage"
        kit_surf  = self._body_font.render(kit_label, True, kit_color)
        surface.blit(kit_surf, (x, y))
        y += kit_surf.get_height() + 6

        # Contextual hints
        if biz_mgr.state != BusinessState.ACTIVE:
            hint = "[R] Enregistrer entreprise (200 € perso)"
        elif not biz_mgr.has_kit:
            hint = "[K] Acheter kit (500 € pro)"
        else:
            hint = "[R/K] déjà configuré"
        hint_surf = self._hint_font.render(hint, True, _DIM)
        surface.blit(hint_surf, (x, y))
