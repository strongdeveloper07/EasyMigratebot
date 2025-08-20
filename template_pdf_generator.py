#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для генерации PDF формы, максимально приближенной к эталонному образцу.
Эталон: "Уведомление от ИГ Пустой.pdf"
"""

import os
import platform
import logging
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Настраиваем логгер
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Размеры страницы A4 в пунктах (595.27 x 841.89)
PAGE_WIDTH, PAGE_HEIGHT = A4

# Константы для размещения элементов - настроены под эталон
# Отступы и позиционирование
MARGIN_LEFT = 40  # Уменьшенный отступ слева для соответствия эталону
MARGIN_RIGHT = 40  # Уменьшенный отступ справа для соответствия эталону
MARGIN_TOP = 50    # Уменьшенный отступ сверху для соответствия эталону
LINE_HEIGHT = 12   # Уменьшенная высота строки

# Размеры шрифтов
FONT_SIZE = 9
SMALL_FONT_SIZE = 7
TINY_FONT_SIZE = 6

# Размеры клеток точно как в эталонной форме
CELL_WIDTH = 9     # Увеличенная ширина ячейки
CELL_HEIGHT = 12   # Увеличенная высота ячейки
SMALL_CELL_WIDTH = 7
SMALL_CELL_HEIGHT = 10

# Функция для регистрации шрифтов
def register_fonts():
    """Регистрирует шрифты для использования в PDF"""
    font_registered = False
    font_name = "Helvetica"  # Стандартный шрифт по умолчанию
    
    # Определяем операционную систему и пути к шрифтам
    system = platform.system()
    if system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
        ]
    elif system == "Darwin":  # macOS
        font_paths = [
            "/Library/Fonts/Arial.ttf",
            "/Library/Fonts/Times New Roman.ttf",
        ]
    else:  # Linux и другие
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    
    # Пробуем зарегистрировать шрифты
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                if "arial" in font_path.lower():
                    pdfmetrics.registerFont(TTFont("Arial", font_path))
                    font_name = "Arial"
                    font_registered = True
                    logger.info(f"Зарегистрирован шрифт Arial: {font_path}")
                    
                    # Также регистрируем его для кириллицы
                    pdfmetrics.registerFont(TTFont("Arial-Cyrillic", font_path))
                    break
                elif "times" in font_path.lower() or "liberation" in font_path.lower():
                    pdfmetrics.registerFont(TTFont("Times", font_path))
                    if not font_registered:
                        font_name = "Times"
                        font_registered = True
                        logger.info(f"Зарегистрирован шрифт Times: {font_path}")
                        
                        # Также регистрируем его для кириллицы
                        pdfmetrics.registerFont(TTFont("Times-Cyrillic", font_path))
            except Exception as e:
                logger.warning(f"Не удалось зарегистрировать шрифт {font_path}: {e}")
    
    # Возвращаем имя зарегистрированного шрифта или стандартный
    return font_name

# Регистрируем шрифты и получаем основной шрифт
FONT_NAME = register_fonts()
FONT_BOLD = FONT_NAME  # По умолчанию у нас нет жирного шрифта, используем основной

def draw_char_cells(c, x, y, text, num_cells, cell_width=CELL_WIDTH, cell_height=CELL_HEIGHT):
    """
    Рисует сетку клеток и заполняет их символами текста точно как в эталонной форме
    с поддержкой кириллицы
    """
    # Подготавливаем текст
    clean_text = str(text).strip().upper() if text else ""
    
    # Рисуем клетки и символы
    for i in range(num_cells):
        cell_x = x + i * cell_width
        
        # Рисуем границы клетки
        c.rect(cell_x, y, cell_width, cell_height)
        
        # Помещаем символ в клетку если он есть
        if i < len(clean_text):
            char = clean_text[i]
            try:
                # Выбираем шрифт в зависимости от типа символа
                if ord(char) > 127:  # Кириллические символы
                    if "Arial" in FONT_NAME:
                        c.setFont("Arial-Cyrillic", SMALL_FONT_SIZE)
                    elif "Times" in FONT_NAME:
                        c.setFont("Times-Cyrillic", SMALL_FONT_SIZE)
                    else:
                        c.setFont(FONT_NAME, SMALL_FONT_SIZE)
                else:
                    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
                
                # Центрируем символ в клетке
                char_width = c.stringWidth(char, c._fontname, c._fontsize)
                char_x = cell_x + (cell_width - char_width) / 2
                char_y = y + (cell_height - c._fontsize) / 2
                
                # Рисуем символ
                c.drawString(char_x, char_y, char)
                
            except Exception as e:
                logger.warning(f"Ошибка при отображении символа '{char}': {e}")
                # Пробуем другие варианты отображения
                try:
                    c.setFont("Helvetica", SMALL_FONT_SIZE)
                    c.drawCentredString(cell_x + cell_width/2, y + cell_height/3, "?")
                except:
                    pass

def draw_checkbox(c, x, y, checked=False, size=8):
    """Рисует чекбокс (квадратик с галочкой или пустой)"""
    c.rect(x, y, size, size)
    if checked:
        # Рисуем галочку
        c.line(x + 1, y + 1, x + size - 1, y + size - 1)
        c.line(x + size - 1, y + 1, x + 1, y + size - 1)

def create_page_1(c, data):
    """
    Создает первую страницу уведомления по эталонному образцу
    """
    current_y = PAGE_HEIGHT - MARGIN_TOP
    
    # === ШАПКА ДОКУМЕНТА ===
    
    # Приложение № 1 (справа)
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, current_y, "Приложение № 1")
    current_y -= LINE_HEIGHT
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, current_y, "к приказу МВД России")
    current_y -= LINE_HEIGHT
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, current_y, "от 05.09.2023 г. № 655")
    current_y -= LINE_HEIGHT * 2
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, current_y, "Форма")
    current_y -= LINE_HEIGHT * 3
    
    # УВЕДОМЛЕНИЕ (заголовок по центру)
    c.setFont(FONT_NAME, 12)  # Чуть больший размер для заголовка
    title = "УВЕДОМЛЕНИЕ"
    title_width = c.stringWidth(title, FONT_NAME, 12)
    c.drawString((PAGE_WIDTH - title_width) / 2, current_y, title)
    current_y -= LINE_HEIGHT * 1.5
    
    # Подзаголовки
    c.setFont(FONT_NAME, 10)
    subtitle1 = "об осуществлении трудовой деятельности иностранным гражданином"
    subtitle1_width = c.stringWidth(subtitle1, FONT_NAME, 10)
    c.drawString((PAGE_WIDTH - subtitle1_width) / 2, current_y, subtitle1)
    current_y -= LINE_HEIGHT
    
    subtitle2 = "или лицом без гражданства, получившим патент"
    subtitle2_width = c.stringWidth(subtitle2, FONT_NAME, 10)
    c.drawString((PAGE_WIDTH - subtitle2_width) / 2, current_y, subtitle2)
    current_y -= LINE_HEIGHT * 3
    
    # === 1. СВЕДЕНИЯ О РАБОТОДАТЕЛЕ ===
    
    # Заголовок раздела
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "1. Сведения о работодателе или заказчике работ (услуг):")
    current_y -= LINE_HEIGHT * 1.5
    
    # Тип работодателя (чекбоксы)
    c.drawString(MARGIN_LEFT + 10, current_y, "юридическое лицо")
    draw_checkbox(c, MARGIN_LEFT, current_y, checked=data.get('employer_type') == 'legal')
    c.drawString(MARGIN_LEFT + 150, current_y, "иностранный гражданин или лицо без гражданства -")
    current_y -= LINE_HEIGHT
    c.drawString(MARGIN_LEFT + 10, current_y, "физическое лицо")
    draw_checkbox(c, MARGIN_LEFT, current_y, checked=data.get('employer_type') == 'physical')
    c.drawString(MARGIN_LEFT + 150, current_y, "индивидуальный предприниматель")
    draw_checkbox(c, MARGIN_LEFT + 140, current_y, checked=data.get('employer_type') == 'ip')
    current_y -= LINE_HEIGHT * 1.5
    
    # 1.1 Наименование
    c.drawString(MARGIN_LEFT, current_y, "1.1. Полное наименование работодателя, заказчика работ (услуг) (для юридических лиц) / Фамилия,")
    current_y -= LINE_HEIGHT
    c.drawString(MARGIN_LEFT, current_y, "имя, отчество (при наличии) работодателя, заказчика работ (услуг) (для физических лиц):")
    current_y -= LINE_HEIGHT * 1.3
    
    # Поле для наименования (ячейки)
    company_name = data.get('company_name', '')
    draw_char_cells(c, MARGIN_LEFT, current_y, company_name, 65)  # Больше ячеек для наименования
    current_y -= LINE_HEIGHT * 2
    
    # 1.2 ИНН
    c.drawString(MARGIN_LEFT, current_y, "1.2. ИНН (при наличии):")
    company_inn = data.get('company_inn', '')
    draw_char_cells(c, MARGIN_LEFT + 130, current_y, company_inn, 15)
    current_y -= LINE_HEIGHT * 1.5
    
    # 1.3 Адрес
    c.drawString(MARGIN_LEFT, current_y, "1.3. Адрес (место нахождения) работодателя или заказчика работ (услуг):")
    current_y -= LINE_HEIGHT * 1.3
    
    # Поле для адреса (ячейки)
    company_address = data.get('company_address', '')
    draw_char_cells(c, MARGIN_LEFT, current_y, company_address, 65)
    current_y -= LINE_HEIGHT * 2
    
    # 1.4 Телефон
    c.drawString(MARGIN_LEFT, current_y, "1.4. Телефон:")
    company_phone = data.get('company_telephone', '')
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, company_phone, 25)
    current_y -= LINE_HEIGHT * 2
    
    # === 2. СВЕДЕНИЯ ОБ ИНОСТРАННОМ ГРАЖДАНИНЕ ===
    
    # Заголовок раздела
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "2. Сведения об иностранном гражданине или лице без гражданства:")
    current_y -= LINE_HEIGHT * 1.5
    
    # 2.1 Фамилия
    c.drawString(MARGIN_LEFT, current_y, "2.1. Фамилия:")
    lastname = data.get('lastname', '')
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, lastname, 30)
    current_y -= LINE_HEIGHT * 1.5
    
    # 2.2 Имя
    c.drawString(MARGIN_LEFT, current_y, "2.2. Имя:")
    firstname = data.get('firstname', '')
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, firstname, 30)
    current_y -= LINE_HEIGHT * 1.5
    
    # 2.3 Отчество
    c.drawString(MARGIN_LEFT, current_y, "2.3. Отчество (при наличии):")
    middlename = data.get('middlename', '')
    draw_char_cells(c, MARGIN_LEFT + 150, current_y, middlename, 25)
    current_y -= LINE_HEIGHT * 1.5
    
    # 2.4 Гражданство
    c.drawString(MARGIN_LEFT, current_y, "2.4. Гражданство:")
    citizenship = data.get('citizenship', '')
    draw_char_cells(c, MARGIN_LEFT + 90, current_y, citizenship, 30)
    current_y -= LINE_HEIGHT
    
    # Текст про лицо без гражданства
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 90, current_y, "(если лицо без гражданства, указать \"лицо без гражданства\")")
    c.setFont(FONT_NAME, FONT_SIZE)
    current_y -= LINE_HEIGHT * 1.5
    
    # 2.5 Дата рождения
    c.drawString(MARGIN_LEFT, current_y, "2.5. Дата рождения:")
    birthdate = data.get('birthdate', '')
    
    # Преобразуем дату в нужный формат (ДД.ММ.ГГГГ)
    if birthdate:
        try:
            if isinstance(birthdate, str):
                # Проверяем формат даты
                if '.' in birthdate:
                    day, month, year = birthdate.split('.')
                elif '-' in birthdate:
                    year, month, day = birthdate.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                # Если это объект datetime
                day = birthdate.day
                month = birthdate.month
                year = birthdate.year
            
            # Форматируем строки чисел
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            # Рисуем ячейки для даты
            draw_char_cells(c, MARGIN_LEFT + 100, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 120, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 125, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 145, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 150, current_y, year_str, 4)
        except:
            # В случае ошибки - пустые клетки
            draw_char_cells(c, MARGIN_LEFT + 100, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 120, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 125, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 145, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 150, current_y, "", 4)
    else:
        # Если дата не указана - пустые клетки
        draw_char_cells(c, MARGIN_LEFT + 100, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 120, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 125, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 145, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 150, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 200, current_y, "(дд.мм.гггг)")
    c.setFont(FONT_NAME, FONT_SIZE)
    current_y -= LINE_HEIGHT * 1.5
    
    # 2.6 Место рождения
    c.drawString(MARGIN_LEFT, current_y, "2.6. Место рождения:")
    birthplace = data.get('birthplace', '')
    draw_char_cells(c, MARGIN_LEFT + 100, current_y, birthplace, 40)
    current_y -= LINE_HEIGHT * 1.5
    
    # 2.7 Документ, удостоверяющий личность
    c.drawString(MARGIN_LEFT, current_y, "2.7. Документ, удостоверяющий личность:")
    current_y -= LINE_HEIGHT
    
    # Продолжение на следующей странице...
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Вид документа")
    c.setFont(FONT_NAME, FONT_SIZE)
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, "ПАСПОРТ", 20)
    current_y -= LINE_HEIGHT
    
    # Серия и номер
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Серия")
    c.setFont(FONT_NAME, FONT_SIZE)
    passport_series = data.get('passport_series', '')
    draw_char_cells(c, MARGIN_LEFT + 30, current_y, passport_series, 5)
    
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 90, current_y, "Номер")
    c.setFont(FONT_NAME, FONT_SIZE)
    passport_number = data.get('passport_number', '')
    draw_char_cells(c, MARGIN_LEFT + 130, current_y, passport_number, 10)
    current_y -= LINE_HEIGHT * 1.5

def create_page_2(c, data):
    """
    Создает вторую страницу уведомления по эталонному образцу
    """
    current_y = PAGE_HEIGHT - MARGIN_TOP
    
    # Продолжение документа, удостоверяющего личность
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Дата выдачи")
    c.setFont(FONT_NAME, FONT_SIZE)
    
    # Дата выдачи паспорта
    passport_issue_date = data.get('passport_issue_date', '')
    if passport_issue_date:
        try:
            if isinstance(passport_issue_date, str):
                if '.' in passport_issue_date:
                    day, month, year = passport_issue_date.split('.')
                elif '-' in passport_issue_date:
                    year, month, day = passport_issue_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = passport_issue_date.day
                month = passport_issue_date.month
                year = passport_issue_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 160, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 1.5
    
    # Кем выдан паспорт
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Кем выдан")
    c.setFont(FONT_NAME, FONT_SIZE)
    
    # Орган выдачи (в несколько строк если нужно)
    passport_issuer = data.get('passport_issuer', '')
    draw_char_cells(c, MARGIN_LEFT + 50, current_y, passport_issuer, 50)
    current_y -= LINE_HEIGHT * 1.5
    
    # Продолжение документа в нескольких строках при необходимости
    if len(passport_issuer) > 50:
        rest_issuer = passport_issuer[50:]
        draw_char_cells(c, MARGIN_LEFT, current_y, rest_issuer, 65)
        current_y -= LINE_HEIGHT * 1.5
    
    # 2.8 Миграционная карта
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "2.8. Миграционная карта (при наличии):")
    current_y -= LINE_HEIGHT
    
    # Номер карты
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Номер карты")
    c.setFont(FONT_NAME, FONT_SIZE)
    migration_card_number = data.get('migration_card_number', '')
    draw_char_cells(c, MARGIN_LEFT + 60, current_y, migration_card_number, 15)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата въезда
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Дата въезда")
    c.setFont(FONT_NAME, FONT_SIZE)
    
    # Заполняем дату въезда
    entry_date = data.get('entry_date', '')
    if entry_date:
        try:
            if isinstance(entry_date, str):
                if '.' in entry_date:
                    day, month, year = entry_date.split('.')
                elif '-' in entry_date:
                    year, month, day = entry_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = entry_date.day
                month = entry_date.month
                year = entry_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 160, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 1.5
    
    # Срок пребывания до
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Срок пребывания до")
    c.setFont(FONT_NAME, FONT_SIZE)
    
    # Заполняем срок пребывания
    stay_until_date = data.get('stay_until_date', '')
    if stay_until_date:
        try:
            if isinstance(stay_until_date, str):
                if '.' in stay_until_date:
                    day, month, year = stay_until_date.split('.')
                elif '-' in stay_until_date:
                    year, month, day = stay_until_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = stay_until_date.day
                month = stay_until_date.month
                year = stay_until_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 110, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 115, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 135, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 140, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 110, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 115, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 135, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 140, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT + 90, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 110, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 115, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 135, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 140, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 190, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 2
    
    # 2.9 Адрес постановки на учет по месту пребывания
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "2.9. Адрес постановки на учет по месту пребывания:")
    current_y -= LINE_HEIGHT
    
    # Населенный пункт
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Населенный пункт")
    c.setFont(FONT_NAME, FONT_SIZE)
    city = data.get('city', '')
    draw_char_cells(c, MARGIN_LEFT + 90, current_y, city, 40)
    current_y -= LINE_HEIGHT * 1.5
    
    # Улица, дом
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Улица, дом, корпус, квартира")
    c.setFont(FONT_NAME, FONT_SIZE)
    address = data.get('address', '')
    draw_char_cells(c, MARGIN_LEFT + 150, current_y, address, 35)
    current_y -= LINE_HEIGHT * 2
    
    # 2.10 Патент
    c.drawString(MARGIN_LEFT, current_y, "2.10. Патент на осуществление трудовой деятельности (при наличии)")
    current_y -= LINE_HEIGHT
    
    # Серия патента
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Серия")
    c.setFont(FONT_NAME, FONT_SIZE)
    patent_series = data.get('patent_series', '')
    draw_char_cells(c, MARGIN_LEFT + 40, current_y, patent_series, 5)
    
    # Номер патента
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 100, current_y, "Номер")
    c.setFont(FONT_NAME, FONT_SIZE)
    patent_number = data.get('patent_number', '')
    draw_char_cells(c, MARGIN_LEFT + 140, current_y, patent_number, 15)
    current_y -= LINE_HEIGHT * 1.5

def create_page_3(c, data):
    """
    Создает третью страницу уведомления по эталонному образцу
    """
    current_y = PAGE_HEIGHT - MARGIN_TOP
    
    # Продолжение патента
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Дата выдачи")
    c.setFont(FONT_NAME, FONT_SIZE)
    
    # Дата выдачи патента
    patent_issue_date = data.get('patent_issue_date', '')
    if patent_issue_date:
        try:
            if isinstance(patent_issue_date, str):
                if '.' in patent_issue_date:
                    day, month, year = patent_issue_date.split('.')
                elif '-' in patent_issue_date:
                    year, month, day = patent_issue_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = patent_issue_date.day
                month = patent_issue_date.month
                year = patent_issue_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 160, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 2
    
    # 2.11 Разрешение на работу
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "2.11. Разрешение на работу (при наличии)")
    current_y -= LINE_HEIGHT
    
    # Серия разрешения
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Серия")
    c.setFont(FONT_NAME, FONT_SIZE)
    permit_series = data.get('permit_series', '')
    draw_char_cells(c, MARGIN_LEFT + 40, current_y, permit_series, 5)
    
    # Номер разрешения
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 100, current_y, "Номер")
    c.setFont(FONT_NAME, FONT_SIZE)
    permit_number = data.get('permit_number', '')
    draw_char_cells(c, MARGIN_LEFT + 140, current_y, permit_number, 15)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата выдачи разрешения
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Дата выдачи")
    c.setFont(FONT_NAME, FONT_SIZE)
    
    # Заполняем дату выдачи разрешения
    permit_issue_date = data.get('permit_issue_date', '')
    if permit_issue_date:
        try:
            if isinstance(permit_issue_date, str):
                if '.' in permit_issue_date:
                    day, month, year = permit_issue_date.split('.')
                elif '-' in permit_issue_date:
                    year, month, day = permit_issue_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = permit_issue_date.day
                month = permit_issue_date.month
                year = permit_issue_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT + 60, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 80, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 85, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 105, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 160, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 2
    
    # 3. Сведения о трудовой деятельности
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "3. Сведения о трудовой деятельности иностранного гражданина или лица без гражданства:")
    current_y -= LINE_HEIGHT * 1.5
    
    # 3.1 Должность
    c.drawString(MARGIN_LEFT, current_y, "3.1. Должность:")
    position = data.get('position', '')
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, position, 40)
    current_y -= LINE_HEIGHT * 1.5
    
    # 3.2 Дата трудоустройства
    c.drawString(MARGIN_LEFT, current_y, "3.2. Дата заключения с иностранным гражданином или лицом без гражданства трудового договора или")
    current_y -= LINE_HEIGHT
    c.drawString(MARGIN_LEFT, current_y, "гражданско-правового договора на выполнение работ (оказание услуг):")
    current_y -= LINE_HEIGHT * 1.3
    
    # Дата
    work_start_date = data.get('work_start_date', '')
    if work_start_date:
        try:
            if isinstance(work_start_date, str):
                if '.' in work_start_date:
                    day, month, year = work_start_date.split('.')
                elif '-' in work_start_date:
                    year, month, day = work_start_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = work_start_date.day
                month = work_start_date.month
                year = work_start_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 20, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 25, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 45, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 50, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 20, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 25, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 45, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 50, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 20, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 25, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 45, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 50, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 80, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 1.5
    
    # 3.3 Тип договора
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "3.3. Трудовой договор/гражданско-правовой договор:")
    current_y -= LINE_HEIGHT
    
    # Вид договора
    c.drawString(MARGIN_LEFT, current_y, "Вид договора:")
    contract_type = data.get('contract_type', '')
    draw_char_cells(c, MARGIN_LEFT + 80, current_y, contract_type, 40)
    current_y -= LINE_HEIGHT * 1.5
    
    # Номер договора
    c.drawString(MARGIN_LEFT, current_y, "№:")
    contract_number = data.get('contract_number', '')
    draw_char_cells(c, MARGIN_LEFT + 20, current_y, contract_number, 15)
    current_y -= LINE_HEIGHT * 1.5

def create_page_4(c, data):
    """
    Создает четвертую страницу уведомления по эталонному образцу
    """
    current_y = PAGE_HEIGHT - MARGIN_TOP
    
    # Продолжение 3.3
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Дата:")
    
    # Дата договора
    contract_date = data.get('contract_date', '')
    if contract_date:
        try:
            if isinstance(contract_date, str):
                if '.' in contract_date:
                    day, month, year = contract_date.split('.')
                elif '-' in contract_date:
                    year, month, day = contract_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = contract_date.day
                month = contract_date.month
                year = contract_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 60, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 65, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 85, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 60, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 65, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 85, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT + 40, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 60, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 65, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 85, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 90, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 140, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 2
    
    # 3.4 Налоговый платеж
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "3.4. Сведения о платеже (налоге) на доходы физических лиц, платеже по выбранной на")
    current_y -= LINE_HEIGHT
    c.drawString(MARGIN_LEFT, current_y, "календарный год налоговой ставке в виде фиксированного авансового платежа:")
    current_y -= LINE_HEIGHT * 1.5
    
    # Номер квитанции/чека
    c.drawString(MARGIN_LEFT, current_y, "№ квитанции/чека:")
    income_tax_number = data.get('income_tax_number', '')
    draw_char_cells(c, MARGIN_LEFT + 100, current_y, income_tax_number, 25)
    current_y -= LINE_HEIGHT * 2
    
    # 4. Достоверность сведений
    c.drawString(MARGIN_LEFT, current_y, "4. Достоверность сведений, изложенных в настоящем уведомлении, подтверждаю:")
    current_y -= LINE_HEIGHT * 2
    
    # Место для подписи
    c.drawString(MARGIN_LEFT, current_y, "Подпись:")
    c.line(MARGIN_LEFT + 50, current_y, MARGIN_LEFT + 150, current_y)
    current_y -= LINE_HEIGHT * 2
    
    # Дата подписи
    c.drawString(MARGIN_LEFT, current_y, "Дата:")
    
    # Текущая дата как дата уведомления
    notification_date = data.get('notification_date', datetime.now().strftime("%d.%m.%Y"))
    if notification_date:
        try:
            if isinstance(notification_date, str):
                if '.' in notification_date:
                    day, month, year = notification_date.split('.')
                elif '-' in notification_date:
                    year, month, day = notification_date.split('-')
                else:
                    day, month, year = "", "", ""
            else:
                day = notification_date.day
                month = notification_date.month
                year = notification_date.year
            
            day_str = str(day).zfill(2)
            month_str = str(month).zfill(2)
            year_str = str(year)
            
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, day_str, 2)
            c.drawString(MARGIN_LEFT + 60, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 65, current_y, month_str, 2)
            c.drawString(MARGIN_LEFT + 85, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, year_str, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 60, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 65, current_y, "", 2)
            c.drawString(MARGIN_LEFT + 85, current_y + 2, ".")
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, "", 4)
    else:
        draw_char_cells(c, MARGIN_LEFT + 40, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 60, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 65, current_y, "", 2)
        c.drawString(MARGIN_LEFT + 85, current_y + 2, ".")
        draw_char_cells(c, MARGIN_LEFT + 90, current_y, "", 4)
    
    # Подсказка формата
    c.setFont(FONT_NAME, SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 140, current_y, "(дд.мм.гггг)")
    current_y -= LINE_HEIGHT * 2
    
    # Место печати
    c.setFont(FONT_NAME, FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "М.П. (при наличии)")
    current_y -= LINE_HEIGHT * 3
    
    # Дополнительная информация (в нижней части страницы)
    c.setFont(FONT_NAME, TINY_FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Уведомление о заключении трудового договора или гражданско-правового договора на выполнение работ")
    current_y -= LINE_HEIGHT * 0.8
    c.drawString(MARGIN_LEFT, current_y, "(оказание услуг) представляется работодателем или заказчиком работ (услуг) в подразделение органа")
    current_y -= LINE_HEIGHT * 0.8
    c.drawString(MARGIN_LEFT, current_y, "миграционной службы в субъекте Российской Федерации, на территории которого иностранный гражданин")
    current_y -= LINE_HEIGHT * 0.8
    c.drawString(MARGIN_LEFT, current_y, "или лицо без гражданства осуществляет трудовую деятельность, в течение 3 рабочих дней со дня")
    current_y -= LINE_HEIGHT * 0.8
    c.drawString(MARGIN_LEFT, current_y, "заключения такого договора.")

def generate_template_pdf(data, output_path="template_notification.pdf"):
    """
    Генерирует PDF форму уведомления, максимально приближенную к эталонному образцу.
    
    Args:
        data: Словарь с данными для заполнения формы
        output_path: Путь для сохранения PDF файла
    
    Returns:
        str: Путь к созданному PDF файлу
    """
    try:
        # Создаем Canvas с явным указанием кодировки
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # Устанавливаем базовые настройки документа
        c._doc.setProducer("Template PDF Generator")
        c._doc.setAuthor("EasyMigrateBot")
        c._doc.setTitle("Уведомление об осуществлении трудовой деятельности")
        
        # Создаем страницы максимально приближенные к эталону
        create_page_1(c, data)
        c.showPage()  # переход на страницу 2
        
        create_page_2(c, data)
        c.showPage()  # переход на страницу 3
        
        create_page_3(c, data)
        c.showPage()  # переход на страницу 4
        
        create_page_4(c, data)
        
        # Сохраняем PDF
        c.save()
        
        logger.info(f"PDF шаблон по эталону создан: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Тестовые данные
    test_data = {
        # Информация о работодателе
        "employer_type": "legal",
        "company_name": "ООО ТЕСТОВАЯ КОМПАНИЯ",
        "company_address": "Г. МОСКВА, ТВЕРСКАЯ УЛИЦА, Д. 1",
        "company_inn": "1234567890",
        "company_telephone": "+7(999)123-45-67",
        
        # Информация об иностранном гражданине
        "lastname": "АБДУЛЛАЕВ",
        "firstname": "АБРОР",
        "middlename": "ЯНГИБАЙ УГЛИ",
        "citizenship": "УЗБЕКИСТАН",
        "birthdate": "01.01.1990",
        "birthplace": "УЗБЕКИСТАН, Г. ТАШКЕНТ",
        
        # Паспортные данные
        "passport_series": "AB",
        "passport_number": "1234567",
        "passport_issue_date": "01.01.2015",
        "passport_issuer": "МВД РЕСПУБЛИКИ УЗБЕКИСТАН",
        
        # Информация о въезде/пребывании
        "migration_card_number": "1234567890",
        "entry_date": "10.01.2023",
        "stay_until_date": "10.01.2024",
        
        # Адрес пребывания
        "city": "МОСКВА",
        "district": "ЦЕНТРАЛЬНЫЙ",
        "address": "ТВЕРСКАЯ УЛИЦА, Д. 1, КВ. 123",
        
        # Информация о работе
        "position": "СПЕЦИАЛИСТ ПО ТЕСТИРОВАНИЮ",
        "work_start_date": "01.08.2025",
        "contract_type": "ТРУДОВОЙ ДОГОВОР",
        "contract_number": "123-ТД",
        "contract_date": "01.08.2025",
        
        # Патент и разрешение
        "patent_number": "123456",
        "patent_issue_date": "01.02.2023",
        "permit_series": "AB",
        "permit_number": "123456",
        "permit_issue_date": "01.02.2023",
        
        # Дополнительная информация
        "income_tax_number": "12345",
        "notification_date": "04.08.2025",
    }
    
    # Генерируем PDF по эталону
    pdf_path = generate_template_pdf(test_data, "template_notification_exact.pdf")
    print(f"PDF создан: {pdf_path}")
