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
inputbox_sprites = pygame.sprite.Group()


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
        if self.slot == other.slot:
            return True
        return False

    def render(self, x, y):
        Tile(self.tile_type, x, y)

    def stats(self):
        return self.name, self.d_atc, self.d_dfc, self.description, self.feature


class Unit(pygame.sprite.Sprite):
    def __init__(self, image, name, attack, defence, min_dmg, max_dmg, count, speed, hp, key='null'):
        self.key_in_library = key
        super().__init__(unit_sprites)
        self.image_filename = image
        self.image = load_image(image)
        self.dead = 0
        self.counter = True
        self.top_hp = hp
        self.count, self.name, self.atc, self.dfc, self.min_dmg, self.max_dmg, self.spd, self.hp = \
            count, name, attack, defence, min_dmg, max_dmg, speed, hp
        self.cur_atc, self.cur_dfc, self.cur_spd, self.cur_hp, self.cur_top_hp = \
            attack, defence, speed, hp, hp
        self.rect = pygame.Rect(0, 0, 0, 0)

    def attack_rat(self, enemy):
        damage = random.randint(self.min_dmg, self.max_dmg) * (self.cur_atc / enemy.cur_dfc) * (
                self.count + 1)
        enemy.get_rat_damage(damage)

    def resize(self, width, height):
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect.width = width
        self.rect.height = height

    def set_rect(self, rect):
        self.rect = rect

    def move(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def reverse(self):
        self.image = pygame.transform.flip(self.image, True, False)

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

    def copy(self):
        return Unit(self.image_filename, self.name, self.atc, self.dfc, self.min_dmg, self.max_dmg, self.count, self.spd, self.hp)

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
        'null': pygame.Surface((0, 0)),
    }

    def __init__(self, tile_type, pos_y, pos_x):
        super().__init__(tile_sprites)
        self.image = pygame.transform.scale(Tile.tile_images[tile_type], (tile_width, tile_height))
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Map:
    def __init__(self, filename, name, description):
        self.filename = "data/maps/" + filename
        self.name = name
        self.description = description
        self.preview = None

    def load(self):
        with open(self.filename, 'r') as mapFile:
            level_map = [list(map(str.strip, line.split(';'))) for line in mapFile]
        max_width = max(map(len, level_map))
        # дополняем каждую строку пустыми клетками ('.')
        return list(map(lambda x: x + ['./'] * (max_width - len(x)), level_map))

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_preview(self, width, height):
        if self.preview is None or self.preview.get_size() != (width, height):
            field = self.load()
            w, h = len(field[0]), len(field)
            empty = pygame.Surface((width, height), flags=pygame.SRCALPHA)
            self.preview = pygame.Surface((w * tile_width, h * tile_height))
            for x in range(h):
                for y in range(w):
                    content, building = field[x][y].split('/')
                    self.preview.blit(pygame.transform.scale(Tile.tile_images["grass"],
                                                             (tile_width, tile_height)),
                                      (y * tile_width, x * tile_height))
                    if content == '#':
                        self.preview.blit(pygame.transform.scale(Tile.tile_images["rock"],
                                                                 (tile_width, tile_height)),
                                          (y * tile_width, x * tile_height))
                    elif content in ITEMS:
                        self.preview.blit(pygame.transform.scale(Tile.tile_images[ITEMS[content].tile_type],
                                                                 (tile_width, tile_height)),
                                          (y * tile_width, x * tile_height))
                    elif building in HOUSES:
                        self.preview.blit(pygame.transform.scale(load_image(os.path.join("homes", building + '.png')),
                                                                 (tile_width, tile_height)),
                                          (y * tile_width, x * tile_height))

            if w * tile_width / width > h * tile_height / height:
                self.preview = pygame.transform.scale(self.preview, (width, int(h * tile_height *
                                                                                (width / (
                                                                                        w * tile_width)))))
                empty.blit(self.preview, (0, (height - self.preview.get_height()) // 2))
            else:
                self.preview = pygame.transform.scale(self.preview, (int(w * tile_width * (height / (
                        h * tile_height))), height))
                empty.blit(self.preview, ((width - self.preview.get_width()) // 2, 0))
            self.preview = empty
        return self.preview


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

    'speedglove': Item('Конные перчатки', 0, 0, "Перчатки скорой дикости", 'other', 'speedglove',
                       {'bonus_move': 500}),
    'rib': Item('Лента дипломата', 0, 0, "Лента дипломата. Все идут за вами", 'other', 'rib',
                {'sale': 1}),
    'costring': Item('Лента дипломата', 0, 0, "Кольцо дипломата. Все идут за вами", 'other',
                     'costring', {'sale': 1}),
    'null': Item('', 0, 0, '', "all", "null"),
    'coins': Item('coins', 0, 0, '', 'coins'),
}

# Библиотека карт
MAPS = {
    'example': Map('example.txt', "Пример", "Просто карта для тестирования"),
}

# Библиотека юнитов
UNITS = {
    'angel': Unit("units/angel.png", "Ангел", 13, 13, 50, 50, 1, 10, 250, 'angel'),
    'fire': Unit("units/fire.png", "Огенный элементаль", 15, 10, 50, 50, 1, 10, 250, 'fire'),
    'horn': Unit("units/horn.png", "Единорог", 12, 9, 50, 50, 1, 10, 'horn'),
    'cyclope': Unit("units/cyclope.png", "Циклоп", 10, 9, 50, 50, 1, 10, 250, 'cyclope'),

    'pegas': Unit("units/pegas.png", "Пегас", 10, 10, 20, 30, 1, 12, 50, 'pegas'),
    'ogre': Unit("units/ogre.png", "Огр", 8, 10, 25, 40, 1, 6, 120, 'ogre'),
    'swordsman': Unit("units/swordsman.png", "Крестоносец", 9, 9, 30, 45, 1, 8, 90, 'swordsman'),
    'earth': Unit("units/earth.png", "Земляной элементаль", 7, 7, 15, 50, 1, 5, 80, 'earth'),

    'air': Unit("units/air.png", "Воздушный элемнатль", 5, 5, 10, 20, 1, 7, 20, 'air'),
    'goblin': Unit("units/goblin.png", "Гоблин", 7, 1, 15, 30, 1, 9, 15, 'goblin'),
    'gnom': Unit("units/gnom.png", "Гном", 3, 6, 50, 50, 1, 4, 30, 'gnom'),
    'pikeman': Unit("units/pikeman.png", "Копейщик", 2, 4, 10, 15, 1, 8, 40, 'pikeman'),
    'null': Unit("null.png", "", 0, 0, 0, 0, 0, 0, 0),
}

HOUSES = {
    'hair': (UNITS['air'], 1, 8, 'hair'),
    'hangel': (UNITS['angel'], 5, 1, 'hangel'),
    'hcyclope': (UNITS['cyclope'], 5, 1, 'hcyclope'),
    'hearth': (UNITS['earth'], 3, 4, 'hearth'),
    'hfire': (UNITS['fire'], 5, 1, 'hfire'),
    'hgnom': (UNITS['gnom'], 1, 8, 'hgnom'),
    'hgoblin': (UNITS['goblin'], 1, 8, 'hgoblin'),
    'hhorn': (UNITS['horn'], 5, 1, 'hhorn'),
    'hogre': (UNITS['ogre'], 3, 4, 'hogre'),
    'hpegas': (UNITS['pegas'], 3, 4, 'hpegas'),
    'hpikeman': (UNITS['pikeman'], 1, 6, 'hpikeman'),
    'hswordsman': (UNITS['swordsman'], 3, 4, 'hswordsman'),
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

    def __init__(self, save_slot):
        self.Dg = networkx.DiGraph()
        self.save_slot = save_slot

        file = open(os.path.join("data/saves/", f"{save_slot}.txt"), encoding='utf-8')
        self.game_name, self.map_name, self.names, *self.field = file.read().split('\n')
        file.close()

        self.field = [list(map(str.strip, line.split(';'))) for line in self.field]

        self.width = len(self.field[0])
        self.height = len(self.field)
        self.players = {}

        self.names = self.names.split(';')
        self.number_of_players = len(self.names)
        self.teams = {}
        colors = (GREEN, RED, BLUE, YELLOW)
        for i in range(self.number_of_players):
            self.teams[colors[i]] = self.names[i]

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
        # Отделяем карту от доп. данных
        data = {}
        data_buildings = {}
        new_field = []
        # self.field = list(map(lambda x: ''.join(x), self.field))
        for row in range(len(self.field)):
            b_flag = 0
            lendata = 0
            new_field.append([])
            for col in range(len(self.field[row])):
                content, building = self.field[row][col].split('/')
                if content[-1] == '}':
                    key = row, col
                    info = content[content.find('{') + 1:-1]
                    data[key] = info
                    content = content[:content.find('{')]
                if building and building[-1] == '}':
                    key = row, col
                    info = building[building.find('{') + 1:-1]
                    data_buildings[key] = info
                    building = building[:building.find('{')]
                new_field[row].append([content, building])

        self.field = new_field

        self.width = len(self.field[0])
        self.height = len(self.field)

        self.frame = pygame.transform.scale(load_image('frame.png'), Field.size_in_pixels)
        screen.blit(self.frame, (0, 0))
        self.space = pygame.Surface((self.width * tile_width,
                                     self.height * tile_height))

        for x in range(self.height):
            for y in range(self.width):
                content, building = self.field[x][y]
                if content == '.':
                    self.field[x][y] = Cell()
                elif content == '#':
                    self.field[x][y] = Cell(content=Block())
                elif content == 'G':
                    self.players[GREEN] = [Player(x, y, GREEN)]
                    if (x, y) in data:
                        weapon, shield, helmet, boots, chest, bonus, army, movepoints, money = \
                            data[(x, y)].split('&')
                        atc = sum(map(lambda x: ITEMS[x].d_atc, (weapon, shield, helmet, boots, chest)))
                        dfc = sum(map(lambda x: ITEMS[x].d_dfc, (weapon, shield, helmet, boots, chest)))
                        bonus = list(map(int, bonus.split(',')))
                        self.players[GREEN][0].atc = atc
                        self.players[GREEN][0].dfc = dfc
                        self.players[GREEN][0].equipped_weapon = weapon
                        self.players[GREEN][0].equipped_shield = shield
                        self.players[GREEN][0].equipped_helmet = helmet
                        self.players[GREEN][0].equipped_boots = boots
                        self.players[GREEN][0].equipped_chest = chest
                        self.players[GREEN][0].bonus = {'sale': bonus[0], 'd_hp': bonus[1], 'bonus_move': bonus[2],
                                                        'd_spd': bonus[3]}
                        self.players[GREEN][0].army = [(UNITS[unit].copy() if unit else 'null') for unit in
                                                       army.split(',')]
                        self.players[GREEN][0].movepoints = int(movepoints)
                        self.players[GREEN][0].money = int(money)
                    self.field[x][y] = Cell(content=self.players[GREEN][0])

                elif content == 'R':
                    if self.number_of_players >= 2:
                        self.players[RED] = [Player(x, y, RED)]
                        if (x, y) in data:
                            weapon, shield, helmet, boots, chest, bonus, army, movepoints, money = \
                                data[(x, y)].split('&')
                            atc = sum(map(lambda x: ITEMS[x].d_atc,
                                          (weapon, shield, helmet, boots, chest)))
                            dfc = sum(map(lambda x: ITEMS[x].d_dfc,
                                          (weapon, shield, helmet, boots, chest)))
                            bonus = list(map(int, bonus.split(',')))
                            self.players[RED][0].atc = atc
                            self.players[RED][0].dfc = dfc
                            self.players[RED][0].equipped_weapon = weapon
                            self.players[RED][0].equipped_shield = shield
                            self.players[RED][0].equipped_helmet = helmet
                            self.players[RED][0].equipped_boots = boots
                            self.players[RED][0].equipped_chest = chest
                            self.players[RED][0].bonus = {'sale': bonus[0], 'd_hp': bonus[1], 'bonus_move': bonus[2],
                                                          'd_spd': bonus[3]}
                            self.players[RED][0].army = [(UNITS[unit].copy() if unit else 'null') for unit in
                                                         army.split(',')]
                            self.players[RED][0].movepoints = int(movepoints)
                            self.players[RED][0].money = int(money)
                        self.field[x][y] = Cell(content=self.players[RED][0])
                    else:
                        self.field[x][y] = Cell()

                elif content == 'B':
                    if self.number_of_players >= 3:
                        self.players[BLUE] = [Player(x, y, BLUE)]
                        if (x, y) in data:
                            weapon, shield, helmet, boots, chest, bonus, army, movepoints, money = data[
                                (x, y)].split('&')
                            atc = sum(map(lambda x: ITEMS[x].d_atc,
                                          (weapon, shield, helmet, boots, chest)))
                            dfc = sum(map(lambda x: ITEMS[x].d_dfc,
                                          (weapon, shield, helmet, boots, chest)))
                            bonus = list(map(int, bonus.split(',')))
                            self.players[BLUE][0].atc = atc
                            self.players[BLUE][0].dfc = dfc
                            self.players[BLUE][0].equipped_weapon = weapon
                            self.players[BLUE][0].equipped_shield = shield
                            self.players[BLUE][0].equipped_helmet = helmet
                            self.players[BLUE][0].equipped_boots = boots
                            self.players[BLUE][0].equipped_chest = chest
                            self.players[BLUE][0].bonus = {'sale': bonus[0], 'd_hp': bonus[1], 'bonus_move': bonus[2],
                                                           'd_spd': bonus[3]}
                            self.players[BLUE][0].army = [(UNITS[unit].copy() if unit else 'null') for unit in
                                                          army.split(',')]
                            self.players[BLUE][0].movepoints = int(movepoints)
                            self.players[BLUE][0].money = int(money)
                        self.field[x][y] = Cell(content=self.players[BLUE][0])
                    else:
                        self.field[x][y] = Cell()

                elif content == 'Y':
                    if self.number_of_players >= 4:
                        self.players[YELLOW] = [Player(x, y, YELLOW)]
                        if (x, y) in data:
                            weapon, shield, helmet, boots, chest, bonus, army, movepoints, money = data[
                                (x, y)].split('&')
                            atc = sum(map(lambda x: ITEMS[x].d_atc,
                                          (weapon, shield, helmet, boots, chest)))
                            dfc = sum(map(lambda x: ITEMS[x].d_dfc,
                                          (weapon, shield, helmet, boots, chest)))
                            bonus = list(map(int, bonus.split(',')))
                            self.players[YELLOW][0].atc = atc
                            self.players[YELLOW][0].dfc = dfc
                            self.players[YELLOW][0].equipped_weapon = weapon
                            self.players[YELLOW][0].equipped_shield = shield
                            self.players[YELLOW][0].equipped_helmet = helmet
                            self.players[YELLOW][0].equipped_boots = boots
                            self.players[YELLOW][0].equipped_chest = chest
                            self.players[YELLOW][0].bonus = {'sale': bonus[0], 'd_hp': bonus[1], 'bonus_move': bonus[2],
                                                             'd_spd': bonus[3]}
                            self.players[YELLOW][0].army = [(UNITS[unit].copy() if unit else 'null') for unit in
                                                            army.split(',')]
                            self.players[YELLOW][0].movepoints = int(movepoints)
                            self.players[YELLOW][0].money = int(money)
                        self.field[x][y] = Cell(content=self.players[YELLOW][0])
                    else:
                        self.field[x][y] = Cell()
                elif content in ITEMS:
                    self.field[x][y] = Cell(content=ITEMS[content])
                else:
                    raise Exception(f"Incorrect content in slot{self.save_slot + 1}: {content}")

                if building in HOUSES:
                    self.field[x][y].building = House(x, y, building + '.png', *HOUSES[building])
                    if (x, y) in data_buildings:
                        self.field[x][y].building.bought = bool(int(data_buildings[(x, y)]))
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
            if (last_row, last_col) == cell and len(path) * 100 <= selected_hero.movepoints:
                selected_hero.movepoints -= len(path) * 100
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

    def save(self):
        new_field = []
        for x in range(self.height):
            new_field.append('')
            for y in range(self.width):
                if type(self.field[x][y]).__name__ == 'Cell':
                    cell = self.field[x][y]
                    content = cell.get_content()
                    building = cell.get_building()
                    if content is None:
                        new_field[x] += '.'
                    elif type(content).__name__ == 'Block':
                        new_field[x] += '#'
                    elif type(content).__name__ == 'Player':
                        new_field[x] += content.team[0].upper()
                        inventory = '&'.join(map(lambda x: x.tile_type,
                                                 (content.equipped_weapon, content.equipped_shield,
                                                  content.equipped_helmet, content.equipped_boots,
                                                  content.equipped_chest)))
                        bonus = ','.join(map(str, content.bonus.values()))
                        army = ','.join(map(lambda x: x.key_in_library, content.army))
                        mp = content.movepoints
                        money = content.money
                        new_field[x] += f'{{{inventory}&{bonus}&{army}&{mp}&{money}}}'
                    elif type(content).__name__ == 'Item':
                        new_field[x] += content.tile_type
                    elif type(content).__name__ == 'NPC':
                        pass

                    new_field[x] += '/'
                    if building is not None:
                        new_field[x] += f"{building.key_in_library}{{{int(building.bought)}}}"
                new_field[x] += ';'
            new_field[x] = new_field[x][:-1]

        file = open(os.path.join("data/saves", f"{self.save_slot}.txt"), 'w', encoding='utf-8')
        file.write(self.game_name + '\n')
        file.write(self.map_name + '\n')
        file.write(';'.join(self.names) + '\n')
        height = len(new_field)
        for row in range(height):
            file.write(''.join(new_field[row]) + '\n' * (row != height - 1))
        file.close()


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
        self.active_units = pygame.sprite.Group()

    def draw_cells(self):
        self.rows = len(self.board)
        self.cols = len(self.board[0])
        self.cell_width = (self.width - FightBoard.margin_left - FightBoard.margin_right) // self.cols
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

        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] is not None:
                    self.active_units.add(self.board[row][col])
                    self.board[row][col].resize(self.cell_width, self.cell_height)


        self.surface.blit(cells_surface, (FightBoard.margin_right, FightBoard.margin_top))

    def draw_units(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] is not None:
                    self.board[row][col].move(self.margin_left + col * self.cell_width,
                                                              self.margin_top + row * self.cell_height)
        self.active_units.draw(self.surface)

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
    board = [[None] * 10 for _ in range(9)]
    turn_queue = left_hero.army + right_hero.army


    for num in range(len(left_hero.army)):
        if left_hero.army[num] != null_unit:
            board[coor_row[num]][0] = left_hero.army[num]


    for num in range(len(right_hero.army)):
        if right_hero.army[num] != null_unit:
            board[coor_row[num]][9] = right_hero.army[num]
            board[coor_row[num]][9].reverse()


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
        fight_board.draw_units()
        screen.blit(fight_board.surface, topleft_coord)
        pygame.display.flip()
        clock.tick(FPS)


class Player(pygame.sprite.Sprite):
    default_image = pygame.transform.scale(load_image('player.png', -1), (tile_width, tile_height))
    null_unit = UNITS["null"] #Unit("player.png", "", 0, 0, 0, 0, 0, 0, 0)
    null_item = ITEMS["null"]
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
        self.atc, self.dfc = 1, 1
        self.equipped_weapon = Player.null_item
        self.equipped_shield = Player.null_item
        self.equipped_helmet = Player.null_item
        self.equipped_boots = Player.null_item
        self.equipped_chest = Player.null_item
        equipped_items = [self.equipped_weapon, self.equipped_shield, self.equipped_helmet, self.equipped_boots,
                          self.equipped_chest]
        self.money = 0
        self.inventory = equipped_items + [self.money]
        self.bonus = {'sale': 1, 'd_hp': 0, 'bonus_move': 0, 'd_spd': 0}
        self.army = [Player.null_unit] * 7
        self.movepoints = 2000

    def move(self, x, y):
        self.pos = x, y
        self.rect = self.image.get_rect().move(tile_width * x, tile_height * y)

    def get_pos(self):
        return self.pos

    def interact(self, other):
        if type(other).__name__ == 'Player':
            if other.team != self.team:
                fight(self, other)
        elif type(other).__name__ == 'Item':
            # Обычные предметы меняются на лучшие версии себя
            if other.slot == 'boots' and other.d_atc > self.equipped_boots.d_atc:
                self.atc, self.dfc = self.atc - self.equipped_boots.d_atc, self.dfc - self.equipped_boots.d_dfc
                self.equipped_boots = other
                self.atc, self.dfc = self.atc + self.equipped_boots.d_atc, self.dfc + self.equipped_boots.d_dfc
            elif other.slot == 'chest' and other.d_atc > self.equipped_chest.d_atc:
                self.atc, self.dfc = self.atc - self.equipped_chest.d_atc, self.dfc - self.equipped_chest.d_dfc
                self.equipped_chest = other
                self.atc, self.dfc = self.atc + self.equipped_chest.d_atc, self.dfc + self.equipped_chest.d_dfc
            elif other.slot == 'helm' and other.d_dfc > self.equipped_helmet.d_dfc:
                self.atc, self.dfc = self.atc - self.equipped_helmet.d_atc, self.dfc - self.equipped_helmet.d_dfc
                self.equipped_helmet = other
                self.atc, self.dfc = self.atc + self.equipped_helmet.d_atc, self.dfc + self.equipped_helmet.d_dfc
            elif other.slot == 'weapon' and other.d_atc > self.equipped_weapon.d_atc:
                self.atc, self.dfc = self.atc - self.equipped_weapon.d_atc, self.dfc - self.equipped_weapon.d_dfc
                self.equipped_weapon = other
                self.atc, self.dfc = self.atc + self.equipped_weapon.d_atc, self.dfc + self.equipped_weapon.d_dfc
            elif other.slot == 'shield' and other.d_dfc > self.equipped_shield.d_dfc:
                self.atc, self.dfc = self.atc - self.equipped_shield.d_atc, self.dfc - self.equipped_shield.d_dfc
                self.equipped_shield = other
                self.atc, self.dfc = self.atc + self.equipped_shield.d_atc, self.dfc + self.equipped_shield.d_dfc
            # НЕОбычные предметы меняются на лучшие версии себя
            elif other.slot == 'other':
                key, val = other.feature.keys()[0], other.feature.values()[0]
                self.bonus[key] = self.bonus[key] + val
            elif other.slot == 'coins':
                self.money += 1
            row, col = self.get_pos()[::-1]
            field.field[row][col].content = None
            field.field[row][col].render(row, col)
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
    def __init__(self, row, col, image_name, unit, cost, delta, key):
        self.key_in_library = key
        self.unit, self.cost, self.delta = unit, cost, delta
        self.unit.count = delta
        self.bought = False
        super().__init__(house_sprites)
        self.image = pygame.transform.scale(load_image("homes/" + image_name),
                                            (tile_width, tile_height))
        self.rect = self.image.get_rect().move(col * tile_width, row * tile_height)
        self.sprites_button = pygame.sprite.Group()

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
        attempt = False

        font_name = pygame.font.Font('data/16478.otf', 26)
        font_aff = pygame.font.Font('data/16478.otf', 18)
        name = font_name.render(f"Жилище {self.unit.name}", 10, (156, 130, 79))
        afford = font_aff.render(
            f"Желаете купить {self.delta} {self.unit.name} за {self.cost // visitor.bonus['sale']} золота?", 10,
            (156, 130, 79))
        reject = font_aff.render(f"Извините, но сейчас вы не можете купить {self.unit.name}", 10, (156, 130, 79))
        congratulation = font_aff.render(f"Поздравляем, вы купили {self.unit.name}", 10, (156, 130, 79))
        current_text = afford

        button_agree = Button(self.sprites_button, 10, int(HEIGHT / 3) - 60,
                              50, 50)
        button_agree.set_background_image("agree.png")
        button_agree.render()
        button_disagree = Button(self.sprites_button, int(WIDTH / 2.5) - 60,
                                 int(HEIGHT / 3) - 60, 50, 50)
        button_disagree.set_background_image("disagree.png")
        button_disagree.render()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        screen.blit(screen_save, (0, 0))
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION:
                    event.pos = event.pos[0] - topleft_coord[0], event.pos[1] - topleft_coord[1]
                if (button_agree.clicked and attempt) or button_disagree.clicked:
                    screen.blit(screen_save, (0, 0))
                    return
                if button_agree.clicked and not attempt:
                    attempt = True
                    current_text = reject
                    if self.cost // visitor.bonus['sale'] <= visitor.money and not self.bought:
                        if Player.null_unit in visitor.army:
                            visitor.army[visitor.army.index(Player.null_unit)] = self.unit
                            visitor.money -= self.cost // visitor.bonus['sale']
                            current_text = congratulation
                            self.bought = True
                        elif self.unit.name in [unit.name for unit in visitor.army] and not self.bought:
                            visitor.army[[unit.name for unit in visitor.army].index(self.unit.name)] = \
                                visitor.army[[unit.name for unit in visitor.army].index(self.unit.name)] + self.unit
                            visitor.money -= self.cost // visitor.bonus['sale']
                            current_text = congratulation
                            self.bought = True
                self.sprites_button.update(event)

            surface.blit(fon, (-100, -100))
            surface.blit(name, (10, 10))
            surface.blit(current_text, (10, 60))
            self.sprites_button.draw(surface)
            screen.blit(surface, topleft_coord)
            pygame.display.flip()
            clock.tick(FPS)


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
    def __init__(self, group, x, y, width, height, function=lambda: None):
        super().__init__(group)
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.function = function
        self.bgcolor = pygame.Color(255, 255, 255)
        self.bgimage = None
        self.hovered = False
        self.clicked = False
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.text = ''
        self.font = pygame.font.FontType(None, -1)
        self.textcolor = (0, 0, 0, 0)

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
        self.bgimage = load_image(filename, -1)
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
        self.image = pygame.Surface([self.width, self.height], flags=pygame.SRCALPHA)
        if self.bgimage is not None:
            self.image.blit(self.bgimage, (0, 0))
        else:
            self.image.fill(self.bgcolor)
        if self.hovered:
            black = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
            black.fill(pygame.Color(*((16 + 16 * self.clicked,) * 3)))
            self.image.blit(black, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

        try:
            rendered = self.font.render(self.text, True, self.textcolor)
            w, h = rendered.get_size()
            self.image.blit(rendered, ((self.width - w) // 2, (self.height - h) // 2))
        except AttributeError:
            print('text not found')

        # self.surface.blit(self.image, (self.x, self.y))


class InputBox(pygame.sprite.Sprite):
    symbols = 'abcdefghijklmnopqrstuvwxyzабвгдеёжзийклмнопрстуфхцчшщъыьэюя1234567890_'

    def __init__(self, group, x, y, width, height, placeholder='',
                 font=pygame.font.Font('data/16478.otf', 24)):
        super().__init__(group)
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.placeholder = placeholder
        self.font = font
        self.bgcolor = pygame.color.Color(105, 105, 105)
        self.bgimage = None
        self.active = False
        self.enabled = True
        self.text = ''
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.incorrect = False
        self.max_length = None

    def on_click(self, event):
        self.active = False
        if self.enabled and self.x < event.pos[0] < self.x + self.width \
                and self.y < event.pos[1] < self.y + self.height:
            self.active = True

    def set_placeholder_text(self, placeholder):
        self.placeholder = placeholder

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.text = ''

    def set_incorrect(self, incorrect):
        self.incorrect = incorrect

    def set_max_length(self, length):
        self.max_length = length

    def set_background_image(self, filename):
        self.bgimage = load_image(filename)
        self.bgimage = pygame.transform.scale(self.bgimage, (self.width, self.height))

    def set_background_color(self, color: pygame.Color):
        self.bgcolor = color

    def on_keydown(self, event):
        if event.key == pygame.K_RETURN:
            self.active = False
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.unicode.lower() in InputBox.symbols:
            if self.max_length is None or len(self.text) < self.max_length:
                self.text += event.unicode
                self.incorrect = False

    def update(self, *args):
        for arg in args:
            if arg.type == pygame.MOUSEBUTTONDOWN:
                self.on_click(arg)
            elif self.active and arg.type == pygame.KEYDOWN:
                self.on_keydown(arg)
        self.render()

    def render(self):
        self.image = pygame.Surface([self.width, self.height], flags=pygame.SRCALPHA)
        if self.bgimage is not None:
            self.image.blit(self.bgimage, (0, 0))
        else:
            self.image.fill(self.bgcolor)
            if not self.incorrect:
                pygame.draw.rect(self.image, pygame.color.Color(0xe7, 0xda, 0xae, 255),
                                 (0, 0, self.image.get_width(),
                                  self.image.get_height()), 1)
        if self.incorrect:
            pygame.draw.rect(self.image, pygame.color.Color(255, 0, 0, 255),
                             (0, 0, self.image.get_width(),
                              self.image.get_height()), 1)

        rendered = self.font.render(self.text if self.text else self.placeholder, True,
                                    pygame.color.Color(0xe7, 0xda, 0xae) if self.text
                                    else pygame.color.Color(128, 128, 128))
        w, h = rendered.get_size()
        self.image.blit(rendered, ((self.width - w) // 2, (self.height - h) // 2))

        if not self.enabled:
            black = pygame.Surface((self.width, self.height))
            black.fill(pygame.Color(0, 0, 0))
            black.set_alpha(150)
            self.image.blit(black, (0, 0))
        if self.active:
            pygame.draw.rect(self.image, pygame.color.Color(0xe7, 0xda, 0xae, 255),
                             (0, 0, self.image.get_width() - 1, self.image.get_height() - 1), 2)
        # self.surface.blit(self.image, (self.x, self.y))


class CheckBoxGroup(pygame.sprite.Group):
    def __init__(self, *sprites):
        super().__init__(sprites)
        self.checked = None

    def get_checked(self):
        for sprite in self.sprites():
            if sprite.is_checked():
                return sprite
        return None

    def uncheck_all(self):
        for sprite in self.sprites():
            sprite.set_checked(False)

    def get_by_name(self, name):
        for sprite in self.sprites():
            if sprite.name == name:
                return sprite
        return None


class CheckBox(Button):
    def __init__(self, group: CheckBoxGroup, name, x, y, width, height, checked=False):
        super().__init__(group, x, y, width, height)  # POSSIBLE CRASH
        self.group = group
        self.name = name
        self.checked = checked

    def set_checked(self, checked):
        self.checked = checked

    def is_checked(self):
        return self.checked

    def on_click(self, event):
        if self.x < event.pos[0] < self.x + self.width \
                and self.y < event.pos[1] < self.y + self.height:
            self.group.uncheck_all()
            self.set_checked(True)

    def update(self, *args):
        for arg in args:
            if arg.type == pygame.MOUSEBUTTONDOWN:
                self.on_click(arg)
            elif arg.type == pygame.MOUSEMOTION:
                self.on_hover(arg)
        self.render()

    def render(self):
        self.image = pygame.Surface([self.width, self.height], flags=pygame.SRCALPHA)
        if self.bgimage is not None:
            self.image.blit(self.bgimage, (0, 0))
        else:
            self.image.fill(self.bgcolor)
            pygame.draw.rect(self.image, pygame.color.Color(0xe7, 0xda, 0xae, 255),
                             (0, 0, self.image.get_width(),
                              self.image.get_height()), 1)
        if self.hovered:
            black = pygame.Surface((self.width, self.height))
            black.fill(0)
            black.set_alpha(32)
            self.image.blit(black, (0, 0))

        try:
            text_surf = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
            lines = self.text.split('\n')
            coord = 0
            for i, line in enumerate(lines):
                rendered = self.font.render(line, True, self.textcolor)
                w, h = rendered.get_size()
                text_surf.blit(rendered, ((self.width - w) // 2, coord))
                coord += h + 2
            self.image.blit(text_surf, (0, (self.height - coord) // 2))

        except AttributeError:
            import traceback
            traceback.print_exc()

        if self.checked:
            pygame.draw.rect(self.image, pygame.color.Color(0xe7, 0xda, 0xae, 255),
                             (1, 1, self.image.get_width() - 2, self.image.get_height() - 2), 3)


def select_save_slot(mode):  # mode = "create" or "load"
    global button_sprites
    button_sprites_save = button_sprites.copy()
    button_sprites.empty()

    if mode not in ("create", "load"):
        raise Exception(f"Incorrect select_save_slot mode: {mode}")

    font = pygame.font.Font('data/16478.otf', 24)
    slots_sprites = CheckBoxGroup()

    # Сохраняем основной экран и затемняем его
    screen_save = screen.copy()
    black = pygame.Surface((WIDTH, HEIGHT))
    black.fill(pygame.color.Color(0, 0, 0))
    black.set_alpha(200)
    screen.blit(black, (0, 0))

    # Создаем экран для выбора
    width, height = WIDTH // 1.5, HEIGHT // 1.25
    topleft_coord = ((WIDTH - width) // 2, (HEIGHT - height) // 2)
    surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
    surface.blit(fon, (-100, -100))

    heading = font.render("Выберите слот для сохранения игры", True,
                          pygame.color.Color(156, 130, 79))
    surface.blit(heading, ((width - heading.get_width()) // 2, 10))

    # загружаем файлы сохранения
    files = os.listdir("data/saves")
    files = list(filter(lambda x: x.endswith('.txt'), files))
    slots = [None] * 10
    for filename in files:
        f = open(os.path.join("data/saves", filename), encoding='utf-8')
        data = f.read()
        f.close()
        game_name, map_name, names, *field = data.split('\n')
        nplayers = len(names.split(';'))
        num = int(filename[:-4])
        slots[num - 1] = game_name, map_name, nplayers

    bwidth = width // 2.5
    bheight = (height - 150) // 7
    left, top = (width - bwidth * 2) // 3, 50
    for i in range(10):
        if i < 5:
            slot = CheckBox(slots_sprites, str(i + 1), left, top + bheight * i * 1.5, bwidth,
                            bheight)
        else:
            slot = CheckBox(slots_sprites, str(i + 1),
                            width - left - bwidth, top + bheight * (i % 5) * 1.5, bwidth, bheight)
        slot.set_background_color(pygame.color.Color(138, 15, 18, 200))

        if slots[i] is not None:
            slot.set_text(f"{slots[i][0]}\nКарта: {slots[i][1]}        Игроков: {slots[i][2]}", font,
                          pygame.color.Color(156, 130, 79))
        else:
            slot.set_text("Пустой слот", font, pygame.color.Color(156, 130, 79))
        slot.render()

    ok_btn = Button(button_sprites, width // 3, top + bheight * 7.5 - 25, int(width // 3),
                    int(bheight // 2))
    ok_btn.set_background_image('button-background.jpg')
    ok_btn.set_text("Подтвердить", font, pygame.color.Color(156, 130, 79))
    ok_btn.render()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONDOWN:
                event.pos = (event.pos[0] - topleft_coord[0], event.pos[1] - topleft_coord[1])
            if ok_btn.clicked:
                selected = slots_sprites.get_checked()
                if selected is not None:
                    i = int(selected.name)
                    if slots[i - 1] is not None:
                        if mode == 'create':
                            yes = dialog("Вы действительно хотите\nперезаписать сохранение?")
                            if yes:
                                button_sprites = button_sprites_save
                                return i
                        elif mode == 'load':
                            button_sprites = button_sprites_save
                            return i
                    else:
                        if mode == 'create':
                            button_sprites = button_sprites_save
                            return i
                        elif mode == 'load':
                            pass

            slots_sprites.update(event)
            button_sprites.update(event)
        slots_sprites.draw(surface)
        button_sprites.draw(surface)
        screen.blit(surface, topleft_coord)
        pygame.display.flip()
        clock.tick(FPS)


def dialog(text):
    font = pygame.font.Font('data/16478.otf', 32)

    # Сохраняем основной экран и затемняем его
    screen_save = screen.copy()
    black = pygame.Surface((WIDTH, HEIGHT))
    black.fill(pygame.color.Color(0, 0, 0))
    black.set_alpha(200)
    screen.blit(black, (0, 0))

    # Создаем экран для выбора
    width, height = 700, 300
    topleft_coord = ((WIDTH - width) // 2, (HEIGHT - height) // 2)
    surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
    surface.blit(fon, (-100, -100))
    text_coord = 20
    for line in text.split('\n'):
        rendered = font.render(line, True, pygame.color.Color(156, 130, 79))
        text_coord += rendered.get_height() + 2
        surface.blit(rendered, ((width - rendered.get_width()) // 2, text_coord))

    bwidth, bheight = int(width // 2.5), height // 4
    left, top = (width - bwidth * 2) // 3, height // 2

    dialog_buttons = pygame.sprite.Group()
    yes_btn = Button(dialog_buttons, width - left - bwidth, top, bwidth, bheight)
    yes_btn.set_background_image('button-background.jpg')
    yes_btn.set_text("Да", font, pygame.color.Color(156, 130, 79))
    yes_btn.render()

    no_btn = Button(dialog_buttons, left, top, bwidth, bheight)
    no_btn.set_background_image('button-background.jpg')
    no_btn.set_text("Нет", font, pygame.color.Color(156, 130, 79))
    no_btn.render()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONDOWN:
                event.pos = (event.pos[0] - topleft_coord[0], event.pos[1] - topleft_coord[1])
            if yes_btn.clicked:
                return True
            if no_btn.clicked:
                return False
            dialog_buttons.update(event)
        dialog_buttons.draw(surface)
        screen.blit(surface, topleft_coord)
        pygame.display.flip()
        clock.tick(FPS)


# Стартовый экран
def start_screen():
    button_sprites.empty()
    screen.blit(fon, (0, 0))

    bwidth, bheight = 480, 100

    font = pygame.font.Font('data/16478.otf', 60)

    newgame_button = Button(button_sprites, (WIDTH - bwidth) // 2,
                            (HEIGHT - bheight * 5.5) // 2, bwidth, bheight)
    newgame_button.set_background_image('button-background.jpg')
    newgame_button.set_text("Новая игра", font, pygame.color.Color(156, 130, 79))
    newgame_button.render()

    continue_button = Button(button_sprites, (WIDTH - bwidth) // 2,
                             (HEIGHT - bheight * 2.5) // 2, bwidth, bheight)
    continue_button.set_background_image('button-background.jpg')
    continue_button.set_text("Продолжить", font, pygame.color.Color(156, 130, 79))
    continue_button.render()

    settings_button = Button(button_sprites, (WIDTH - bwidth) // 2,
                             (HEIGHT - bheight * -0.5) // 2, bwidth, bheight)
    settings_button.set_background_image('button-background.jpg')
    settings_button.set_text("Настройки", font, pygame.color.Color(156, 130, 79))
    settings_button.render()

    exit_button = Button(button_sprites, (WIDTH - bwidth) // 2,
                         (HEIGHT - bheight * -3.5) // 2, bwidth, bheight, terminate)
    exit_button.set_background_image('button-background.jpg')
    exit_button.set_text("Выйти", font, pygame.color.Color(32, 32, 32))
    exit_button.render()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                terminate()
            if newgame_button.clicked:
                return new_game()
            if continue_button.clicked or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                return Field(select_save_slot('load'))
            button_sprites.update(event)
        screen.blit(fon, (0, 0))
        button_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


# Создать новую игру (выбрать карту, количество игроков и т.д.)
def new_game():
    screen.blit(fon, (0, 0))

    font = pygame.font.Font('data/16478.otf', 24)

    button_sprites.empty()

    inp_x, y = WIDTH // 12.8, HEIGHT // 10.8
    bwidth, bheight = WIDTH // 6.4, HEIGHT // 18

    # Поля для ввода имен игроков
    g_input = InputBox(inputbox_sprites, inp_x, y, bwidth, bheight, 'Имя')
    g_input.set_background_color(pygame.color.Color(27, 18, 12, 200))
    g_input.set_max_length(16)
    g_input.render()

    r_input = InputBox(inputbox_sprites, inp_x, y + bheight * 1.5, bwidth, bheight, 'Имя')
    r_input.set_background_color(pygame.color.Color(27, 18, 12, 200))
    r_input.set_enabled(False)
    r_input.set_max_length(16)
    r_input.render()

    b_input = InputBox(inputbox_sprites, inp_x, y + bheight * 3, bwidth, bheight, 'Имя')
    b_input.set_background_color(pygame.color.Color(27, 18, 12, 200))
    b_input.set_enabled(False)
    b_input.set_max_length(16)
    b_input.render()

    y_input = InputBox(inputbox_sprites, inp_x, y + bheight * 4.5, bwidth, bheight, 'Имя')
    y_input.set_background_color(pygame.color.Color(27, 18, 12, 200))
    y_input.set_enabled(False)
    y_input.set_max_length(16)
    y_input.render()

    # Цветные кружки возле полей для ввода для обозначения цвета команд
    circles = pygame.Surface((bheight, bheight * 5.5), flags=pygame.SRCALPHA)
    colors = [(0, 0x80, 0, 200), (255, 0, 0, 200), (0, 0, 255, 200), (255, 255, 0, 200)]
    ys = [0, int(bheight * 1.5), int(bheight * 3), int(bheight * 4.5)]
    for i in range(4):
        pygame.draw.circle(circles, colors[i], (bheight // 2, ys[i] + bheight // 2),
                           bheight // 2)
    screen.blit(circles, (inp_x - bheight - 10, y))

    # Выбор карты
    map_x = WIDTH - inp_x - bwidth
    checkbox_sprites = CheckBoxGroup()
    for i, (name, map_obj) in enumerate(MAPS.items()):
        checkbox = CheckBox(checkbox_sprites, name, map_x, y + bheight * i * 1.5, bwidth, bheight)
        checkbox.set_text(map_obj.get_name(), font, pygame.color.Color(156, 130, 79))
        checkbox.set_background_color(pygame.color.Color(138, 15, 18, 200))
        checkbox.set_checked(i == 0)
        checkbox.render()

    font = pygame.font.Font('data/16478.otf', 48)
    description = font.render(MAPS[checkbox_sprites.get_checked().name].get_description(),
                              True, pygame.color.Color(156, 130, 79))
    preview_size = int(WIDTH - bwidth * 3.5), int(HEIGHT * 0.7)
    preview_x, preview_y = (WIDTH - preview_size[0]) // 2, y
    preview = MAPS[checkbox_sprites.get_checked().name].get_preview(*preview_size)

    # Кнопка создания игры
    bwidth *= 1.5
    bheight *= 1.5

    newgame_button = Button(button_sprites, map_x - bwidth // 6, int(y + 0.85 * HEIGHT - bheight),
                            int(bwidth), int(bheight))
    newgame_button.set_background_image('button-background.jpg')
    newgame_button.set_text("Создать игру", font, pygame.color.Color(156, 130, 79))
    newgame_button.render()

    # Кнопка назад
    goback_button = Button(button_sprites, inp_x - bwidth // 6, int(y + 0.85 * HEIGHT - bheight),
                           int(bwidth), int(bheight))
    goback_button.set_background_image('button-background.jpg')
    goback_button.set_text("Назад", font, pygame.color.Color(156, 130, 79))
    goback_button.render()

    # Поле ввода названия игры
    bwidth *= 1.5
    name_input = InputBox(inputbox_sprites, (WIDTH - bwidth) // 2, int(y + 0.85 * HEIGHT - bheight),
                          bwidth, bheight, 'Введите название игры')
    name_input.set_background_color(pygame.color.Color(27, 18, 12, 200))
    name_input.set_max_length(42)
    name_input.render()

    while True:
        map_name = checkbox_sprites.get_checked().name
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE or goback_button.clicked:
                return start_screen()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN or newgame_button.clicked:
                map_name = checkbox_sprites.get_checked().name
                if not g_input.text:
                    g_input.set_incorrect(True)
                elif not name_input.text:
                    name_input.set_incorrect(True)
                else:
                    save_slot = select_save_slot("create")  # Слот для сохранения
                    file = open(os.path.join("data/saves", f"{save_slot}.txt"), 'w', encoding='utf-8')
                    file.write(name_input.text + '\n')
                    file.write(map_name + '\n')
                    file.write(';'.join(filter(lambda x: x, (g_input.text, r_input.text, b_input.text, y_input.text))) + '\n')
                    field = MAPS[map_name].load()
                    height = len(field)
                    for row in range(height):
                        file.write(';'.join(field[row]) + '\n' * (row != height - 1))
                    file.close()
                    return Field(save_slot)

            inputbox_sprites.update(event)
            button_sprites.update(event)
            checkbox_sprites.update(event)
            description = font.render(MAPS[map_name].get_description(), True, pygame.color.Color(156, 130, 79))
            preview = MAPS[checkbox_sprites.get_checked().name].get_preview(*preview_size)
        screen.blit(fon, (0, 0))
        screen.blit(circles, (inp_x - bheight - 10, y), special_flags=pygame.BLEND_ADD)
        screen.blit(description,
                    ((WIDTH - description.get_width()) // 2, (y - description.get_height()) // 2))
        screen.blit(preview, (preview_x, preview_y))

        r_input.set_enabled(g_input.text)
        b_input.set_enabled(r_input.text)
        y_input.set_enabled(b_input.text)

        checkbox_sprites.draw(screen)
        inputbox_sprites.draw(screen)
        button_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


fon = pygame.transform.scale(load_image('background.jpg'), (WIDTH, HEIGHT))
field = start_screen()  # Main menu
screen.fill(0xff0000)
cam = Camera(field)
control_panel = ControlPanel(field, cam)
black_texture = pygame.transform.scale(load_image("black-texture.png"), (WIDTH, HEIGHT))
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
            if event.key == pygame.K_s and ctrl_pressed:
                field.save()

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
