#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для создания PDF-формы уведомления по эталонному образцу МВД.
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Размеры страницы A4 в пунктах (595.27 x 841.89)
PAGE_WIDTH, PAGE_HEIGHT = A4

# Константы для отступов и позиционирования
MARGIN_LEFT = 45
MARGIN_RIGHT = 45
MARGIN_TOP = 50
MARGIN_BOTTOM = 50
LINE_HEIGHT = 14

# Размеры клеток для ввода данных
CELL_WIDTH = 8.5
CELL_HEIGHT = 11.5
SMALL_CELL_WIDTH = 6
SMALL_CELL_HEIGHT = 9

# Размеры шрифтов
FONT_SIZE = 9
SMALL_FONT_SIZE = 8
TINY_FONT_SIZE = 7

# Регистрируем шрифты с поддержкой кириллицы
def register_fonts():
    """Регистрирует шрифты для использования в PDF"""
    font_registered = False
    font_name = "Helvetica"  # По умолчанию
    
    # Определяем операционную систему и пути к шрифтам
    system = platform.system()
    if system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/cour.ttf",  # Courier New
        ]
    elif system == "Darwin":  # macOS
        font_paths = [
            "/Library/Fonts/Arial.ttf",
            "/Library/Fonts/Times New Roman.ttf",
            "/Library/Fonts/Courier New.ttf",
        ]
    else:  # Linux и другие
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    
    # Пробуем зарегистрировать шрифт
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # Регистрируем шрифт для основного текста
                pdfmetrics.registerFont(TTFont("FormFont", font_path))
                # Регистрируем шрифт для кириллицы
                pdfmetrics.registerFont(TTFont("CyrillicFont", font_path))
                font_name = "FormFont"
                font_registered = True
                logger.info(f"Зарегистрирован шрифт: {font_path}")
                break
            except Exception as e:
                logger.warning(f"Не удалось зарегистрировать шрифт {font_path}: {e}")
    
    if not font_registered:
        logger.warning("Не удалось зарегистрировать шрифт с поддержкой кириллицы, используем стандартный")
    
    return font_name

# Функция для рисования клеток с символами
def draw_char_cells(c, x, y, text, num_cells, cell_width=CELL_WIDTH, cell_height=CELL_HEIGHT, font_size=SMALL_FONT_SIZE):
    """
    Рисует сетку клеток и заполняет их символами текста.
    Поддерживает кириллицу.
    """
    # Подготавливаем текст
    clean_text = str(text).strip().upper() if text else ""
    
    # Преобразуем в строку если это не строка
    try:
        if not isinstance(clean_text, str):
            clean_text = str(clean_text, "utf-8")
    except Exception as e:
        logger.warning(f"Ошибка преобразования текста: {e}")
    
    # Рисуем клетки и символы
    for i in range(num_cells):
        cell_x = x + i * cell_width
        
        # Рисуем границы клетки
        c.rect(cell_x, y, cell_width, cell_height)
        
        # Помещаем символ в клетку если он есть
        if i < len(clean_text):
            char = clean_text[i]
            try:
                # Используем соответствующий шрифт для символа
                font_to_use = "CyrillicFont" if ord(char) > 127 else "FormFont"
                c.setFont(font_to_use, font_size)
                
                # Центрируем символ в клетке
                char_width = c.stringWidth(char, font_to_use, font_size)
                char_x = cell_x + (cell_width - char_width) / 2
                char_y = y + (cell_height - font_size) / 2
                
                # Рисуем символ
                c.drawString(char_x, char_y, char)
                
            except Exception as e:
                logger.warning(f"Ошибка при отображении символа '{char}': {e}")
                try:
                    c.setFont("Helvetica", font_size)
                    c.drawCentredString(cell_x + cell_width/2, y + cell_height/3, "?")
                except:
                    pass

# Функция для рисования checkbox
def draw_checkbox(c, x, y, checked=False, size=8):
    """Рисует checkbox"""
    c.rect(x, y, size, size)
    if checked:
        c.setFont("FormFont", 7)
        c.drawString(x + 1.5, y + 1, "V")

