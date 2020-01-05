import pygame
import os
import sys
import random

GREEN, RED, BLUE, YELLOW = 'green', 'red', 'blue', 'yellow'

N = 4  # int(input())  # tmp

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
button_sprites = pygame.sprite.Group()
tile_sprites = pygame.sprite.Group()
player_sprites = pygame.sprite.Group()
unit_sprites = pygame.sprite.Group()


class Block:  # Предмет, блокирующий проход
    def __init__(self, tile_type='rock'):
        self.tile_type = tile_type

    def render(self, x, y):
        Tile(self.tile_type, x, y)


class Cell:  # Ячейка поля Field
    def __init__(self, cost=0, tile_type='grass', content=None):
        self.cost = cost  # cost - стоимость передвижения по клетке
        self.tile_type = tile_type
        self.content = content  # content - содержимое ячейки (None, экземпляр класса Block или любой другой объект)

    def get_cost(self):
        return self.cost

    def is_blocked(self):
        return type(self.content).__name__ == 'Block'

    def get_content(self):
        return self.content

    def render(self, x, y):
        Tile(self.tile_type, x, y)
        try:
            self.content.render(x, y)
        except AttributeError:
            pass


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

    def __init__(self, filename, number_of_players=1):
        filename = "data/maps/" + filename
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        # дополняем каждую строку пустыми клетками ('.')
        self.field = list(map(lambda x: list(x.ljust(max_width, '.')), level_map))
        self.width = len(self.field[0])
        self.height = len(self.field)
        self.players = {}

        self.number_of_players = number_of_players

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
                    self.field[x][y] = Cell()
                elif self.field[x][y] == '#':
                    self.field[x][y] = Cell(content=Block())
                elif self.field[x][y] == 'G':
                    self.players[GREEN] = [Player(x, y, GREEN)]
                    self.field[x][y] = Cell(content=self.players[GREEN][0])
                elif self.field[x][y] == 'R':
                    if self.number_of_players >= 2:
                        self.players[RED] = [Player(x, y, RED)]
                        self.field[x][y] = Cell(content=self.players[RED][0])
                    else:
                        self.field[x][y] = Cell()
                elif self.field[x][y] == 'B':
                    if self.number_of_players >= 3:
                        self.players[BLUE] = [Player(x, y, BLUE)]
                        self.field[x][y] = Cell(content=self.players[BLUE][0])
                    else:
                        self.field[x][y] = Cell()
                elif self.field[x][y] == 'Y':
                    if self.number_of_players >= 4:
                        self.players[YELLOW] = [Player(x, y, YELLOW)]
                        self.field[x][y] = Cell(content=self.players[YELLOW][0])
                    else:
                        self.field[x][y] = Cell()
                elif self.field[x][y] == '0':
                    self.field[x][y] = Cell(content=Item('money', 0, 0, '', 0))
                self.field[x][y].render(x, y)

    def move(self, direction):

        # Это все не работает. TODO: нормальное передвижение героев
        return

        x, y = self.player.get_pos()
        if direction == 'up':
            if y > 0 and not self.field[y - 1][x].is_blocked():
                self.player.move(x, y - 1)
                y -= 1
        elif direction == 'down':
            if y < self.height - 1 and not self.field[y + 1][x].is_blocked():
                self.player.move(x, y + 1)
                y += 1
        elif direction == 'left':
            if x > 0 and not self.field[y][x - 1].is_blocked():
                self.player.move(x - 1, y)
                x -= 1
        elif direction == 'right':
            if x < self.width - 1 and not self.field[y][x + 1].is_blocked():
                self.player.move(x + 1, y)
                x += 1

        content = self.field[y][x].get_content()
        if content is not None:
            self.player.interact(content)
            if type(content).__name__ == "Item":
                self.field[y][x].content = None
                self.field[y][x].render(y, x)

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


