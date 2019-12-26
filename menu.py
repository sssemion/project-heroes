import pygame
import os
import sys

pygame.init()
screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()
FPS = 60
running = True


def terminate():
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, function=lambda x: x):
        super.__init__()
        self.x, self.y = x, y
        self.function = function

    def on_click(self, event):
        if self.x < event.pos[0] < self.x + self.width and self.y < event.pos[1] < self.y + self.height:
            self.function()

    def connect(self, function):
        self.function = function

    def set_backgroung_image(self, filename):
        img = load_image(filename)

    def update(self, *args):
        self.on_click(args[-1])






def start_screen():
    intro_text = []

    fon = pygame.transform.scale(load_image('background.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                terminate()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                print(1)
        pygame.display.flip()
        clock.tick(FPS)


start_screen()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        # elif event.type == pygame.KEYDOWN:
        #     if event.key == pygame.K_UP:
        #         move(player, 'up')
        #     if event.key == pygame.K_DOWN:
        #         move(player, 'down')
        #     if event.key == pygame.K_LEFT:
        #         move(player, 'left')
        #     if event.key == pygame.K_RIGHT:
        #         move(player, 'right')
    # all_sprites.draw(screen)
    # tiles_group.draw(screen)
    # player_group.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
