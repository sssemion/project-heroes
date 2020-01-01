import pygame
import os
import sys
import random

pygame.init()
screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()
FPS = 60
running = True

tile_width = tile_height = 50


def terminate():
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None):
    fullname = os.path.join('data/images', name)
    image = pygame.image.load(fullname).convert_alpha()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# Sprite groups
all_sprites = pygame.sprite.Group()
buttons = pygame.sprite.Group()
tiles = pygame.sprite.Group()
players = pygame.sprite.Group()


class ControlPanel:  # Панель управления в правой части экрана
    width = 200  # px


class ResourcePanel:  # Панель ресурсов в нижней части экрана
    height = 40  # px


class Field:  # Игровое поле
    size_in_pixels = WIDTH - ControlPanel.width, HEIGHT - ResourcePanel.height
    margin_top = int(15 / 732 * size_in_pixels[1])
    margin_right = int(13 / 1171 * size_in_pixels[0])
    margin_left = int(15 / 1171 * size_in_pixels[0])
    margin_bottom = int(16 / 732 * size_in_pixels[1])

    def __init__(self, filename):
        filename = "data/maps/" + filename
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        # дополняем каждую строку пустыми клетками ('.')
        self.field = list(map(lambda x: x.ljust(max_width, '.'), level_map))
        self.width = len(self.field[0])
        self.height = len(self.field)
        self.player = None

        self.render()

    def render(self):
        self.frame = pygame.transform.scale(load_image('frame.png'), Field.size_in_pixels)
        screen.blit(self.frame, (0, 0))
        w, h = self.frame.get_size()
        self.space = pygame.Surface((w - Field.margin_right - Field.margin_left,
                                     h - Field.margin_top - Field.margin_bottom))
        self.space.blit(
            pygame.transform.scale(load_image('black-texture.png'), (w, w)), (0, 0))

        for x in range(self.height):
            for y in range(self.width):
                if self.field[x][y] == '.':
                    Tile('grass', x, y)
                elif self.field[x][y] == '#':
                    Tile('grass', x, y)
                    Tile('rock', x, y)
                elif self.field[x][y] == '@':
                    Tile('grass', x, y)
                    self.player = Player(x, y, 'green')
                    self.field[x] = self.field[x][:y] + '.' + self.field[x][y + 1:]

    def move(self, direction):
        x, y = self.player.get_pos()
        if direction == 'up':
            if y > 0 and self.field[y - 1][x] == '.':
                self.player.move(x, y - 1)
        elif direction == 'down':
            if y < self.height - 1 and self.field[y + 1][x] == '.':
                self.player.move(x, y + 1)
        elif direction == 'left':
            if x > 0 and self.field[y][x - 1] == '.':
                self.player.move(x - 1, y)
        elif direction == 'right':
            if x < self.width - 1 and self.field[y][x + 1] == '.':
                self.player.move(x + 1, y)

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        if cell is not None:
            self.on_click(cell)

    def get_cell(self, mouse_pos):
        if not (Field.margin_left <= mouse_pos[0] <= Field.margin_left + self.width * tile_width) or not (
                Field.margin_top <= mouse_pos[1] <= Field.margin_top + self.height * tile_height):
            return None
        return (mouse_pos[1] - Field.margin_top) // tile_height, (mouse_pos[0] - Field.margin_left) // tile_width

    def on_click(self, cell_coords):
        pass


class Player(pygame.sprite.Sprite):
    image = load_image('player.png', -1)

    def __init__(self, pos_y, pos_x, team):
        super().__init__(players)
        self.team = team
        self.image = pygame.transform.scale(self.image, (tile_width, tile_height))
        self.rect = self.image.get_rect().move(tile_width * pos_x,
                                               tile_height * pos_y)
        self.pos = pos_x, pos_y

    def move(self, x, y):
        self.pos = x, y
        self.rect = self.image.get_rect().move(tile_width * x,
                                               tile_height * y)

    def get_pos(self):
        return self.pos


class Tile(pygame.sprite.Sprite):
    tile_images = {
        'grass': load_image("grass.png"),
        'rock': load_image("rock.png", -1),
    }

    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(tiles)
        self.image = pygame.transform.scale(Tile.tile_images[tile_type], (tile_width, tile_height))
        self.rect = self.image.get_rect().move(tile_width * pos_x,
                                               tile_height * pos_y)


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
        self.clicked = False
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

# Здесь нужно сделать всё по красоте, чтобы он наследовался от спрайта и рисовался во время битвы,
# ведь я всего лишь бэкэнд - лох, а ты фронтенд гений!!! TODO
class Unit:
    def __init__(self, name, attack, defence, min_dmg, max_dmg, count, speed, hp, town):
        self.dead = 0
        self.counter = True
        self.top_hp = hp
        self.town = town
        self.count, self.name, self.atc, self.dfc, self.min_dmg, self.max_dmg, self.spd, self.hp = count, name, attack, defence, min_dmg, max_dmg, speed, hp

    def attack_rat(self, enemy):
        damage = random.randint(self.min_dmg, self.max_dmg) * (self.atc / enemy.dfc) * (self.count + 1)
        enemy.get_rat_damage(damage)

    def attack_hon(self, enemy):
        damage = random.randint(self.min_dmg, self.max_dmg) * (self.atc / enemy.dfc) * (self.count + 1)
        if enemy.counter:
            enemy.get_honest_damage(damage, self)
        else:
            enemy.get_rat_damage(damage)

    def get_honest_damage(self, damage, attacker):
        self.count -= damage // self.hp
        self.top_hp -= damage % self.hp
        if self.count >= 0:
            self.counter = False
            attacker.get_rat_damage(
                random.randint(self.min_dmg, self.max_dmg) * (self.atc / attacker.dfc) * (self.count + 1))
        else:
            self.dead = 1

    def get_rat_damage(self, damage):
        self.count -= damage // self.hp
        self.top_hp -= damage % self.hp
        if self.count < 0:
            self.dead = 1

    def __lt__(self, other):
        if self.spd < other.spd:
            return True
        return False

    def __le__(self, other):
        if self.spd <= other.spd:
            return True
        return False

    def __gt__(self, other):
        if self.spd > other.spd:
            return True
        return False

    def __ge__(self, other):
        if self.spd >= other.spd:
            return True
        return False


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
            if start_button.clicked:
                return
            buttons.update(event)
        pygame.display.flip()
        clock.tick(FPS)


start_screen()  # Main menu
screen.fill(0xff0000)
field = Field("example.txt")  # Игровое поле

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            terminate()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                field.move('up')
            if event.key == pygame.K_DOWN:
                field.move('down')
            if event.key == pygame.K_LEFT:
                field.move('left')
            if event.key == pygame.K_RIGHT:
                field.move('right')
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                edge_x, edge_y = field.size_in_pixels
                x, y = event.pos
                if x < edge_x and y < edge_y:
                    print(1)
    all_sprites.draw(screen)
    tiles.draw(field.space)
    players.draw(field.space)
    screen.blit(field.space, (Field.margin_right, Field.margin_top))
    pygame.display.flip()
    clock.tick(FPS)
