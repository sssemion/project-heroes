import itertools
import os
import random
import sys

import networkx
import pygame

GREEN, RED, BLUE, YELLOW = 'green', 'red', 'blue', 'yellow'
selected_hero, current_color = None, GREEN
sel_her_row, sel_her_col = None, None
last_row, last_col = -1, -1
N = 2  # tmp

pygame.init()
screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()
FPS = 60
running = True

tile_width = tile_height = 50


class Camera:
    def __init__(self, field):
        self.rows, self.cols = 0, 0
        self.field = field

    def get_x_shift(self):
        return self.cols * tile_width

    def get_y_shift(self):
        return self.rows * tile_height

    def set_rows(self, rows):
        self.rows = rows

    def set_cols(self, cols):
        self.cols = cols

    def upper(self, delta=1):
        self.rows -= delta
        self.rows = max(-1, self.rows)

    def lower(self, delta=1):
        self.rows += delta
        self.rows = min(self.field.height - 1, self.rows)

    def left(self, delta=1):
        self.cols -= delta
        self.cols = max(-1, self.cols)

    def right(self, delta=1):
        self.cols += delta
        self.cols = min(self.field.width - 1, self.cols)


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
house_sprites = pygame.sprite.Group()

fon = pygame.transform.scale(load_image('background.jpg'), (WIDTH, HEIGHT))


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

    def stats(self):
        return self.name, self.d_atc, self.d_dfc, self.description, self.feature


class Unit(pygame.sprite.Sprite):
    def __init__(self, image, name, attack, defence, min_dmg, max_dmg, count, speed, hp):
        super().__init__(unit_sprites)
        self.image = load_image(image)
        self.dead = 0
        self.counter = True
        self.top_hp = hp
        self.count, self.name, self.atc, self.dfc, self.min_dmg, self.max_dmg, self.spd, self.hp = \
            count, name, attack, defence, min_dmg, max_dmg, speed, hp
        self.cur_atc, self.cur_dfc, self.cur_spd, self.cur_hp, self.cur_top_hp = \
            attack, defence, speed, hp, hp

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

    def __add__(self, other):
        self.count += other.count


# Библитека предметов
ITEMS = {
    'club': Item('Дубина', 2, 0, "Мощная, но неудобная дубина огра", 'weapon', 'club'),
    'darksword': Item('Зловещий меч', 4, 0, "Постаревший от времени меч мертвеца", 'weapon',
                      'darksword'),
    'mace': Item('Кистень', 8, 0, "Сделанный на славу кистень", 'weapon', 'mace'),
    'titansword': Item('Меч титана', 12, -3, "Тяжелый меч, которым сложно защищаться", 'weapon',
                       'titansword'),

    'poorshield': Item('Щит бедняка', 0, 2, "Щит мертвого оборванца", 'shield', 'poorshield'),
    'darkshield': Item('Щит мертвеца', 0, 4, "Ржавый щит, украшенный черепом", 'shield',
                       'darkshield'),
    'ironshield': Item('Щит 1000 гномьих судеб', 0, 8, "Щит, над которым старлся город гномов",
                       'shield', 'ironshield'),
    'bestshield': Item('Щит печально павшего воина', -3, 12, "Щит последнего воина", 'shield',
                       'bestshield'),

    'crownhelm': Item('Корона', 0, 2, "Корона, которая лучше смотрится на королях", 'helm',
                      'crownhelm'),
    'darkhelm': Item('Мертвецкий шлем', 0, 4, "Шлем умершего короля мертвых", 'helm', 'darkhelm'),
    'skullhelm': Item('Шлем-череп', 8, -2, "Проклятый (?) богами шлем", 'helm', 'skullhelm'),
    'hornhelm': Item('Шлем стада единорогов', 10, 8, "Шлем с трофеями стального единорога", 'helm',
                     'hornhelm'),

    'darkboots': Item('Боты обмана', -2, -6, "Ботинки обманщика-марафонца", 'boots', 'darkboots',
                      {'bonus_move': 500}),
    'saintboots': Item('Сандали Мироздателя', 4, 4, "Сандали Мироздателя", 'boots', 'saintboots'),
    'speedboots': Item('Скороходы', 0, 0, "Ботинки из душ лошадей", 'boots', 'speedboots',
                       {'bonus_move': 1500}),
    'boneboots': Item('Ботинки погребенных', 2, 2, "Поножи из костей невинных рабов", 'boots',
                      'boneboots'),

    'poorchest': Item('Школьный нагрудник', 2, 6, "Нагрудник ученика школы наездников", 'chest',
                      'poorchest'),
    'firechest': Item('Кираса огня', 4, 9, "Кираса адского пламени", 'chest', 'firechest'),
    'goldchest': Item('Праздничный наряд', 8, 14, "Торжественное одеяние циклопов по праздникам",
                      'chest', 'goldchest'),
    'titanchest': Item('Титаноывй нагрудник', 12, 20, "Нагрудник Герерала Титанов", 'chest',
                       'titanchest'),

    'speedglove': Item('Конные перчатки', 0, 0, "Перчатки скорой дикости", 'other', 'glovespeed',
                       {'bonus_move': 500}),
    'rib': Item('Лента дипломата', 0, 0, "Лента дипломата. Все идут за вами", 'other', 'rib',
                {'sale': 1}),
    'costring': Item('Лента дипломата', 0, 0, "Кольцо дипломата. Все идут за вами", 'other',
                     'ringcost', {'sale': 1}),
}

