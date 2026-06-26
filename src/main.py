import pygame
import sys

from engine.time_manager import TimeManager
from engine.economy_manager import EconomyManager
from business.manager import BusinessManager, MissionState
from ui.hud import HUD, BAR_HEIGHT
from ui.status_panel import StatusPanel
from ui.lead_panel import LeadPanel

SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
SALARY_TRANSFER = 100.0


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _wire_midnight(time_mgr: TimeManager, eco_mgr: EconomyManager, hud: HUD) -> None:
    def on_midnight():
        eco_mgr.on_midnight()
        for n in eco_mgr.pop_notifications():
            hud.push_toast(n.text, positive=n.positive)

    time_mgr.on_midnight(on_midnight)


def _flush_notifications(manager, hud: HUD) -> None:
    """Surface all pending notifications from any manager to the HUD."""
    for n in manager.pop_notifications():
        hud.push_toast(n.text, positive=n.positive)


def _handle_game_over(screen: pygame.Surface) -> None:
    font_big = pygame.font.SysFont("consolas", 52, bold=True)
    font_sub = pygame.font.SysFont("consolas", 26)
    screen.fill((20, 0, 0))
    msg = font_big.render("FAILLITE PERSONNELLE", True, (220, 55, 55))
    sub = font_sub.render("Votre compte perso est à zéro — game over.", True, (180, 100, 100))
    screen.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2, SCREEN_H // 2 - 60))
    screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 2 + 20))
    pygame.display.flip()
    pygame.time.wait(4_000)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Entrepreneur Simulator")
    clock = pygame.time.Clock()

    time_mgr = TimeManager()
    eco_mgr  = EconomyManager()
    biz_mgr  = BusinessManager()
    hud      = HUD(SCREEN_W)
    status   = StatusPanel()
    lead_ui  = LeadPanel(SCREEN_W, SCREEN_H)

    _wire_midnight(time_mgr, eco_mgr, hud)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ── Events ──────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                # Pause
                if event.key == pygame.K_p:
                    time_mgr.toggle_pause()
                    hud.push_toast("Pause" if time_mgr.is_paused else "Reprise ▶", positive=True)

                # Salary transfer  perso ← pro
                elif event.key == pygame.K_s:
                    ok = eco_mgr.transfer_salary(SALARY_TRANSFER)
                    if ok:
                        _flush_notifications(eco_mgr, hud)
                    else:
                        hud.push_toast("Fonds Pro insuffisants pour le virement.", positive=False)

                # Register business
                elif event.key == pygame.K_r:
                    biz_mgr.register(eco_mgr)
                    _flush_notifications(biz_mgr, hud)

                # Buy kit
                elif event.key == pygame.K_k:
                    biz_mgr.buy_kit(eco_mgr)
                    _flush_notifications(biz_mgr, hud)

                # Accept lead
                elif event.key == pygame.K_a:
                    if biz_mgr.mission_state == MissionState.LEAD_INCOMING:
                        biz_mgr.accept_lead(eco_mgr, time_mgr)
                        _flush_notifications(biz_mgr, hud)
                        # eco_mgr midnight toasts are auto-surfaced by _wire_midnight
                    else:
                        hud.push_toast("Aucune mission en attente.", positive=False)

                # Refuse lead
                elif event.key == pygame.K_d:
                    if biz_mgr.mission_state == MissionState.LEAD_INCOMING:
                        biz_mgr.refuse_lead()
                        _flush_notifications(biz_mgr, hud)

        # ── Update ──────────────────────────────────────────────────────
        time_mgr.update(dt)
        biz_mgr.update(dt, time_mgr.hour)
        hud.update(dt)

        # ── Game-over check ─────────────────────────────────────────────
        if eco_mgr.game_over:
            _handle_game_over(screen)
            running = False
            break

        # ── Draw ────────────────────────────────────────────────────────
        screen.fill((15, 15, 25))
        hud.draw(screen, time_mgr, eco_mgr)
        status.draw(screen, biz_mgr)

        if biz_mgr.mission_state == MissionState.LEAD_INCOMING:
            lead_ui.draw(screen, biz_mgr.current_lead)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