# Функция для обработки даты
def format_date(date_str):
    """Форматирует дату в формат ДД.ММ.ГГГГ"""
    if not date_str:
        return ""
    
    # Если дата уже в нужном формате
    if isinstance(date_str, str) and len(date_str.split('.')) == 3:
        return date_str
    
    # Если дата передана как объект datetime
    if hasattr(date_str, 'strftime'):
        return date_str.strftime('%d.%m.%Y')
    
    # В других случаях пробуем конвертировать
    try:
        dt = datetime.strptime(str(date_str), '%Y-%m-%d')
        return dt.strftime('%d.%m.%Y')
    except:
        try:
            dt = datetime.strptime(str(date_str), '%d/%m/%Y')
            return dt.strftime('%d.%m.%Y')
        except:
            return str(date_str)

# Создание страниц формы уведомления
def create_page_1(c, data):
    """Создает первую страницу уведомления по эталону"""
    # Заголовок по центру
    c.setFont("FormFont", 12)
    title = "УВЕДОМЛЕНИЕ О ЗАКЛЮЧЕНИИ ТРУДОВОГО ДОГОВОРА"
    title_width = c.stringWidth(title, "FormFont", 12)
    c.drawString((PAGE_WIDTH - title_width) / 2, PAGE_HEIGHT - MARGIN_TOP, title)
    
    # Подзаголовок по центру
    c.setFont("FormFont", 10)
    subtitle = "ИЛИ ГРАЖДАНСКО-ПРАВОВОГО ДОГОВОРА НА ВЫПОЛНЕНИЕ РАБОТ (ОКАЗАНИЕ УСЛУГ)"
    subtitle_width = c.stringWidth(subtitle, "FormFont", 10)
    c.drawString((PAGE_WIDTH - subtitle_width) / 2, PAGE_HEIGHT - MARGIN_TOP - 15, subtitle)
    
    subtitle2 = "С ИНОСТРАННЫМ ГРАЖДАНИНОМ ИЛИ ЛИЦОМ БЕЗ ГРАЖДАНСТВА"
    subtitle2_width = c.stringWidth(subtitle2, "FormFont", 10)
    c.drawString((PAGE_WIDTH - subtitle2_width) / 2, PAGE_HEIGHT - MARGIN_TOP - 30, subtitle2)
    
    # Текущая позиция по Y
    current_y = PAGE_HEIGHT - MARGIN_TOP - 60
    
    # Сведения о работодателе
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Сведения о работодателе, заказчике работ (услуг):")
    current_y -= LINE_HEIGHT * 1.5
    
    # Юридическое лицо
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "1. Полное наименование:")
    current_y -= LINE_HEIGHT
    
    # Название компании в клетках
    draw_char_cells(c, MARGIN_LEFT, current_y, data.get("company_name", ""), 60)
    current_y -= LINE_HEIGHT * 1.5
    
    # Адрес
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "2. Адрес (место нахождения):")
    current_y -= LINE_HEIGHT
    
    # Адрес компании в клетках
    draw_char_cells(c, MARGIN_LEFT, current_y, data.get("company_address", ""), 60)
    current_y -= LINE_HEIGHT * 1.5
    
    # ИНН
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "3. ИНН:")
    draw_char_cells(c, MARGIN_LEFT + 50, current_y, data.get("company_inn", ""), 12)
    current_y -= LINE_HEIGHT * 1.5
    
    # Телефон
    c.drawString(MARGIN_LEFT, current_y, "4. Телефон:")
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, data.get("company_telephone", ""), 15)
    current_y -= LINE_HEIGHT * 2
    
    # Сведения об иностранном гражданине
    c.drawString(MARGIN_LEFT, current_y, "Сведения об иностранном гражданине (лице без гражданства), с которым заключен трудовой договор или")
    current_y -= LINE_HEIGHT
    c.drawString(MARGIN_LEFT, current_y, "гражданско-правовой договор на выполнение работ (оказание услуг):")
    current_y -= LINE_HEIGHT * 1.5
    
    # ФИО
    c.drawString(MARGIN_LEFT, current_y, "1. Фамилия:")
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, data.get("lastname", ""), 25)
    current_y -= LINE_HEIGHT * 1.5
    
    c.drawString(MARGIN_LEFT, current_y, "2. Имя:")
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, data.get("firstname", ""), 25)
    current_y -= LINE_HEIGHT * 1.5
    
    c.drawString(MARGIN_LEFT, current_y, "3. Отчество:")
    draw_char_cells(c, MARGIN_LEFT + 70, current_y, data.get("middlename", ""), 25)
    c.setFont("FormFont", SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 290, current_y + 3, "(при наличии)")
    current_y -= LINE_HEIGHT * 1.5
    
    # Гражданство
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "4. Гражданство:")
    draw_char_cells(c, MARGIN_LEFT + 80, current_y, data.get("citizenship", ""), 25)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата рождения
    c.drawString(MARGIN_LEFT, current_y, "5. Дата рождения:")
    
    # Форматируем и разбиваем дату на компоненты
    birthdate = format_date(data.get("birthdate", ""))
    if birthdate:
        try:
            day, month, year = birthdate.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT + 100, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 120, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 125, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 145, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 150, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 100, current_y, birthdate, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT + 100, current_y, "", 10)
    
    # Место рождения
    current_y -= LINE_HEIGHT * 1.5
    c.drawString(MARGIN_LEFT, current_y, "6. Место рождения:")
    draw_char_cells(c, MARGIN_LEFT, current_y - LINE_HEIGHT, data.get("birthplace", ""), 60)
    
    # Нижний колонтитул
    c.setFont("FormFont", SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, MARGIN_BOTTOM, "Страница 1 из 4")

