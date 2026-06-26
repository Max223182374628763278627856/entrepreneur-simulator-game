import pygame
import sys

from engine.time_manager import TimeManager
from engine.economy_manager import EconomyManager
from ui.hud import HUD, BAR_HEIGHT

SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
SALARY_TRANSFER = 100.0


def _wire_midnight(time_mgr: TimeManager, eco_mgr: EconomyManager, hud: HUD) -> None:
    """Connect midnight event: deduct daily costs and push resulting toasts."""
    def on_midnight():
        eco_mgr.on_midnight()
        for notif in eco_mgr.pop_notifications():
            hud.push_toast(notif.text, positive=notif.positive)

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


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Entrepreneur Simulator")
    clock = pygame.time.Clock()

    time_mgr = TimeManager()
    eco_mgr  = EconomyManager()
    hud      = HUD(SCREEN_W)

    _wire_midnight(time_mgr, eco_mgr, hud)

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
                        for n in eco_mgr.pop_notifications():
                            hud.push_toast(n.text, positive=n.positive)
                    else:
                        hud.push_toast("Fonds Pro insuffisants pour le virement", positive=False)

        # ── Update ──────────────────────────────────────────────────────
        time_mgr.update(dt)
        hud.update(dt)

        # ── Game-over check ─────────────────────────────────────────────
        if eco_mgr.game_over:
            _handle_game_over(screen)
            running = False
            break

        # ── Draw ────────────────────────────────────────────────────────
        screen.fill((15, 15, 25))                     # world background
        # (future: draw world tiles, sprites, etc. below BAR_HEIGHT)
        hud.draw(screen, time_mgr, eco_mgr)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