# Библиотека юнитов
UNITS = {
    'angel': Unit("units/angel.png", "Ангел", 13, 13, 50, 50, 1, 10, 250),
    'fire': Unit("units/fire.png", "Огенный элементаль", 15, 10, 50, 50, 1, 10, 250),
    'horn': Unit("units/horn.png", "Единорог", 12, 9, 50, 50, 1, 10, 250),
    'cyclope': Unit("units/cyclope.png", "Циклоп", 10, 9, 50, 50, 1, 10, 250),

    'pegas': Unit("units/pegas.png", "Пегас", 10, 10, 20, 30, 1, 12, 50),
    'ogre': Unit("units/ogre.png", "Огр", 8, 10, 25, 40, 1, 6, 120),
    'swordsman': Unit("units/swordsman.png", "Крестоносец", 9, 9, 30, 45, 1, 8, 90),
    'earth': Unit("units/earth.png", "Земляной элементаль", 7, 7, 15, 50, 1, 5, 80),

    'air': Unit("units/air.png", "Воздушный элемнатль", 5, 5, 10, 20, 1, 7, 20),
    'goblin': Unit("units/goblin.png", "Гоблин", 7, 1, 15, 30, 1, 9, 15),
    'gnom': Unit("units/gnom.png", "Гном", 3, 6, 50, 50, 1, 4, 30),
    'pikeman': Unit("units/pikeman.png", "Копейщик", 2, 4, 10, 15, 1, 8, 40),
}

HOUSES = {
    'hair': (UNITS['air'], 1, 8),
    'hangel': (UNITS['angel'], 5, 1),
    'hcyclope': (UNITS['cyclope'], 5, 1),
    'hearth': (UNITS['earth'], 3, 4),
    'hfire': (UNITS['fire'], 5, 8),
    'hgnom': (UNITS['gnom'], 1, 8),
    'hgoblin': (UNITS['goblin'], 1, 8),
    'hhorn': (UNITS['horn'], 5, 1),
    'hogre': (UNITS['ogre'], 3, 4),
    'hpegas': (UNITS['pegas'], 3, 4),
    'hpikeman': (UNITS['pikeman'], 1, 6),
    'hswordsman': (UNITS['swordsman'], 3, 4),
}


class Block:  # Предмет, блокирующий проход
    def __init__(self, tile_type='rock'):
        self.tile_type = tile_type

    def render(self, x, y):
        Tile(self.tile_type, x, y)