class Unit(pygame.sprite.Sprite):
    def __init__(self, image, name, attack, defence, min_dmg, max_dmg, count, speed, hp, team, shoot):
        super().__init__(unit_sprites)
        self.image = load_image(image)
        self.dead = 0
        self.counter = True
        self.top_hp = hp
        self.team = team
        self.shoot = shoot
        self.count, self.name, self.atc, self.dfc, self.min_dmg, self.max_dmg, self.spd, self.hp = \
            count, name, attack, defence, min_dmg, max_dmg, speed, hp
        self.cur_atc, self.cur_dfc, self.cur_min_dmg, self.cur_max_dmg, self.cur_spd, self.cur_hp, self.cur_top_hp = \
            attack, defence, min_dmg, max_dmg, speed, hp, hp

    def attack_rat(self, enemy):
        damage = random.randint(self.min_dmg, self.max_dmg) * (self.cur_atc / enemy.cur_dfc) * (self.count + 1)
        enemy.get_rat_damage(damage)

    def attack_hon(self, enemy):
        damage = random.randint(self.min_dmg, self.max_dmg) * (self.cur_atc / enemy.cur_dfc) * (self.count + 1)
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
                random.randint(self.min_dmg, self.max_dmg) * (self.cur_atc / attacker.cur_dfc) * (self.count + 1))
        else:
            self.dead = 1

    def get_rat_damage(self, damage):
        self.count -= damage // self.hp
        self.top_hp -= damage % self.hp
        if self.count < 0:
            self.dead = 1

    def hero_bonus(self, hero):
        d_atc, d_dfc, d_features = hero.atc, hero.dfc, hero.bonus
        self.cur_atc, self.cur_dfc, self.hp, self.cur_spd, self.cur_top_hp = \
            self.cur_atc + d_atc, self.cur_dfc + d_dfc, self.hp + d_features['d_hp'], \
            self.cur_spd + d_features['d_spd'], self.cur_top_hp + d_features['d_hp']

    def update(self, updating_type='', *args):
        if updating_type:
            if updating_type == 'adjust-size':
                width, height = args
                self.image = pygame.transform.scale(self.image, (width, height))
            # ... other types
            else:
                raise Exception(f'incorrect updating_type: {updating_type}')

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


class FightBoard:
    margin_top = 125
    margin_right = margin_left = 50
    margin_bottom = 25

    def __init__(self, board, width, height):
        self.board = board
        self.width = width
        self.height = height
        self.rows = self.cols = 0
        self.cell_width = self.cell_height = 0
        self.surface = pygame.Surface((width, height))
        self.surface.blit(pygame.transform.scale(load_image('fight-background.jpg'), (width, height)), (0, 0))

    def draw_cells(self):
        self.rows = len(self.board)
        self.cols = len(self.board[0])
        self.cell_width = (self.width - FightBoard.margin_left - FightBoard.margin_right) // self.cols
        self.cell_height = (self.height - FightBoard.margin_top - FightBoard.margin_bottom) // self.rows
        cells_surface = pygame.Surface((self.width - FightBoard.margin_left - FightBoard.margin_right + 2,
                                        self.height - FightBoard.margin_top - FightBoard.margin_bottom + 2))
        for i in range(self.rows + 1):
            pygame.draw.line(cells_surface, 0xffffff, (0, i * self.cell_height),
                             (self.width - FightBoard.margin_right - FightBoard.margin_left, i * self.cell_height), 2)
        for i in range(self.cols + 1):
            pygame.draw.line(cells_surface, 0xffffff, (i * self.cell_width, 0),
                             (i * self.cell_width, self.height - FightBoard.margin_top - FightBoard.margin_bottom), 2)
        cells_surface.set_colorkey(0x000000)
        cells_surface.set_alpha(128)
        self.surface.blit(cells_surface, (FightBoard.margin_right, FightBoard.margin_top))

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)

    def get_cell(self, mouse_pos):
        if not (FightBoard.margin_left <= mouse_pos[
            0] <= FightBoard.margin_left + self.width * self.cell_width) or not (
                FightBoard.margin_top <= mouse_pos[1] <= FightBoard.margin_top + self.height * self.cell_height):
            return None
        return (mouse_pos[1] - FightBoard.margin_top) // self.cell_height, (
                mouse_pos[0] - FightBoard.margin_left) // self.cell_width

    def on_click(self, cell):
        pass


class HeroFightScreen:
    width, height = 125, 300
    font = pygame.font.Font('data/HoMMFontCyr.ttf', 16)

    def __init__(self, hero, right=False):
        self.surface = pygame.Surface((HeroFightScreen.width, HeroFightScreen.height))
        self.surface.blit(pygame.transform.scale(load_image('fight-hero-background.jpg'),
                                                 (HeroFightScreen.width, HeroFightScreen.height)), (0, 0))
        self.hero = hero
        self.right = right
        self.img_height = 0

    def draw_image(self):
        img = self.hero.original_image
        if self.right:
            img = pygame.transform.flip(img, True, False)
        w, h = img.get_size()
        h = (h * (HeroFightScreen.width - 10)) // w
        w = HeroFightScreen.width - 10
        self.img_height = h
        self.surface.blit(pygame.transform.scale(img, (w, h)), (5, 5))

    def draw_text(self):
        atc, dfc = self.hero.get_characteristics()
        text = [
            f'Атака: {atc}',
            f'Защита: {dfc}',
        ]
        text_coord = self.img_height + 10
        for line in text:
            string = HeroFightScreen.font.render(line, 1, pygame.color.Color(156, 130, 79))
            string_rect = string.get_rect()
            text_coord += 5
            string_rect.top = text_coord
            string_rect.x = 10
            text_coord += string_rect.height
            self.surface.blit(string, string_rect)


