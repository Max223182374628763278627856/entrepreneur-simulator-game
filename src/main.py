import pygame
import sys


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Entrepreneur Simulator")
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((15, 15, 25))
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