class Cell:  # Ячейка поля Field
    def __init__(self, cost=100, tile_type='grass', content=None, building=None):
        self.cost = cost  # cost - стоимость передвижения по клетке
        self.tile_type = tile_type
        self.content = content  # content - содержимое ячейки (None, экземпляр класса Block или любой другой объект)
        self.building = building

    def get_cost(self):
        return self.cost

    def is_blocked(self):
        return type(self.content).__name__ == 'Block'

    def get_content(self):
        return self.content

    def get_building(self):
        return self.building

    def render(self, x, y):
        Tile(self.tile_type, x, y)
        try:
            self.content.render(x, y)
        except AttributeError:
            pass

    def get_minimap_color(self):
        if self.building is not None:
            return 0x331a00
        elif self.content is None:
            return 0x008000
        elif type(self.content).__name__ == "Item":
            return 0xffd700
        elif type(self.content).__name__ == "Player":
            return 0xff0000
        elif type(self.content).__name__ == "Block":
            return 0x454545
        else:
            return 0


class ControlPanel:  # Панель управления в правой части экрана
    width = 200  # px
    backgroung = pygame.transform.scale(load_image("control-panel-background.jpg"), (width, HEIGHT))

    def __init__(self, field, cam):
        self.field = field
        self.cam = cam
        self.surface = pygame.Surface((self.width, HEIGHT))
        self.surface.blit(self.backgroung, (0, 0))
        self.render_minimap()

    def draw(self):
        map = self.render_minimap()
        self.surface.blit(map, ((self.width - map.get_width()) // 2, 8))
        screen.blit(self.surface, (WIDTH - self.width, 0))

    def render_minimap(self):
        width, height = self.field.width, self.field.height
        frame_size = 2
        cell_size = min((self.width - 16) // width, 250 // height)
        w, h = cell_size * width + frame_size * 2, cell_size * height + frame_size * 2
        surface = pygame.Surface((w, h))
        for row in range(height):
            for col in range(width):
                color = self.field.field[row][col].get_minimap_color()
                pygame.draw.rect(surface, color, (cell_size * col + frame_size,
                                                  cell_size * row + frame_size,
                                                  cell_size, cell_size))

        # обозначаем область, видимую на экране
        pygame.draw.rect(surface, 0xff0000, (self.cam.cols * cell_size + frame_size,
                                             self.cam.rows * cell_size + frame_size,
                                             cell_size * self.field.col_count,
                                             cell_size * self.field.row_count), 1)

        # рисуем рамочку
        pygame.draw.rect(surface, 0xe7daae, (0, 0, w - 1, h - 1), 2)
        return surface


class Field:  # Игровое поле
    size_in_pixels = WIDTH - ControlPanel.width, HEIGHT
    margin_top = int(14 / 732 * size_in_pixels[1])
    margin_right = int(13 / 1171 * size_in_pixels[0])
    margin_left = int(15 / 1171 * size_in_pixels[0])
    margin_bottom = int(16 / 732 * size_in_pixels[1])

    # сколько строк и столбцов помещается на экране
    row_count = (size_in_pixels[1] - margin_top - margin_bottom) // tile_height
    col_count = (size_in_pixels[0] - margin_left - margin_right) // tile_width

    def __init__(self, filename, number_of_players=1):
        self.Dg = networkx.DiGraph()
        filename = "data/maps/" + filename
        with open(filename, 'r') as mapFile:
            level_map = [list(map(str.strip, line.split(';'))) for line in mapFile]
        max_width = max(map(len, level_map))
        # дополняем каждую строку пустыми клетками ('.')
        self.field = list(map(lambda x: x + ['.'] * (max_width - len(x)), level_map))
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
                if (not self.field[row][col].is_blocked()) or type(
                        self.field[row][col].content).__name__ == 'Player':
                    posibilities = self.possible_turns(row, col)
                    for turn in posibilities:
                        if not self.field[row + turn[0]][col + turn[1]].is_blocked():
                            if turn[0] and turn[1]:
                                pass
                            else:
                                self.Dg.add_edge(str(row) + ',' + str(col),
                                                 str(row + turn[0]) + ',' + str(col + turn[1]))

    def render(self):
        self.frame = pygame.transform.scale(load_image('frame.png'), Field.size_in_pixels)
        screen.blit(self.frame, (0, 0))
        self.space = pygame.Surface((self.width * tile_width,
                                     self.height * tile_height))

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
                    self.field[x][y] = Cell(content=ITEMS['club'])
                elif self.field[x][y] in HOUSES:
                    self.field[x][y] = Cell(building=House(x, y, self.field[x][y] + '.png', *HOUSES[self.field[x][y]]))
                self.field[x][y].render(x, y)

    def get_click(self, event):
        cell = self.get_cell(event.pos)

        if cell is not None:
            self.on_click(cell, event.button)

    def get_cell(self, mouse_pos):
        x_shift = min(0, cam.get_x_shift())
        y_shift = min(0, cam.get_y_shift())
        if not (Field.margin_left <= mouse_pos[
            0] + x_shift <= Field.margin_left + self.width * tile_width) or \
                not (Field.margin_top <= mouse_pos[
                    1] + y_shift <= Field.margin_top + self.height * tile_height) or \
                not (mouse_pos[0] < Field.size_in_pixels[0] and mouse_pos[1] < Field.size_in_pixels[
                    1]):
            return None
        return (mouse_pos[1] - Field.margin_top + cam.get_y_shift()) // tile_height, (
                mouse_pos[0] - Field.margin_left + cam.get_x_shift()) // tile_width  # row col

    def on_click(self, cell, action):
        global sel_her_col, sel_her_row, last_row, last_col, selected_hero, path
        if action == 1 and selected_hero is not None:
            if selected_hero.get_pos() == cell[::-1]:
                return
            if (last_row, last_col) == cell:
                # Убираем стрелочки
                arrow_sprites.empty()

                for row, col in path[1:]:

                    prev_col, prev_row = selected_hero.get_pos()
                    k = 7  # Коэфиициент скорости движения
                    drow = (row - prev_row) * k  # delta rows (in pixels)
                    dcol = (col - prev_col) * k  # delta cols (in pixels)
                    if dcol:
                        selected_hero.set_reversed(dcol < 0)
                    prev_row *= tile_height
                    prev_col *= tile_width
                    while not (row * tile_height - abs(drow) <= prev_row
                               <= row * tile_height + abs(drow) and
                               col * tile_width - abs(dcol) <= prev_col
                               <= col * tile_width + abs(dcol)):
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT or (
                                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                                terminate()
                        prev_row += drow
                        prev_col += dcol
                        selected_hero.update('moving', dcol, drow)

                        tile_sprites.draw(self.space)
                        house_sprites.draw(self.space)
                        player_sprites.draw(self.space)
                        screen.blit(self.space, (Field.margin_right - cam.get_x_shift(),
                                                 Field.margin_top - cam.get_y_shift()))
                        self.draw_frame()
                        pygame.display.flip()
                        clock.tick(FPS)
                    selected_hero.move(col, row)

                    # Взаимодейтсвие с предметами
                    content = self.field[row][col].get_content()
                    building = self.field[row][col].get_building()
                    if content is not None:
                        selected_hero.interact(content)
                    if building is not None:
                        selected_hero.interact(building)
                    self.field[row][col].content = selected_hero
                    self.field[sel_her_row][sel_her_col].content = None
                    sel_her_col, sel_her_row = selected_hero.get_pos()

                    # Двигаем камеру при необходимости
                    if sel_her_row - cam.rows < 3:
                        cam.upper(3 - (sel_her_row - cam.rows))
                    elif sel_her_row - cam.rows > Field.row_count - 3:
                        cam.lower(sel_her_row - cam.rows - (Field.row_count - 3))
                    if sel_her_col - cam.cols < 3:
                        cam.left(3 - (sel_her_col - cam.cols))
                    elif sel_her_col - cam.cols > Field.col_count - 3:
                        cam.right(sel_her_col - cam.cols - (Field.col_count - 3))

                    screen.blit(black_texture, (0, 0))
                    screen.blit(self.space, (Field.margin_right - cam.get_x_shift(),
                                             Field.margin_top - cam.get_y_shift()))
                    self.draw_frame()
                    control_panel.draw()
                    pygame.display.flip()
                    clock.tick(FPS)

                selected_hero.image = selected_hero.default_image

            else:
                # Убираем старые стрелочки
                arrow_sprites.empty()
                # Рисуем стрелочки
                previous_cell_backup = last_row, last_col  # На случай если в клетку не удастся попасть
                last_row, last_col = cell
                try:
                    path = networkx.shortest_path(self.Dg, str(sel_her_row) + ',' + str(sel_her_col),
                                                  str(last_row) + ',' + str(last_col), weight=1)
                except networkx.NetworkXNoPath:
                    last_row, last_col = previous_cell_backup
                    return
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
                last_row, last_col = -1, -1
        # print(sel_her_row, sel_her_col, last_row, last_col)

    def draw_frame(self):  # перерисовывает рамочку вокруг поля
        screen.blit(self.frame, (0, 0))


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
        self.surface.blit(
            pygame.transform.scale(load_image('fight-background.jpg'), (width, height)), (0, 0))

    def draw_cells(self):
        self.rows = len(self.board)
        self.cols = len(self.board[0])
        self.cell_width = (
                                  self.width - FightBoard.margin_left - FightBoard.margin_right) // self.cols
        self.cell_height = (
                                   self.height - FightBoard.margin_top - FightBoard.margin_bottom) // self.rows
        cells_surface = pygame.Surface(
            (self.width - FightBoard.margin_left - FightBoard.margin_right + 2,
             self.height - FightBoard.margin_top - FightBoard.margin_bottom + 2))
        for i in range(self.rows + 1):
            pygame.draw.line(cells_surface, 0xffffff, (0, i * self.cell_height),
                             (self.width - FightBoard.margin_right - FightBoard.margin_left,
                              i * self.cell_height), 2)
        for i in range(self.cols + 1):
            pygame.draw.line(cells_surface, 0xffffff, (i * self.cell_width, 0),
                             (i * self.cell_width,
                              self.height - FightBoard.margin_top - FightBoard.margin_bottom), 2)
        cells_surface.set_colorkey(0x000000)
        cells_surface.set_alpha(128)
        self.surface.blit(cells_surface, (FightBoard.margin_right, FightBoard.margin_top))

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)

    def get_cell(self, mouse_pos):
        if not (FightBoard.margin_left <= mouse_pos[
            0] <= FightBoard.margin_left + self.width * self.cell_width) or not (
                FightBoard.margin_top <= mouse_pos[
            1] <= FightBoard.margin_top + self.height * self.cell_height):
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
                                                 (HeroFightScreen.width, HeroFightScreen.height)),
                          (0, 0))
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