def create_page_2(c, data):
    """Создает вторую страницу уведомления по эталону"""
    # Текущая позиция по Y
    current_y = PAGE_HEIGHT - MARGIN_TOP
    
    # Документ, удостоверяющий личность
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "7. Документ, удостоверяющий личность:")
    current_y -= LINE_HEIGHT
    
    # Паспорт
    passport_series = data.get("passport_series", "")
    passport_number = data.get("passport_number", "")
    
    c.drawString(MARGIN_LEFT + 20, current_y, "Серия")
    draw_char_cells(c, MARGIN_LEFT + 60, current_y, passport_series, 8)
    
    c.drawString(MARGIN_LEFT + 140, current_y, "Номер")
    draw_char_cells(c, MARGIN_LEFT + 180, current_y, passport_number, 10)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата выдачи
    passport_issue_date = format_date(data.get("passport_issue_date", ""))
    c.drawString(MARGIN_LEFT + 20, current_y, "Дата выдачи")
    
    if passport_issue_date:
        try:
            day, month, year = passport_issue_date.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 110, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 115, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 135, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 140, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, passport_issue_date, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT + 90, current_y, "", 10)
    
    current_y -= LINE_HEIGHT * 1.5
    
    # Кем выдан
    c.drawString(MARGIN_LEFT + 20, current_y, "Кем выдан")
    draw_char_cells(c, MARGIN_LEFT, current_y - LINE_HEIGHT, data.get("passport_issuer", ""), 60)
    current_y -= LINE_HEIGHT * 3
    
    # Миграционная карта
    c.drawString(MARGIN_LEFT, current_y, "8. Номер миграционной карты:")
    draw_char_cells(c, MARGIN_LEFT + 170, current_y, data.get("migration_card_number", ""), 15)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата въезда
    c.drawString(MARGIN_LEFT, current_y, "9. Дата въезда в Российскую Федерацию:")
    
    entry_date = format_date(data.get("entry_date", ""))
    if entry_date:
        try:
            day, month, year = entry_date.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT + 230, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 250, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 255, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 275, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 280, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 230, current_y, entry_date, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT + 230, current_y, "", 10)
    
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата пребывания
    c.drawString(MARGIN_LEFT, current_y, "10. Дата окончания срока временного пребывания в Российской Федерации:")
    current_y -= LINE_HEIGHT
    
    stay_until_date = format_date(data.get("stay_until_date", ""))
    if stay_until_date:
        try:
            day, month, year = stay_until_date.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 20, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 25, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 45, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 50, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT, current_y, stay_until_date, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT, current_y, "", 10)
    
    current_y -= LINE_HEIGHT * 2
    
    # Адрес пребывания
    c.drawString(MARGIN_LEFT, current_y, "11. Адрес постановки на учет по месту пребывания или адрес регистрации по месту жительства:")
    current_y -= LINE_HEIGHT
    
    # Город и район
    city = data.get("city", "")
    district = data.get("district", "")
    
    draw_char_cells(c, MARGIN_LEFT, current_y, city, 30)
    c.setFont("FormFont", SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 80, current_y - LINE_HEIGHT, "(город, район)")
    
    draw_char_cells(c, MARGIN_LEFT + 250, current_y, district, 30)
    c.drawString(MARGIN_LEFT + 330, current_y - LINE_HEIGHT, "(субъект Российской Федерации)")
    
    current_y -= LINE_HEIGHT * 2
    
    # Улица, дом, квартира
    draw_char_cells(c, MARGIN_LEFT, current_y, data.get("address", ""), 60)
    c.setFont("FormFont", SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT + 180, current_y - LINE_HEIGHT, "(улица, дом, квартира)")
    
    current_y -= LINE_HEIGHT * 2
    
    # Сведения о работе
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Сведения о разрешении на работу или патенте:")
    current_y -= LINE_HEIGHT * 1.5
    
    # Наличие разрешения на работу или патента
    c.drawString(MARGIN_LEFT, current_y, "12. Наличие разрешения на работу или патента:")
    current_y -= LINE_HEIGHT
    
    # Чекбоксы для выбора
    offset_x = MARGIN_LEFT + 20
    c.drawString(offset_x, current_y, "Имеется")
    draw_checkbox(c, offset_x - 15, current_y, checked=True)
    
    offset_x = MARGIN_LEFT + 120
    c.drawString(offset_x, current_y, "Не требуется")
    draw_checkbox(c, offset_x - 15, current_y, checked=False)
    
    # Нижний колонтитул
    c.setFont("FormFont", SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, MARGIN_BOTTOM, "Страница 2 из 4")