def fight(left_hero, right_hero):  # TODO
    coor_row = [0, 1, 3, 4, 5, 7, 8]
    null_unit = Unit("player.png", "", 0, 0, 0, 0, 0, 0, 0, "", False)
    board = [[0] * 10 for _ in range(9)]
    turn_queue = left_hero.army + right_hero.army

    for num in range(len(left_hero.army)):
        if left_hero.army[num] != null_unit:
            board[coor_row[num]][0] = left_hero.army[num]

    for num in range(len(right_hero.army)):
        if right_hero.army[num] != null_unit:
            board[coor_row[num]][9] = right_hero.army[num]

    # Сохраняем основной экран и затемняем его
    screen_save = screen.copy()
    black = pygame.Surface((WIDTH, HEIGHT))
    black.fill(pygame.color.Color(0, 0, 0))
    black.set_alpha(200)
    screen.blit(black, (0, 0))

    # Создаем экран боя
    width, height = 800, 556
    topleft_coord = ((WIDTH - width) // 2, (HEIGHT - height) // 2)
    fight_board = FightBoard(board, width, height)

    # Чертим клеточки
    fight_board.draw_cells()

    # Создаем экраны героев
    left_hero_screen = HeroFightScreen(left_hero)
    left_hero_screen.draw_image()
    left_hero_screen.draw_text()
    screen.blit(left_hero_screen.surface, (topleft_coord[0] - HeroFightScreen.width - 5, topleft_coord[1]))

    right_hero_screen = HeroFightScreen(right_hero, right=True)
    right_hero_screen.draw_image()
    right_hero_screen.draw_text()
    screen.blit(right_hero_screen.surface, (topleft_coord[0] + width + 5, topleft_coord[1]))

    screen.blit(fight_board.surface, topleft_coord)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    screen.blit(screen_save, (0, 0))
                    return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                x -= topleft_coord[0]
                y -= topleft_coord[1]
                fight_board.get_click((x, y))
        pygame.display.flip()
        clock.tick(FPS)


class Meet:  # TODO
    def __init__(self, left_hero, right_hero):
        pass


class Item:
    def __init__(self, name, d_atc, d_dfc, description, slot, tile_type='coins', feature=None):
        self.name, self.d_atc, self.d_dfc, self.description, self.feature = name, d_atc, d_dfc, description, feature
        self.slot = slot
        self.tile_type = tile_type

    def equip_dequip(self):
        return self.d_atc, self.d_dfc, self.feature

    def get_description(self):
        return self.description

    def __eq__(self, other):
        if self.name == other.name and self.d_atc == other.d_atc and self.d_dfc == other.d_dfc and self.description == other.description and self.feature == other.feature:
            return True
        return False

    def render(self, x, y):
        Tile(self.tile_type, x, y)

    def stats(self):  # я хз что она должна возвращать TODO Item.stats()
        pass


class Player(pygame.sprite.Sprite):
    image = load_image('player.png', -1)
    null_item = Item("", 0, 0, "all", "")
    null_unit = Unit("player.png", "", 0, 0, 0, 0, 0, 0, 0, "", False)

    def __init__(self, pos_y, pos_x, team):
        super().__init__(player_sprites)
        self.team = team
        self.image = pygame.transform.scale(self.image, (tile_width, tile_height))
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect().move(tile_width * pos_x,
                                               tile_height * pos_y)
        self.pos = pos_x, pos_y
        self.type = 'hero'
        self.team = team
        self.atc, self.dfc = 0, 0
        self.xp, self.next_level = 0, 1000
        self.inventory = [Player.null_item] * 30
        self.equiped_items = [Player.null_item] * 10
        self.bonus = {'anti_tax': 0, 'd_hp': 0, 'bonus_move': 0, 'd_spd': 0}
        self.army = [Player.null_unit] * 7

    def move(self, x, y):
        self.pos = x, y
        self.rect = self.image.get_rect().move(tile_width * x,
                                               tile_height * y)

    def get_pos(self):
        return self.pos

    def swap_item(self, other, slot):
        if (self.equiped_items[slot].slot == other.slot) or self.equiped_items[slot] == \
                Player.null_item or other == Player.null_item:
            d_atc, d_dfc, d_feat = self.equiped_items[slot].equip_dequip()
            self.atc, self.dfc = self.atc - d_atc, self.dfc - d_dfc
            for key, val in d_feat.items():
                self.bonus[key] -= val
            self.equiped_items[slot], self.inventory[self.inventory.index(Player.null_item)] = \
                other, self.equiped_items[slot]
            d_atc, d_dfc, d_feat = self.equiped_items[slot].equip_dequip()
            self.atc, self.dfc = self.atc + d_atc, self.dfc + d_dfc
            for key, val in d_feat.items():
                self.bonus[key] += val
            return True
        return False

    def interact(self, other):
        if type(other).__name__ == 'Hero':
            if other.team != self.team:
                self.fight(other)
                return
            if other.team == self.team:
                self.meet(other)
                return
        elif type(other).__name__ == 'Item':  # А тут вписать то что будет в этом классе,
            # который отвечает за предмет лежащий на поле
            self.inventory[self.inventory.index(Player.null_item)] = Item(*other.stats())  # Что-то типа заглушки,
            # которая превращает предмет, который лежит на полу в предмет, который в инвентаре герояTODO * 3

        elif type(other).__name__ == 'build':
            if other.variety != 'town':  # Опять заглушка
                d_atc, d_dfc, d_features = other.visit
                self.atc, self.dfc = self.atc + d_atc, self.dfc + d_dfc
                for key, val in d_features.items():
                    self.bonus[key] += val

    def get_characteristics(self):
        return self.atc, self.dfc

    # Два метода заглушки, которые ещё рано реализовывать, так как на карте даже двух героев то нет,
    # а тут их взаимодействия и эт фронт уже (твоя работа), так что я иду нафиг Соре
    # Тут наверно придется класс Fight писать TODO * 2
    def fight(self, other):
        pass

    def meet(self, other):
        pass

    def render(self, *args):  # рисует кружочек возле героя чтобы различать разные команды
        x, y = self.get_pos()
        pygame.draw.ellipse(self.image, pygame.color.Color(self.team), pygame.Rect(int(tile_width * 0.35),
                                                                                   int(tile_height * 0.75),
                                                                                   int(tile_width * 0.3),
                                                                                   int(tile_height * 0.2)))


class Tile(pygame.sprite.Sprite):
    tile_images = {
        'grass': load_image("grass.png"),
        'rock': load_image("rock.png", -1),
        'coins': load_image("coins.png"),
    }

    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(tile_sprites)
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


def start_screen():
    fon = pygame.transform.scale(load_image('background.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))

    bwidth, bheight = 400, 80

    font = pygame.font.Font(None, 80)

    start_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight * 4) // 2,
                          bwidth, bheight)
    start_button.set_background_image('button-background.jpg')
    start_button.set_text("Start", font, pygame.color.Color(156, 130, 79))
    start_button.render()

    settings_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight) // 2, bwidth,
                             bheight)
    settings_button.set_background_image('button-background.jpg')
    settings_button.set_text("Settings", font, pygame.color.Color(156, 130, 79))
    settings_button.render()

    exit_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT + bheight * 2) // 2, bwidth,
                         bheight, terminate)
    exit_button.set_background_image('button-background.jpg')
    exit_button.set_text("Exit", font, pygame.color.Color(32, 32, 32))
    exit_button.render()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                terminate()
            if start_button.clicked or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                return
            button_sprites.update(event)
        pygame.display.flip()
        clock.tick(FPS)


start_screen()  # Main menu
screen.fill(0xff0000)
field = Field("example.txt", N)  # Игровое поле

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
            if event.key == pygame.K_f:
                fight(field.players[GREEN][0], field.players[BLUE][0])
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                edge_x, edge_y = field.size_in_pixels
                x, y = event.pos
                if x < edge_x and y < edge_y:
                    print(1)
    all_sprites.draw(screen)
    tile_sprites.draw(field.space)
    player_sprites.draw(field.space)
    screen.blit(field.space, (Field.margin_right, Field.margin_top))
    pygame.display.flip()
    clock.tick(FPS)