def fight(left_hero, right_hero):
    coor_row = [0, 1, 3, 4, 5, 7, 8]
    null_unit = Unit("player.png", "", 0, 0, 0, 0, 0, 0, 0)
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
    screen.blit(left_hero_screen.surface,
                (topleft_coord[0] - HeroFightScreen.width - 5, topleft_coord[1]))

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


class Player(pygame.sprite.Sprite):
    default_image = pygame.transform.scale(load_image('player.png', -1), (tile_width, tile_height))
    null_item = Item("", 0, 0, "all", "")
    null_unit = Unit("player.png", "", 0, 0, 0, 0, 0, 0, 0)
    moving_animation = itertools.cycle(
        [pygame.transform.scale(load_image(f'heroes/default/{i}.png'), (tile_width, tile_height)) for
         i in range(len([name for name in os.listdir('data/images/heroes/default')]) - 1)])
    animation_counter = 0

    def __init__(self, pos_y, pos_x, team):
        super().__init__(player_sprites)
        self.team = team
        self.image = self.default_image.copy()
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
        self.bonus = {'sale': 1, 'd_hp': 0, 'bonus_move': 0, 'd_spd': 0}
        self.army = [Player.null_unit] * 7
        self.movepoints = 2000

    def move(self, x, y):
        self.pos = x, y
        self.rect = self.image.get_rect().move(tile_width * x, tile_height * y)

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
        if type(other).__name__ == 'Player':
            if other.team != self.team:
                fight(self, other)
        elif type(other).__name__ == 'Item':
            if Player.null_item in self.inventory:
                self.inventory[self.inventory.index(Player.null_item)] = other
                row, col = self.get_pos()[::-1]
                field.field[row][col].content = None
                field.field[row][col].render(row, col)
        elif type(other).__name__ == 'build':
            if other.variety != 'town':  # Опять заглушка
                d_atc, d_dfc, d_features = other.visit
                self.atc, self.dfc = self.atc + d_atc, self.dfc + d_dfc
                for key, val in d_features.items():
                    self.bonus[key] += val
        elif type(other).__name__ == 'House':
            other.visit(self)

    def get_characteristics(self):
        return self.atc, self.dfc

    def render(self, *args):  # рисует кружочек возле героя чтобы различать разные команды
        x, y = self.get_pos()
        pygame.draw.ellipse(self.image, pygame.color.Color(self.team),
                            pygame.Rect(int(tile_width * 0.35),
                                        int(tile_height * 0.75),
                                        int(tile_width * 0.3),
                                        int(tile_height * 0.2)))

    def update(self, updating_type='', *args):
        if updating_type:
            if updating_type == 'moving':
                if not self.animation_counter:
                    self.image = next(self.moving_animation)
                self.animation_counter += 1
                self.animation_counter %= 5
                self.rect = self.rect.move(*args)
            # ... other types
            else:
                raise Exception(f'incorrect updating_type: {updating_type}')

    def set_reversed(self, reversed):
        self.moving_animation = itertools.cycle(
            [pygame.transform.flip(
                pygame.transform.scale(load_image(f'heroes/default/{i}.png'),
                                       (tile_width, tile_height)),
                reversed, False) for i in
                range(len([name for name in os.listdir('data/images/heroes/default')]) - 1)])


