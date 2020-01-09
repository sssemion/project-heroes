import itertools
import os
import random
import sys
import traceback

import networkx
import pygame

GREEN, RED, BLUE, YELLOW = 'green', 'red', 'blue', 'yellow'
selected_hero, current_color = None, GREEN
sel_her_row, sel_her_col = None, None
last_row, last_col = -1, -1
N = 1  # tmp

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
arrow_sprites = pygame.sprite.Group()


class Block:  # Предмет, блокирующий проход
    def __init__(self, tile_type='rock'):
        self.tile_type = tile_type

    def render(self, x, y):
        Tile(self.tile_type, x, y)


class Cell:  # Ячейка поля Field
    def __init__(self, cost=100, tile_type='grass', content=None):
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
        self.Dg = networkx.DiGraph()
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
        self.graph()

    def possible_turns(self, WantRow, WantColumn):
        if WantRow == self.height - 1 and WantColumn == self.width - 1:
            return [[0, -1], [-1, -1], [-1, 0]]

        if self.height - 1 > WantRow > 0 and self.width - 1 > WantColumn > 0:
            return [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]

        if self.height - 1 > WantRow > 0 and WantColumn == 0:
            return [[-1, 0], [-1, 1], [0, 1], [1, 1], [1, 0]]

        if 0 < WantRow < self.height - 1 and WantColumn == self.width - 1:
            return [[-1, 0], [-1, -1], [0, -1], [1, -1], [1, 0]]

        if self.width - 1 > WantColumn > 0 and WantRow == 0:
            return [[0, -1], [1, -1], [1, 0], [1, 1], [0, 1]]

        if 0 < WantColumn < self.width - 1 and self.height - 1 == WantRow:
            return [[0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 1]]

        if WantRow == 0 and WantColumn == 0:
            return [[0, 1], [1, 1], [1, 0]]

        if WantRow == 0 and WantColumn == self.width - 1:
            return [[0, -1], [1, -1], [1, 0]]

        if WantRow == self.height - 1 and WantColumn == 0:
            return [[-1, 0], [-1, 1], [0, 1]]

    def graph(self):
        for row in range(self.height):
            for col in range(self.width):
                if self.field[row][col].content is None or type(
                        self.field[row][col].content).__name__ == 'Player':
                    posibilities = self.possible_turns(row, col)
                    for turn in posibilities:
                        if self.field[row + turn[0]][col + turn[1]].content is None:
                            if turn[0] and turn[1]:
                                pass
                            else:
                                self.Dg.add_edge(str(row) + ',' + str(col),
                                                 str(row + turn[0]) + ',' + str(col + turn[1]))

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

    def get_click(self, event):
        cell = self.get_cell(event.pos)

        if cell is not None:
            self.on_click(cell, event.button)

    def get_cell(self, mouse_pos):
        if not (Field.margin_left <= mouse_pos[
            0] <= Field.margin_left + self.width * tile_width) or not (
                Field.margin_top <= mouse_pos[
            1] <= Field.margin_top + self.height * tile_height) or not (
                mouse_pos[0] < Field.size_in_pixels[0] and mouse_pos[1] < Field.size_in_pixels[1]):
            return None
        return (mouse_pos[1] - Field.margin_top) // tile_height, (
                mouse_pos[0] - Field.margin_left) // tile_width  # row col

    def on_click(self, cell, action):
        global sel_her_col, sel_her_row, last_row, last_col, selected_hero
        if action == 1 and selected_hero is not None:
            path = []
            if (last_row, last_col) == cell:
                # Убираем стрелочки
                arrow_sprites.empty()
                # TODO: Анимация передвижения героев (путь строится, стрелочки рисуются)
            else:
                # Убираем старые стрелочки
                arrow_sprites.empty()
                # Рисуем стрелочки
                last_row, last_col = cell
                path = networkx.shortest_path(self.Dg, str(sel_her_row) + ',' + str(sel_her_col),
                                              str(last_row) + ',' + str(last_col), weight=1)
                path = list(map(lambda x: list(map(int, x.split(','))), path))
                for i, (row, col) in enumerate(path[1:-1], 1):
                    prev_row, prev_col = path[i - 1]
                    next_row, next_col = path[i + 1]
                    # Определяем направление стрелочки
                    if prev_row == next_row:
                        if prev_col < next_col:
                            direction = "right"
                        else:
                            direction = "left"
                    elif prev_col == next_col:
                        if prev_row < next_row:
                            direction = "down"
                        else:
                            direction = "top"
                    elif prev_row < next_row:
                        if next_row == row:
                            if prev_col < next_col:
                                direction = "top-to-right"
                            elif prev_col > next_col:
                                direction = "top-to-left"
                        elif next_col == col:
                            if prev_col < next_col:
                                direction = "left-to-down"
                            if prev_col > next_col:
                                direction = "right-to-down"
                    else:
                        if next_row == row:
                            if prev_col < next_col:
                                direction = "down-to-right"
                            else:
                                direction = "down-to-left"
                        elif next_col == col:
                            if prev_col < next_col:
                                direction = "left-to-top"
                            else:
                                direction = "right-to-top"
                    Arrow(direction, row, col)
                Arrow("goal", *path[-1])


        elif action == 3:
            if type(self.field[cell[0]][cell[1]].content).__name__ == 'Player':
                sel_her_row, sel_her_col = cell[0], cell[1]
                selected_hero = self.field[cell[0]][cell[1]].content
                print(f'selected hero: {selected_hero}')
        # print(sel_her_row, sel_her_col, last_row, last_col)


