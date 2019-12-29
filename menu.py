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
    fullname = os.path.join('data/images', name)
    image = pygame.image.load(fullname).convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Button(pygame.sprite.Sprite):
    def __init__(self, group, surface, x, y, width, height, function=lambda: None):
        super().__init__(group)
        self.surface = surface
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.function = function
        self.bgcolor = pygame.Color(255, 255, 255)
        self.bgimage = None
        self.hovered = False
        self.clicked = False

    def on_click(self, event):
        self.clicked = False
        if self.x < event.pos[0] < self.x + self.width \
                and self.y < event.pos[1] < self.y + self.height:
            self.clicked = True
            self.function()

    def on_hover(self, event):  # По наведении курсора на кнопку
        self.hovered = False
        if self.x < event.pos[0] < self.x + self.width \
                and self.y < event.pos[1] < self.y + self.height:
            self.hovered = True

    def connect(self, function):
        self.function = function

    def set_background_image(self, filename):
        self.bgimage = load_image(filename)
        self.bgimage = pygame.transform.scale(self.bgimage, (self.width, self.height))

    def set_background_color(self, color: pygame.Color):
        self.bgcolor = color

    def set_text(self, text, font: pygame.font.Font, color: pygame.color.Color):
        self.text = text
        self.font = font
        self.textcolor = color

    def update(self, *args):
        for arg in args:
            if arg.type == pygame.MOUSEBUTTONDOWN:
                self.on_click(arg)
            elif arg.type == pygame.MOUSEMOTION:
                self.on_hover(arg)
        self.render()

    def render(self):
        self.image = pygame.Surface([self.width, self.height])
        if self.bgimage is not None:
            self.image.blit(self.bgimage, (0, 0))
        else:
            self.image.fill(self.bgcolor)
        if self.hovered:
            black = pygame.Surface((self.width, self.height))
            black.fill(pygame.Color(0, 0, 0))
            black.set_alpha(32 + 32 * self.clicked)
            self.clicked = False
            self.image.blit(black, (0, 0))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        try:
            rendered = self.font.render(self.text, True, self.textcolor)
            w, h = rendered.get_size()
            self.image.blit(rendered, ((self.width - w) // 2, (self.height - h) // 2))
        except AttributeError:
            print('error')

        self.surface.blit(self.image, (self.x, self.y))


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

    buttons = pygame.sprite.Group()
    bwidth, bheight = 400, 80

    start_button = Button(buttons, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight * 4) // 2,
                          bwidth, bheight)
    start_button.set_background_image('button-background.jpg')
    font = pygame.font.Font(None, 80)
    start_button.set_text("Start", font, pygame.Color(156, 130, 79))
    start_button.render()

    settings_button = Button(buttons, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight) // 2, bwidth,
                             bheight)
    settings_button.set_background_image('button-background.jpg')
    font = pygame.font.Font(None, 80)
    settings_button.set_text("Settings", font, pygame.Color(156, 130, 79))
    settings_button.render()

    exit_button = Button(buttons, screen, (WIDTH - bwidth) // 2, (HEIGHT + bheight * 2) // 2, bwidth,
                         bheight, terminate)
    exit_button.set_background_image('button-background.jpg')
    font = pygame.font.Font(None, 80)
    exit_button.set_text("Exit", font, pygame.Color(32, 32, 32))
    exit_button.render()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                terminate()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                pass
            if event.type == pygame.MOUSEMOTION:
                pass
            buttons.update(event)
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