class House(pygame.sprite.Sprite):
    def __init__(self, row, col, image_name, unit, cost, delta):
        self.unit, self.cost, self.delta = unit, cost, delta
        super().__init__(house_sprites)
        self.image = pygame.transform.scale(load_image("homes/" + image_name),
                                            (tile_width, tile_height))
        self.rect = self.image.get_rect().move(col * tile_width, row * tile_height)

    def visit(self, visitor: Player):
        # Сохраняем основной экран и затемняем его
        screen_save = screen.copy()
        black = pygame.Surface((WIDTH, HEIGHT))
        black.fill(pygame.color.Color(0, 0, 0))
        black.set_alpha(200)
        screen.blit(black, (0, 0))

        # Создаем экран взаимодействия
        width, height = int(WIDTH / 2.5), int(HEIGHT / 3)
        topleft_coord = ((WIDTH - width) // 2, (HEIGHT - height) // 2)
        surface = pygame.Surface((width, height))
        surface.blit(fon, (-100, -100))
        font_name = pygame.font.Font('data/HoMMFontCyr.ttf', 26)
        font_aff = pygame.font.Font('data/HoMMFontCyr.ttf', 20)
        name = font_name.render(f"Жилище {self.unit.name}", 10, (156, 130, 79))
        afford = font_aff.render(f"Желаете купить {self.delta} {self.unit.name} за {self.cost} золота?", 10,
                                 (156, 130, 79))
        button_agree = Button()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        screen.blit(screen_save, (0, 0))
                        return
            surface.blit(name, (10, 10))
            surface.blit(afford, (10, 60))
            screen.blit(surface, topleft_coord)
            pygame.display.flip()
            clock.tick(FPS)


class Tile(pygame.sprite.Sprite):
    tile_images = {
        'bestshield': load_image("items/bestshield-floor.png", -1),
        'boneboots': load_image("items/boneboots-floor.png", -1),
        'club': load_image("items/club-floor.png", -1),
        'costrib': load_image("items/rib-floor.png", -1),
        'costring': load_image("items/ringcost-floor.png", -1),
        'crownhelm': load_image("items/crownhelm-floor.png", -1),
        'darkboots': load_image("items/darkboots-floor.png", -1),
        'darkhelm': load_image("items/darkhelm-floor.png", -1),
        'darkshield': load_image("items/darkshield-floor.png", -1),
        'darksword': load_image("items/darksword-floor.png"),
        'firechest': load_image("items/firechest-floor.png", -1),
        'goldchest': load_image("items/goldchest-floor.png", -1),
        'hornhelm': load_image("items/hormhelm-floor.png", -1),
        'ironshield': load_image("items/ironshield-floor.png", -1),
        'mace': load_image("items/mace-floor.png", -1),
        'poorchest': load_image("items/poorchest-floor.png", -1),
        'poorshield': load_image("items/poorshield-floor.png", -1),
        'saintboots': load_image("items/saintboots-floor.png", -1),
        'skullhelm': load_image("items/skullhelm-floor.png", -1),
        'speedboots': load_image("items/speedboots-floor.png", -1),
        'speedglove': load_image("items/glovespeed-floor.png", -1),
        'titanchest': load_image("items/titanchest-floor.png", -1),
        'titansword': load_image("items/titansword-floor.png", -1),
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
                pygame.transform.flip(Arrow.top_to_right, True, False), -90)
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
    screen.blit(fon, (0, 0))

    bwidth, bheight = 400, 80

    font = pygame.font.Font(None, 80)

    start_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight * 4) // 2,
                          bwidth, bheight)
    start_button.set_background_image('button-background.jpg')
    start_button.set_text("Start", font, pygame.color.Color(156, 130, 79))
    start_button.render()

    settings_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT - bheight) // 2,
                             bwidth,
                             bheight)
    settings_button.set_background_image('button-background.jpg')
    settings_button.set_text("Settings", font, pygame.color.Color(156, 130, 79))
    settings_button.render()

    exit_button = Button(button_sprites, screen, (WIDTH - bwidth) // 2, (HEIGHT + bheight * 2) // 2,
                         bwidth,
                         bheight, terminate)
    exit_button.set_background_image('button-background.jpg')
    exit_button.set_text("Exit", font, pygame.color.Color(32, 32, 32))
    exit_button.render()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                terminate()
            if start_button.clicked or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                return
            button_sprites.update(event)
        pygame.display.flip()
        clock.tick(FPS)