# Здесь нужно сделать всё по красоте, чтобы он наследовался от спрайта и рисовался во время битвы,
# ведь я всего лишь бэкэнд - лох, а ты фронтенд гений!!! TODO
# Ещё должен быть метод, который зеркалит спрайт юнита (надо тебе же для Fight)
class Unit:
    def __init__(self, name, attack, defence, min_dmg, max_dmg, count, speed, hp, team, shoot):
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
        damage = random.randint(self.min_dmg, self.max_dmg) * (self.cur_atc / enemy.cur_dfc) * (
                self.count + 1)
        enemy.get_rat_damage(damage)

    def attack_hon(self, enemy):
        damage = random.randint(self.min_dmg, self.max_dmg) * (self.cur_atc / enemy.cur_dfc) * (
                self.count + 1)
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
                random.randint(self.min_dmg, self.max_dmg) * (self.cur_atc / attacker.cur_dfc) * (
                        self.count + 1))
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


class Fight:  # TODO
    coor_row = [0, 1, 3, 4, 5, 7, 8]
    null_unit = Unit("", 0, 0, 0, 0, 0, 0, 0, "", False)

    def __init__(self, left_hero, right_hero):
        self.board = [[0] for _ in range(10)] * 9
        self.turn_queue = left_hero.army + right_hero.army

        for num in range(len(left_hero.army)):
            if left_hero.army[num] != Fight.null_unit:
                self.board[Fight.coor_row[num]][0] = left_hero.army[num]

        for num in range(len(right_hero.army)):
            if right_hero.army[num] != Fight.null_unit:
                self.board[Fight.coor_row[num]][9] = right_hero.army[num]


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
    null_unit = Unit("", 0, 0, 0, 0, 0, 0, 0, "", False)
    moving_animation = itertools.cycle([load_image(f'heroes/default/{i}.png') for i in range(
        len([name for name in os.listdir('data/images/heroes/default')]) - 1)])

    def __init__(self, pos_y, pos_x, team):
        super().__init__(player_sprites)
        self.team = team
        self.image = pygame.transform.scale(self.image, (tile_width, tile_height))
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
        self.movepoints = 2000

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
            self.inventory[self.inventory.index(Player.null_item)] = Item(
                *other.stats())  # Что-то типа заглушки,
            # которая превращает предмет, который лежит на полу в предмет, который в инвентаре героя TODO * 3

        elif type(other).__name__ == 'build':
            if other.variety != 'town':  # Опять заглушка
                d_atc, d_dfc, d_features = other.visit
                self.atc, self.dfc = self.atc + d_atc, self.dfc + d_dfc
                for key, val in d_features.items():
                    self.bonus[key] += val

    # Два метода заглушки, которые ещё рано реализовывать, так как на карте даже двух героев то нет,
    # а тут их взаимодействия и эт фронт уже (твоя работа), так что я иду нахуй Соре
    # Тут наверно придется класс Fight писать TODO * 2
    def fight(self, other):
        Fight(self, other)
        pass

    def meet(self, other):
        pass

    def update(self, updating_type='', *args):
        if updating_type:
            if updating_type == 'moving':
                self.image = next(self.moving_animation)
                self.rect.move(*args)
            # ... other types
            else:
                raise Exception(f'incorrect updating_type: {updating_type}')


