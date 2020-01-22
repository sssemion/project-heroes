import os

import xlrd

from houses import HOUSES
from items import ITEMS
from maps import MAPS
from neutrals import NEUTRALS

filename = input('Введите путь к xlsx-файлу: ')

rb = xlrd.open_workbook(filename)
sheet = rb.sheet_by_index(0)

converted_map = ""

for rownum in range(sheet.nrows):
    row = sheet.row_values(rownum)
    for col in range(sheet.ncols):
        c_el = row[col].strip()
        if c_el == '':
            converted_map += './'
        elif c_el in '#GRBY':
            converted_map += c_el + '/'
        elif c_el in ITEMS:
            converted_map += c_el + '/'
        elif c_el in NEUTRALS:
            converted_map += c_el + '/'
        elif c_el in HOUSES:
            converted_map += './' + c_el
        else:
            message = f"Incorrect object '{c_el}' in (row {rownum + 1}; col {col + 1})"
            raise Exception(message)
        if col != sheet.ncols - 1:
            converted_map += ';'
    if rownum != sheet.nrows - 1:
        converted_map += '\n'
print("Карта успешно конвертирована")

while True:
    filename = input("Придумайте название для файла карты: ")
    if filename in MAPS:
        print("Файл с таким именем уже существует. Вы хотите перезаписать файл?")
        if input("[y/n] ") == 'y':
            break
    else:
        break
name = input("Придумайте название для карты: ")
dscr = input("Придумайте описание для карты: ")

key = filename
filename += '.txt'
file = open(os.path.join("data/maps", filename), 'w', encoding='utf-8')
file.write(converted_map)
file.close()

MAPS[key] = (filename, name, dscr)
file = open("maps.py", 'w', encoding='utf-8')
file.write("# Библиотека карт\nMAPS = {\n    # key       filename        name    description\n")
for key, val in MAPS.items():
    file.write(f"   '{key}': ('{val[0]}', '{val[1]}', '{val[2]}'),\n")
file.write('}\n')
file.close()

print("Карта успешно добавлена в библиотеку")
input("Нажмите Enter для выхода")
