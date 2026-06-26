import pygame
import sys

from engine.time_manager import TimeManager
from engine.economy_manager import EconomyManager
from business.manager import BusinessManager, MissionState
from business.marketing import MarketingManager
from ui.hud import HUD, BAR_HEIGHT
from ui.status_panel import StatusPanel
from ui.lead_panel import LeadPanel

SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
SALARY_TRANSFER = 100.0


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _flush(manager, hud: HUD) -> None:
    """Surface all pending notifications from any manager to the HUD."""
    for n in manager.pop_notifications():
        hud.push_toast(n.text, positive=n.positive)


def _wire_midnight(
    time_mgr: TimeManager,
    eco_mgr:  EconomyManager,
    biz_mgr:  BusinessManager,
    mkt_mgr:  MarketingManager,
    hud:      HUD,
) -> None:
    def on_midnight() -> None:
        # 1. Daily living costs + overdraft agios
        eco_mgr.on_midnight()
        _flush(eco_mgr, hud)

        # 2. Daily marketing spend
        for n in mkt_mgr.on_midnight(eco_mgr):
            hud.push_toast(n.text, positive=n.positive)

        # 3. Monthly office rent (auto-triggers every 30 game days)
        biz_mgr.on_midnight(eco_mgr)
        _flush(biz_mgr, hud)

    time_mgr.on_midnight(on_midnight)


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
    mkt_mgr  = MarketingManager()
    hud      = HUD(SCREEN_W)
    status   = StatusPanel()
    lead_ui  = LeadPanel(SCREEN_W, SCREEN_H)

    _wire_midnight(time_mgr, eco_mgr, biz_mgr, mkt_mgr, hud)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ── Events ──────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_p:
                    time_mgr.toggle_pause()
                    hud.push_toast("Pause" if time_mgr.is_paused else "Reprise ▶", positive=True)

                elif event.key == pygame.K_s:
                    ok = eco_mgr.transfer_salary(SALARY_TRANSFER)
                    if ok:
                        _flush(eco_mgr, hud)
                    else:
                        hud.push_toast("Fonds Pro insuffisants pour le virement.", positive=False)

                elif event.key == pygame.K_r:
                    biz_mgr.register(eco_mgr)
                    _flush(biz_mgr, hud)

                elif event.key == pygame.K_k:
                    biz_mgr.buy_kit(eco_mgr)
                    _flush(biz_mgr, hud)

                elif event.key == pygame.K_b:
                    biz_mgr.buy_barillets(eco_mgr)
                    _flush(biz_mgr, hud)

                elif event.key == pygame.K_l:
                    biz_mgr.rent_office(eco_mgr)
                    _flush(biz_mgr, hud)

                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    mkt_mgr.increase()
                    hud.push_toast(f"Budget pub : {mkt_mgr.daily_budget:.0f} €/j", positive=True)

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    mkt_mgr.decrease()
                    hud.push_toast(f"Budget pub : {mkt_mgr.daily_budget:.0f} €/j", positive=True)

                elif event.key == pygame.K_a:
                    if biz_mgr.mission_state == MissionState.LEAD_INCOMING:
                        biz_mgr.accept_lead(eco_mgr, time_mgr)
                        _flush(biz_mgr, hud)
                    else:
                        hud.push_toast("Aucune mission en attente.", positive=False)

                elif event.key == pygame.K_d:
                    if biz_mgr.mission_state == MissionState.LEAD_INCOMING:
                        biz_mgr.refuse_lead()
                        _flush(biz_mgr, hud)

        # ── Update ──────────────────────────────────────────────────────
        time_mgr.update(dt)
        biz_mgr.update(dt, time_mgr.hour, mkt_mgr.lead_rate)
        hud.update(dt)

        # ── Game-over check ─────────────────────────────────────────────
        if eco_mgr.game_over:
            _handle_game_over(screen)
            running = False
            break

        # ── Draw ────────────────────────────────────────────────────────
        screen.fill((15, 15, 25))
        hud.draw(screen, time_mgr, eco_mgr)
        status.draw(screen, biz_mgr, mkt_mgr)

        if biz_mgr.mission_state == MissionState.LEAD_INCOMING:
            lead_ui.draw(screen, biz_mgr.current_lead, biz_mgr.stock_barillets)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