def create_page_3(c, data):
    """Создает третью страницу уведомления по эталону"""
    # Текущая позиция по Y
    current_y = PAGE_HEIGHT - MARGIN_TOP
    
    # Серия и номер патента
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "13. Серия и номер патента:")
    
    patent_number = data.get("patent_number", "")
    draw_char_cells(c, MARGIN_LEFT + 150, current_y, patent_number, 15)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата выдачи патента
    c.drawString(MARGIN_LEFT, current_y, "14. Дата выдачи патента:")
    
    patent_issue_date = format_date(data.get("patent_issue_date", ""))
    if patent_issue_date:
        try:
            day, month, year = patent_issue_date.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT + 130, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 150, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 155, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 175, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 180, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 130, current_y, patent_issue_date, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT + 130, current_y, "", 10)
    
    current_y -= LINE_HEIGHT * 1.5
    
    # Профессия
    c.drawString(MARGIN_LEFT, current_y, "15. Профессия (специальность, должность, вид трудовой деятельности):")
    current_y -= LINE_HEIGHT
    
    draw_char_cells(c, MARGIN_LEFT, current_y, data.get("position", ""), 60)
    current_y -= LINE_HEIGHT * 1.5
    
    # Трудовой или гражданско-правовой договор
    c.drawString(MARGIN_LEFT, current_y, "16. Трудовой договор или гражданско-правовой договор на выполнение работ (оказание услуг):")
    current_y -= LINE_HEIGHT
    
    contract_type = data.get("contract_type", "")
    contract_number = data.get("contract_number", "")
    
    c.drawString(MARGIN_LEFT + 20, current_y, "№")
    draw_char_cells(c, MARGIN_LEFT + 40, current_y, contract_number, 15)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата заключения
    c.drawString(MARGIN_LEFT, current_y, "17. Дата заключения:")
    
    contract_date = format_date(data.get("contract_date", ""))
    if contract_date:
        try:
            day, month, year = contract_date.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 130, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 135, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 155, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 160, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 110, current_y, contract_date, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT + 110, current_y, "", 10)
    
    current_y -= LINE_HEIGHT * 1.5
    
    # Срок действия договора
    c.drawString(MARGIN_LEFT, current_y, "18. Срок действия договора:")
    current_y -= LINE_HEIGHT
    
    # Дата начала работы
    work_start_date = format_date(data.get("work_start_date", ""))
    c.drawString(MARGIN_LEFT + 20, current_y, "с")
    
    if work_start_date:
        try:
            day, month, year = work_start_date.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 60, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 65, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 85, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, work_start_date, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT + 40, current_y, "", 10)
    
    current_y -= LINE_HEIGHT * 2
    
    # Сведения об уплате НДФЛ
    c.drawString(MARGIN_LEFT, current_y, "19. Сведения об уплате налога на доходы физических лиц:")
    current_y -= LINE_HEIGHT
    
    c.drawString(MARGIN_LEFT + 20, current_y, "19.1 Патент:")
    current_y -= LINE_HEIGHT
    
    c.drawString(MARGIN_LEFT + 40, current_y, "№")
    draw_char_cells(c, MARGIN_LEFT + 60, current_y, data.get("income_tax_number", ""), 15)
    
    c.drawString(MARGIN_LEFT + 200, current_y, "Сумма (руб.)")
    draw_char_cells(c, MARGIN_LEFT + 280, current_y, "", 10)
    current_y -= LINE_HEIGHT * 1.5
    
    # Нижний колонтитул
    c.setFont("FormFont", SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, MARGIN_BOTTOM, "Страница 3 из 4")