start_screen()  # Main menu
screen.fill(0xff0000)
field = Field("example.txt", N)  # Игровое поле
cam = Camera(field)
control_panel = ControlPanel(field, cam)
black_texture = pygame.transform.scale(load_image('black-texture.png'), (WIDTH, HEIGHT))
up_counter, down_counter, left_counter, right_counter = [None] * 4
ctrl_pressed = False
hold_timeout = 5  # задержка после зажатия кнопки
hold_speed = 30  # задержка между повторениями зажатых кнопок

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            terminate()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LCTRL:
                ctrl_pressed = True
            if event.key == pygame.K_UP:
                up_counter = -hold_timeout  # Устанавливаем задержку по врмемни
                # на циклическое повторение при зажатии
                cam.upper()  # Двигаем камеру
            if event.key == pygame.K_DOWN:
                down_counter = -hold_timeout
                cam.lower()
            if event.key == pygame.K_LEFT:
                left_counter = -hold_timeout
                cam.left()
            if event.key == pygame.K_RIGHT:
                right_counter = -hold_timeout
                cam.right()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LCTRL:
                ctrl_pressed = False
            if event.key == pygame.K_UP:
                up_counter = None
            if event.key == pygame.K_DOWN:
                down_counter = None
            if event.key == pygame.K_LEFT:
                left_counter = None
            if event.key == pygame.K_RIGHT:
                right_counter = None
            if event.key == pygame.KMOD_CTRL:
                ctrl_pressed = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 or event.button == 3:
                field.get_click(event)
            if event.button == 4:
                if ctrl_pressed:
                    cam.left()
                else:
                    cam.upper()
            if event.button == 5:
                if ctrl_pressed:
                    cam.right()
                else:
                    cam.lower()

    # Увеличиваем счетчик зажатых клавиш (если они зажаты)
    if up_counter is not None:
        up_counter += 1
        cam.upper(up_counter // hold_speed > 0)
    if down_counter is not None:
        down_counter += 1
        cam.lower(down_counter // hold_speed > 0)
    if left_counter is not None:
        left_counter += 1
        cam.left(left_counter // hold_speed > 0)
    if right_counter is not None:
        right_counter += 1
        cam.right(right_counter // hold_speed > 0)

    screen.blit(black_texture, (0, 0))

    # all_sprites.draw(screen)
    tile_sprites.draw(field.space)
    house_sprites.draw(field.space)
    arrow_sprites.draw(field.space)
    player_sprites.draw(field.space)
    screen.blit(field.space, (Field.margin_right - cam.get_x_shift(),
                              Field.margin_top - cam.get_y_shift()))
    field.draw_frame()
    control_panel.draw()
    pygame.display.flip()
    clock.tick(FPS)