class Tile(pygame.sprite.Sprite):
    tile_images = {
        'grass': load_image("grass.png"),
        'rock': load_image("rock.png", -1),
        'coins': load_image("coins.png"),
    }

    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(tile_sprites)
        self.image = pygame.transform.scale(Tile.tile_images[tile_type], (tile_width, tile_height))
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Arrow(pygame.sprite.Sprite):
    top_to_right = load_image("from-top-to-right-arrow.png")
    left_to_right = load_image("from-left-to-right-arrow.png")
    goal = load_image("goal.png")

    def __init__(self, direction, pos_y, pos_x):
        super().__init__(arrow_sprites)
        if direction == 'goal':
            self.image = Arrow.goal
        elif direction == 'top-to-right':
            self.image = Arrow.top_to_right
        elif direction == 'right':
            self.image = Arrow.left_to_right
        elif direction == 'left':
            self.image = pygame.transform.flip(Arrow.left_to_right, True, False)
        elif direction == 'top':
            self.image = pygame.transform.rotate(Arrow.left_to_right, 90)
        elif direction == 'down':
            self.image = pygame.transform.rotate(Arrow.left_to_right, -90)
        elif direction == 'top-to-right':
            self.image = Arrow.top_to_right
        elif direction == 'right-to-down':
            self.image = pygame.transform.rotate(Arrow.top_to_right, -90)
        elif direction == 'down-to-left':
            self.image = pygame.transform.rotate(Arrow.top_to_right, 180)
        elif direction == 'left-to-top':
            self.image = pygame.transform.rotate(Arrow.top_to_right, 90)
        elif direction == 'top-to-left':
            self.image = pygame.transform.flip(Arrow.top_to_right, True, False)
        elif direction == 'left-to-down':
            self.image = pygame.transform.rotate(
                pygame.transform.flip(Arrow.top_to_right, False, True), -90)
        elif direction == 'down-to-right':
            self.image = pygame.transform.flip(Arrow.top_to_right, False, True)
        elif direction == 'right-to-top':
            self.image = pygame.transform.rotate(
                pygame.transform.flip(Arrow.top_to_right, True, True), 180)
        else:
            raise Exception(f'incorrect Arrow direction: {direction}')
        self.image = pygame.transform.scale(self.image, (tile_width, tile_height))
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


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

    start_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight * 4) // 2,
                          bwidth, bheight)
    start_button.set_background_image('button-background.jpg')
    font = pygame.font.Font(None, 80)
    start_button.set_text("Start", font, pygame.Color(156, 130, 79))
    start_button.render()

    settings_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight) // 2,
                             bwidth,
                             bheight)
    settings_button.set_background_image('button-background.jpg')
    font = pygame.font.Font(None, 80)
    settings_button.set_text("Settings", font, pygame.Color(156, 130, 79))
    settings_button.render()

    exit_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT + bheight * 2) // 2,
                         bwidth,
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
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 or event.button == 3:
                field.get_click(event)
    all_sprites.draw(screen)
    tile_sprites.draw(field.space)
    arrow_sprites.draw(field.space)
    player_sprites.draw(field.space)
    screen.blit(field.space, (Field.margin_right, Field.margin_top))
    pygame.display.flip()
    clock.tick(FPS)