def create_page_4(c, data):
    """Создает четвертую страницу уведомления по эталону"""
    # Текущая позиция по Y
    current_y = PAGE_HEIGHT - MARGIN_TOP
    
    # Продолжение формы
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "19.2 В порядке, предусмотренном международным договором Российской Федерации:")
    current_y -= LINE_HEIGHT * 1.5
    
    # Сумма 19.2
    c.drawString(MARGIN_LEFT + 20, current_y, "Сумма (руб.)")
    draw_char_cells(c, MARGIN_LEFT + 100, current_y, "", 10)
    current_y -= LINE_HEIGHT * 2
    
    # Достоверность
    c.setFont("FormFont", FONT_SIZE + 1)
    c.drawString(MARGIN_LEFT, current_y, "Достоверность сведений, изложенных в настоящем уведомлении, подтверждаю:")
    current_y -= LINE_HEIGHT * 2
    
    # Подпись и дата
    c.setFont("FormFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, current_y, "Подпись лица, уполномоченного от имени работодателя")
    c.line(MARGIN_LEFT + 270, current_y, MARGIN_LEFT + 370, current_y)
    current_y -= LINE_HEIGHT * 1.5
    
    # Дата уведомления
    notification_date = format_date(data.get("notification_date", datetime.now().strftime('%d.%m.%Y')))
    c.drawString(MARGIN_LEFT, current_y, "Дата")
    
    if notification_date:
        try:
            day, month, year = notification_date.split('.')
            # День
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, day, 2)
            c.drawString(MARGIN_LEFT + 60, current_y, ".")
            # Месяц
            draw_char_cells(c, MARGIN_LEFT + 65, current_y, month, 2)
            c.drawString(MARGIN_LEFT + 85, current_y, ".")
            # Год
            draw_char_cells(c, MARGIN_LEFT + 90, current_y, year, 4)
        except:
            draw_char_cells(c, MARGIN_LEFT + 40, current_y, notification_date, 10)
    else:
        draw_char_cells(c, MARGIN_LEFT + 40, current_y, "", 10)
    
    current_y -= LINE_HEIGHT * 2
    
    # МП (место печати)
    c.drawString(MARGIN_LEFT, current_y, "М.П.")
    c.drawString(MARGIN_LEFT + 30, current_y, "(при наличии печати)")
    
    current_y -= LINE_HEIGHT * 4
    
    # Отметки
    c.drawString(MARGIN_LEFT, current_y, "Отметка территориального органа МВД России:")
    current_y -= LINE_HEIGHT * 1.5
    
    # Регистрационный номер
    c.drawString(MARGIN_LEFT + 20, current_y, "Регистрационный номер")
    c.line(MARGIN_LEFT + 150, current_y, MARGIN_LEFT + 350, current_y)
    current_y -= LINE_HEIGHT * 2
    
    # Дата постановки на учет
    c.drawString(MARGIN_LEFT + 20, current_y, "Дата постановки на учет")
    c.drawString(MARGIN_LEFT + 170, current_y, "\"____\"____________20___г.")
    current_y -= LINE_HEIGHT * 2
    
    # Должность
    c.drawString(MARGIN_LEFT + 20, current_y, "Должность, Ф.И.О. должностного лица, принявшего уведомление")
    c.line(MARGIN_LEFT + 370, current_y, PAGE_WIDTH - MARGIN_RIGHT, current_y)
    current_y -= LINE_HEIGHT * 1.5
    c.line(MARGIN_LEFT, current_y, PAGE_WIDTH - MARGIN_RIGHT, current_y)
    current_y -= LINE_HEIGHT * 1.5
    
    # Подпись
    c.drawString(MARGIN_LEFT + 20, current_y, "Подпись должностного лица, принявшего уведомление")
    c.line(MARGIN_LEFT + 320, current_y, PAGE_WIDTH - MARGIN_RIGHT, current_y)
    
    # Нижний колонтитул
    c.setFont("FormFont", SMALL_FONT_SIZE)
    c.drawString(MARGIN_LEFT, MARGIN_BOTTOM, "Страница 4 из 4")

def create_notification_pdf_by_template(data, output_path):
    """
    Создает PDF уведомление точно по эталонному образцу МВД.
    
    Args:
        data (dict): Словарь с данными для заполнения формы
        output_path (str): Путь для сохранения сгенерированного PDF
    
    Returns:
        str: Путь к созданному файлу
    """
    try:
        # Регистрируем шрифты
        font_name = register_fonts()
        
        # Создаем Canvas с указанием кодировки
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # Устанавливаем базовые настройки документа
        c._doc.setProducer("EasyMigrateBot PDF Generator")
        c._doc.setAuthor("EasyMigrateBot")
        c._doc.setTitle("Уведомление о заключении трудового договора")
        
        # Создаем страницы по эталону
        create_page_1(c, data)
        c.showPage()  # переход на страницу 2
        
        create_page_2(c, data)
        c.showPage()  # переход на страницу 3
        
        create_page_3(c, data)
        c.showPage()  # переход на страницу 4
        
        create_page_4(c, data)
        
        # Сохраняем PDF
        c.save()
        logger.info(f"Создан PDF по эталону: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_notification_from_db_data(user_data, output_dir="notifications"):
    """
    Создает PDF уведомление по эталону на основе данных из базы данных.
    
    Args:
        user_data (dict): Данные пользователя из базы данных
        output_dir (str): Директория для сохранения сгенерированных PDF
    
    Returns:
        str: Путь к созданному файлу
    """
    try:
        # Используем новый формат официального уведомления МВД
        from utils.mvd_notification_pdf import create_notification_from_db_data as create_mvd_notification
        return create_mvd_notification(user_data, output_dir)
    
    except Exception as e:
        logger.error(f"Ошибка при создании уведомления из данных БД: {e}")
        import traceback
        traceback.print_exc()
        return None

# Тестирование функции генерации PDF
if __name__ == "__main__":
    # Тестовые данные
    test_data = {
        # Информация о работодателе
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
        "work_start_date": datetime.now().strftime("%d.%m.%Y"),
        "contract_type": "ТРУДОВОЙ ДОГОВОР",
        "contract_number": "123-ТД",
        "contract_date": datetime.now().strftime("%d.%m.%Y"),
        
        # Патент и разрешение
        "patent_number": "123456",
        "patent_issue_date": "01.02.2023",
        
        # Дополнительная информация
        "income_tax_number": "12345",
        "notification_date": datetime.now().strftime("%d.%m.%Y"),
    }
    
    # Генерируем PDF
    output_path = "template_notification_test.pdf"
    create_notification_pdf_by_template(test_data, output_path)
    print(f"Создан тестовый PDF: {output_path}")
