import os
import platform
import logging
import re
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
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
CELL_WIDTH = 13.5
CELL_HEIGHT = 13.5

# Размеры шрифтов
FONT_SIZE = 9
SMALL_FONT_SIZE = 8
TINY_FONT_SIZE = 7

# Данные по регионам для автозаполнения
REGION_DATA = {
    "ДМИТРОВ": {
        "mvd_name": "ОТДЕЛ ПО ВОПРОСАМ МИГРАЦИИ УМВД РОССИИ ПО ДМИТРОВСКОМУ ГОРОДСКОМУ ОКРУГУ",
        "work_address": "МОСКОВСКАЯ ОБЛАСТЬ, ДМИТРОВСКИЙ ГОРОДСКОЙ ОКРУГ, УЛ. ПОЧТОВАЯ Д.16, КОРПУС 1"
    },
    "ДОЛГОПРУДНЫЙ": {
        "mvd_name": "ОТДЕЛ ПО ВОПРОСАМ МИГРАЦИИ МУ МВД РОССИИ \"МЫТИЩИНСКОЕ\"",
        "work_address": "МОСКОВСКАЯ ОБЛАСТЬ, Г. ДОЛГОПРУДНЫЙ, ЛИХАЧЕВСКОЕ ШОССЕ, Д. 27"
    },
    "ВОЛЖСКИЙ": {
        "mvd_name": "УПРАВЛЕНИЕ ПО ВОПРОСАМ МИГРАЦИИ ГУ МВД РОССИИ ПО ВОЛГОГРАДСКОЙ ОБЛАСТИ",
        "work_address": "ВОЛГОГРАДСКАЯ ОБЛАСТЬ, Г. ВОЛЖСКИЙ, ПРОСПЕКТ МЕТАЛЛУРГОВ, Д. 6"
    }
}

# База данных компаний для автозаполнения по ИНН
COMPANY_DATA = {
    "7733450363": {
        "full_name": "ООО \"ЭЛЕНВКВ\"",
        "legal_address": "Г. МОСКВА, ВН. ТЕР. Г. МУНИЦИПАЛЬНЫЙ ОКРУГ ЮЖНОЕ ТУШИНО, УЛ. ВАСИЛИЯ ПЕТУШКОВА, Д. 8, ПОМЕЩЕНИЕ 1/1А",
        "inn": "7733450363",
        "ogrn": "1247700503885",
        "kpp": "773301001"
    }
    # Здесь можно добавить другие компании по мере необходимости
}

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

def parse_document_series_number(full_number):
    """
    Разделяет серию и номер документа.
    Например: FK0207865 -> серия: FK, номер: 0207865
    Поддерживает и числовые серии: 342500015683 -> серия: 34, номер: 2500015683
    """
    if not full_number:
        return "", ""
    
    full_number = str(full_number).strip().upper()
    
    # Специальная обработка для патентов с числовой серией (например, 34)
    # Если строка начинается с 2-3 цифр, за которыми следует много цифр
    if full_number.isdigit() and len(full_number) > 5:
        # Для патентов: первые 2 цифры - серия, остальное - номер
        if len(full_number) >= 10:  # Длинный номер патента
            return full_number[:2], full_number[2:]
    
    # Находим где заканчиваются буквы и начинаются цифры
    series = ""
    number = ""
    
    for i, char in enumerate(full_number):
        if char.isdigit():
            series = full_number[:i]
            number = full_number[i:]
            break
    else:
        # Если только буквы или только цифры
        if full_number.isalpha():
            series = full_number
        else:
            number = full_number
    
    return series, number

def get_region_data(city):
    """
    Возвращает данные региона по названию города.
    """
    if not city:
        return REGION_DATA["ДМИТРОВ"]  # По умолчанию
    
    city_upper = str(city).strip().upper()
    
    for region_key in REGION_DATA.keys():
        if region_key in city_upper:
            return REGION_DATA[region_key]
    
    # Если не найдено точное совпадение, ищем частичное
    if "ДМИТРОВ" in city_upper:
        return REGION_DATA["ДМИТРОВ"]
    elif "ДОЛГОПРУДН" in city_upper:
        return REGION_DATA["ДОЛГОПРУДНЫЙ"]
    elif "ВОЛЖСК" in city_upper:
        return REGION_DATA["ВОЛЖСКИЙ"]
    
    return REGION_DATA["ДМИТРОВ"]  # По умолчанию

def get_company_data_by_inn(inn):
    """
    Получает данные компании по ИНН для автозаполнения пункта 11.
    
    Args:
        inn (str): ИНН компании
        
    Returns:
        dict: Данные компании или пустой словарь, если компания не найдена
    """
    inn_clean = str(inn).strip() if inn else ""
    return COMPANY_DATA.get(inn_clean, {
        "full_name": "",
        "legal_address": "",
        "inn": "",
        "ogrn": "",
        "kpp": ""
    })

def sanitize_filename(filename):
    """
    Очищает имя файла от недопустимых символов для Windows.
    Заменяет недопустимые символы на безопасные аналоги.
    """
    if not filename:
        return ""
    
    # Недопустимые символы в именах файлов Windows: < > : " | ? * /
    # Также добавляем \ и некоторые управляющие символы
    invalid_chars = r'[<>:"|?*\\\/]'
    
    # Заменяем недопустимые символы на подчеркивания
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Заменяем пробелы рядом с подчеркиваниями
    sanitized = re.sub(r'\s+_+\s*', '_', sanitized)
    sanitized = re.sub(r'\s*_+\s+', '_', sanitized)
    
    # Убираем множественные подчеркивания
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Убираем подчеркивания и пробелы в начале и конце
    sanitized = sanitized.strip('_ ')
    
    # Ограничиваем длину имени файла (без расширения)
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized

def prepare_data_for_pdf(data):
    """
    Подготавливает данные для PDF, добавляя автозаполнение по региону.
    """
    prepared_data = data.copy()
    
    # Получаем данные региона
    city = data.get("city", "")
    region_data = get_region_data(city)
    
    # Автозаполнение MVD органа
    prepared_data["mvd_office"] = region_data["mvd_name"]
    
    # Автозаполнение адреса работы если не указан
    if not prepared_data.get("work_address"):
        prepared_data["work_address"] = region_data["work_address"]
    
    # Обработка серии и номера паспорта
    passport_full = data.get("passport_number", "") or data.get("passport_series", "")
    if passport_full:
        series, number = parse_document_series_number(passport_full)
        prepared_data["passport_series"] = series
        prepared_data["passport_number"] = number
    
    # ИСПРАВЛЕНИЕ 1: Обработка серии и номера патента из правильного поля БД
    patent_full = ""
    if data.get("patent_series"):
        patent_full = str(data.get("patent_series", "")) + str(data.get("patent_number", ""))
    elif data.get("patent_number"):
        patent_full = str(data.get("patent_number", ""))
    
    if patent_full:
        series, number = parse_document_series_number(patent_full)
        prepared_data["patent_series"] = series  # Правильное поле для серии патента
        prepared_data["patent_number"] = number
        prepared_data["patent_blank_series"] = series  # Для совместимости
    
    # ИСПРАВЛЕНИЕ 7: Обработка серии и номера ДМС - полный номер в число
    dms_number = data.get("dms_number", "") or data.get("insurance_number", "")
    
    # Если есть полный номер ДМС, помещаем его целиком в поле номера
    if dms_number:
        prepared_data["insurance_series"] = ""  # Серия остается пустой
        prepared_data["insurance_number"] = str(dms_number)  # Весь номер в поле номера
    else:
        # Fallback на старую логику для обратной совместимости
        dms_series = data.get("dms_series", "")
        if dms_series:
            prepared_data["insurance_series"] = str(dms_series)
        else:
            prepared_data["insurance_series"] = ""
        prepared_data["insurance_number"] = ""
    
    # ИСПРАВЛЕНИЕ 1: Страховая организация напрямую из insurance_company
    insurance_company_value = data.get("insurance_company", "")
    
    # Важная проверка 1: убеждаемся, что в поле страховой компании не попал email
    if insurance_company_value and "@" in insurance_company_value:
        # Если в поле страховой компании оказался email, перемещаем его в insurance_expiry
        # и очищаем поле страховой компании
        if not data.get("insurance_expiry"):
            data["insurance_expiry"] = insurance_company_value
        insurance_company_value = ""
    
    # Важная проверка 2: убеждаемся, что в поле страховой компании не попал номер телефона
    # Проверяем типичные форматы телефонных номеров: +7..., 8..., (XXX)..., XX-XX-XX
    import re
    if insurance_company_value and re.search(r'^\+?\d[\d\-\(\) ]{5,20}$', insurance_company_value):
        # Если похоже на телефон, перемещаем в поле контактного телефона
        # и очищаем поле страховой компании
        data["contact_phone"] = insurance_company_value
        insurance_company_value = ""
    
    if insurance_company_value:
        prepared_data["insurance_company"] = insurance_company_value
    else:
        # Если нет данных, используем стандартный текст
        prepared_data["insurance_company"] = "АЛЬФАСТРАХОВАНИЕ"
    
    # ИСПРАВЛЕНИЕ 4: Контактный email из поля insurance_expiry для пункта 10
    insurance_expiry_value = data.get("insurance_expiry", "")
    
    # Проверяем, является ли значение в поле insurance_expiry email-адресом
    if insurance_expiry_value and "@" in str(insurance_expiry_value):
        # Используем insurance_expiry как email для пункта 10
        prepared_data["contact_email"] = insurance_expiry_value
    elif data.get("contact_email"):
        # Для обратной совместимости используем contact_email
        prepared_data["contact_email"] = data.get("contact_email") 
    else:
        prepared_data["contact_email"] = ""
    
    # ИСПРАВЛЕНИЕ 6: Для компании ООО "ЭЛЕНВКВ" НЕ добавляем email в адрес
    # Email будет добавлен отдельно после ИНН, ОГРН, КПП
    
    # ИСПРАВЛЕНИЕ 3: Контактный телефон всегда +79858036952
    prepared_data["contact_phone"] = "+79858036952"
        
    # ИСПРАВЛЕНИЕ: Дата выдачи ДМС из insurance_date
    if data.get("insurance_date"):
        prepared_data["insurance_date"] = data.get("insurance_date")
    
    # НОВОЕ: Автозаполнение данных компании по ИНН для пункта 11
    company_inn = data.get("inn", "")
    if company_inn:
        company_data = get_company_data_by_inn(company_inn)
        if company_data and company_data.get("full_name"):
            # Автозаполняем поля компании если они не заполнены
            if not prepared_data.get("company_name"):
                prepared_data["company_name"] = company_data.get("full_name", "")
            if not prepared_data.get("company_address"):
                prepared_data["company_address"] = company_data.get("legal_address", "")
            if not prepared_data.get("ogrn"):
                prepared_data["ogrn"] = company_data.get("ogrn", "")
            if not prepared_data.get("kpp"):
                prepared_data["kpp"] = company_data.get("kpp", "")
            # ИНН уже есть в данных, но убедимся что он заполнен
            if not prepared_data.get("inn"):
                prepared_data["inn"] = company_data.get("inn", "")
    
    return prepared_data

# Функция для непрерывного заполнения клеточек (как на официальном образце)
def draw_continuous_char_cells(c, x, y, all_text, cells_per_line, total_lines, cell_width=CELL_WIDTH, cell_height=CELL_HEIGHT, font_size=FONT_SIZE):
    """
    Заполняет клеточки непрерывно, как на официальном образце.
    Весь текст заполняется последовательно через все доступные строки.
    
    Args:
        c: Canvas объект ReportLab
        x, y: Координаты начала первой строки
        all_text: Весь текст для заполнения
        cells_per_line: Количество клеточек в одной строке
        total_lines: Общее количество строк
        cell_width, cell_height: Размеры клеточек
        font_size: Размер шрифта
        
    Returns:
        int: Количество использованных строк
    """
    if not all_text:
        # Рисуем пустые клеточки
        for line in range(total_lines):
            current_y = y - (line * (cell_height + 5))
            draw_char_cells(c, x, current_y, "", cells_per_line, cell_width, cell_height, font_size)
        return total_lines
    
    # Подготавливаем весь текст как одну строку
    clean_text = str(all_text).strip().upper()
    
    # ИСПРАВЛЕНИЕ: Более умная разбивка для максимального использования места
    lines = []
    
    # Заполняем символы подряд через все строки (как на первом скриншоте)
    for i in range(0, len(clean_text), cells_per_line):
        line_text = clean_text[i:i + cells_per_line]
        lines.append(line_text)
        if len(lines) >= total_lines:
            break
    
    # ВАЖНО: Если данные не помещаются в указанное количество строк,
    # продолжаем заполнение (как на первом скриншоте)
    while len(lines) < total_lines:
        lines.append("")
    
    # Рисуем все строки
    for i, line in enumerate(lines):
        current_y = y - (i * (cell_height + 5))
        draw_char_cells(c, x, current_y, line, cells_per_line, cell_width, cell_height, font_size)
    
    return len(lines)

# Функция для автоматического переноса длинного текста на несколько строк клеточек
def draw_multiline_char_cells(c, x, y, text, cells_per_line, max_lines=3, cell_width=CELL_WIDTH, cell_height=CELL_HEIGHT, font_size=FONT_SIZE):
    """
    Рисует текст с автоматическим переносом на несколько строк клеточек.
    Разбивает по словам для более читаемого отображения.
    
    Args:
        c: Canvas объект ReportLab
        x, y: Координаты начала первой строки
        text: Текст для отображения
        cells_per_line: Количество клеточек в одной строке
        max_lines: Максимальное количество строк
        cell_width, cell_height: Размеры клеточек
        font_size: Размер шрифта
        
    Returns:
        int: Количество использованных строк
    """
    if not text:
        # Рисуем пустые клеточки
        for line in range(max_lines):
            current_y = y - (line * (cell_height + 5))
            draw_char_cells(c, x, current_y, "", cells_per_line, cell_width, cell_height, font_size)
        return max_lines
    
    # Подготавливаем текст
    clean_text = str(text).strip().upper()
    
    # Разбиваем текст на строки по словам (более умный алгоритм)
    lines = []
    words = clean_text.split()
    current_line = ""
    
    for word in words:
        # Пробуем добавить слово к текущей строке
        test_line = current_line + (" " if current_line else "") + word
        
        if len(test_line) <= cells_per_line:
            # Слово помещается - добавляем
            current_line = test_line
        else:
            # Слово не помещается
            if current_line:
                # Сохраняем текущую строку и начинаем новую
                lines.append(current_line)
                current_line = word
                if len(lines) >= max_lines - 1:  # Оставляем место для последней строки
                    break
            else:
                # Очень длинное слово - разбиваем по символам
                while len(word) > cells_per_line:
                    lines.append(word[:cells_per_line])
                    word = word[cells_per_line:]
                    if len(lines) >= max_lines - 1:
                        break
                current_line = word
    
    # Добавляем оставшуюся часть
    if current_line and len(lines) < max_lines:
        lines.append(current_line)
    
    # Заполняем пустыми строками если нужно
    while len(lines) < max_lines:
        lines.append("")
    
    # Рисуем строки
    lines_used = 0
    for i, line in enumerate(lines[:max_lines]):
        current_y = y - (i * (cell_height + 5))
        draw_char_cells(c, x, current_y, line, cells_per_line, cell_width, cell_height, font_size)
        lines_used += 1
    
    return lines_used

# Функция для рисования клеток с символами
def draw_char_cells(c, x, y, text, num_cells, cell_width=CELL_WIDTH, cell_height=CELL_HEIGHT, font_size=FONT_SIZE):
    """
    Рисует сетку клеток и заполняет их символами текста.
    Поддерживает кириллицу с улучшенной читаемостью.
    """
    # Подготавливаем текст
    clean_text = str(text).strip().upper() if text else ""
    
    # Преобразуем в строку если это не строка
    try:
        if not isinstance(clean_text, str):
            clean_text = str(clean_text, "utf-8")
    except Exception as e:
        logger.warning(f"Ошибка преобразования текста: {e}")
    
    # Увеличиваем размер шрифта для лучшей читаемости
    display_font_size = font_size + 1
    
    # Рисуем клетки и символы
    for i in range(num_cells):
        cell_x = x + i * cell_width
        
        # Рисуем границы клетки с более толстыми линиями
        c.setLineWidth(0.8)  # Немного толще стандартной линии
        c.rect(cell_x, y, cell_width, cell_height)
        
        # Помещаем символ в клетку если он есть
        if i < len(clean_text):
            char = clean_text[i]
            try:
                # Используем кириллический шрифт для всех символов для единообразия
                c.setFont("CyrillicFont", display_font_size)
                
                # Центрируем символ в клетке более точно
                char_width = c.stringWidth(char, "CyrillicFont", display_font_size)
                char_x = cell_x + (cell_width - char_width) / 2
                char_y = y + (cell_height - display_font_size) / 2 + 1  # Немного выше для лучшего вида
                
                # Устанавливаем черный цвет для максимального контраста
                c.setFillColor(colors.black)
                
                # Рисуем символ
                c.drawString(char_x, char_y, char)
                
            except Exception as e:
                logger.warning(f"Ошибка при отображении символа '{char}': {e}")
                try:
                    c.setFont("CyrillicFont", display_font_size)
                    c.setFillColor(colors.black)
                    c.drawCentredString(cell_x + cell_width/2, y + cell_height/3, "?")
                except:
                    pass
    
    # Возвращаем толщину линии к стандартной
    c.setLineWidth(0.5)

# Функция для рисования линий (без клеток)
def draw_lines(c, x, y, width, num_lines=1, line_spacing=20):
    """
    Рисует горизонтальные линии для заполнения (без клеток).
    """
    for i in range(num_lines):
        line_y = y - i * line_spacing
        c.line(x, line_y, x + width, line_y)

def draw_checkbox(c, x, y, checked=False, size=13.5):
    """Рисует checkbox"""
    c.rect(x, y, size, size)
    if checked:
        c.setFont("FormFont", 12)
        c.drawString(x + 3, y + 2, "X")

# Функция для обработки даты
def format_date(date_str):
    """Форматирует дату в формат ДД.ММ.ГГГГ"""
    if not date_str:
        return ""
    
    # Если дата уже в нужном формате
    if isinstance(date_str, str) and len(date_str.split('.')) == 3:
        return date_str
    
    try:
        # Если дата - объект datetime
        if hasattr(date_str, 'strftime'):
            return date_str.strftime('%d.%m.%Y')
        
        # Пробуем парсить из строки
        from dateutil import parser
        dt = parser.parse(str(date_str))
        return dt.strftime('%d.%m.%Y')
    except:
        return str(date_str)

def parse_date_with_month_names(date_str):
    """
    Парсит дату с месяцами в буквенном формате и возвращает компоненты.
    Например: "10 июля 2025 г." -> день: "10", месяц: "07", год: "2025"
    """
    if not date_str:
        return "", "", ""
    
    # Словарь месяцев
    months = {
        'января': '01', 'янв': '01',
        'февраля': '02', 'фев': '02',
        'марта': '03', 'мар': '03',
        'апреля': '04', 'апр': '04',
        'мая': '05', 'май': '05',
        'июня': '06', 'июн': '06',
        'июля': '07', 'июл': '07',
        'августа': '08', 'авг': '08',
        'сентября': '09', 'сен': '09',
        'октября': '10', 'окт': '10',
        'ноября': '11', 'ноя': '11',
        'декабря': '12', 'дек': '12'
    }
    
    date_str = str(date_str).lower().strip()
    
    # Удаляем "г." если есть
    date_str = date_str.replace('г.', '').strip()
    
    # Разбиваем на части
    parts = date_str.split()
    
    if len(parts) >= 3:
        day = parts[0].zfill(2)  # Добавляем ведущий ноль если нужно
        month_name = parts[1]
        year = parts[2]
        
        # Ищем месяц в словаре
        month = months.get(month_name, "01")
        
        return day, month, year
    
    # Если не удалось парсить, пробуем стандартную функцию
    formatted = format_date(date_str)
    if formatted and len(formatted.split('.')) == 3:
        parts = formatted.split('.')
        return parts[0], parts[1], parts[2]
    
    return "", "", ""

# Создаем страницу 1
def create_page_1(c, data):
    """Создает первую страницу: Личные данные + патент"""
    # Регистрируем шрифты
    font_name = register_fonts()
    
    # Устанавливаем базовый шрифт
    c.setFont(font_name, FONT_SIZE)
    
    # Заголовок - Приложение № 1
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 50, "Приложение № 1")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 70, "к приказу МВД России")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 90, "от 05.09.2023 г. № 655")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 110, "Форма")
    
    # Заголовок - УВЕДОМЛЕНИЕ
    c.setFont("CyrillicFont", 12)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 150, "УВЕДОМЛЕНИЕ")
    c.setFont("CyrillicFont", 10)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 170, "об осуществлении трудовой деятельности иностранным гражданином")
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 190, "или лицом без гражданства, получившим патент")
    
    # Текст - Настоящее уведомление представляется в:
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, PAGE_HEIGHT - 230, "Настоящее уведомление представляется в:")
    
    # Клетки для ввода территориального органа МВД (автозаполнение)
    y_pos = PAGE_HEIGHT - 250
    mvd_office = data.get("mvd_office", "")
    
    # Разбиваем название на строки, если оно длинное
    mvd_lines = []
    if len(mvd_office) > 42:
        words = mvd_office.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 42:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    mvd_lines.append(current_line)
                current_line = word
        if current_line:
            mvd_lines.append(current_line)
    else:
        mvd_lines.append(mvd_office)
    
    # Заполняем максимум 3 строки
    for i in range(3):
        text = mvd_lines[i] if i < len(mvd_lines) else ""
        draw_char_cells(c, MARGIN_LEFT, y_pos - i * (CELL_HEIGHT + 5), text, 42)
    
    # Пояснение под клетками
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 3 * (CELL_HEIGHT + 5) - 5, 
                      "(наименование территориального органа МВД России на региональном и районном уровнях)")

    # 1.1. Фамилия
    y_pos -= 3 * (CELL_HEIGHT + 5) + 25
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "1.1. Фамилия")
    draw_char_cells(c, MARGIN_LEFT + 100, y_pos, data.get("lastname", ""), 34)
    
    # 1.2. Имя
    y_pos -= CELL_HEIGHT + 10
    c.drawString(MARGIN_LEFT, y_pos + 5, "1.2. Имя")
    draw_char_cells(c, MARGIN_LEFT + 100, y_pos, data.get("firstname", ""), 34)
    
    # 1.3. Отчество
    y_pos -= CELL_HEIGHT + 10
    c.drawString(MARGIN_LEFT, y_pos + 5, "1.3. Отчество")
    c.drawString(MARGIN_LEFT, y_pos - 10, "(при наличии)")
    draw_char_cells(c, MARGIN_LEFT + 100, y_pos, data.get("middlename", ""), 34)
    
    # 1.4. Гражданство
    y_pos -= CELL_HEIGHT + 20
    c.drawString(MARGIN_LEFT, y_pos + 5, "1.4. Гражданство")
    draw_char_cells(c, MARGIN_LEFT + 100, y_pos, data.get("citizenship", ""), 34)
    
    # 1.5. Дата рождения:
    y_pos -= CELL_HEIGHT + 15
    birthdate = format_date(data.get("birthdate", ""))
    day = birthdate.split(".")[0] if len(birthdate.split(".")) > 0 else ""
    month = birthdate.split(".")[1] if len(birthdate.split(".")) > 1 else ""
    year = birthdate.split(".")[2] if len(birthdate.split(".")) > 2 else ""
    
    c.drawString(MARGIN_LEFT, y_pos + 5, "1.5. Дата рождения:")
    
    # День
    draw_char_cells(c, MARGIN_LEFT + 100, y_pos, day, 2)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + 100 + CELL_WIDTH, y_pos - 15, "(число)")
    
    # Месяц
    draw_char_cells(c, MARGIN_LEFT + 100 + 3*CELL_WIDTH, y_pos, month, 2)
    c.drawCentredString(MARGIN_LEFT + 100 + 4*CELL_WIDTH, y_pos - 15, "(месяц)")
    
    # Год
    draw_char_cells(c, MARGIN_LEFT + 100 + 6*CELL_WIDTH, y_pos, year, 4)
    c.drawCentredString(MARGIN_LEFT + 100 + 8*CELL_WIDTH, y_pos - 15, "(год)")
    
    # 1.6. Документ, удостоверяющий личность
    y_pos -= CELL_HEIGHT + 20
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "1.6. Документ, удостоверяющий")
    c.drawString(MARGIN_LEFT, y_pos - 10, "личность:")
    
    # Название документа
    draw_char_cells(c, MARGIN_LEFT + 150, y_pos, data.get("document_type", "ПАСПОРТ"), 22)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + 250, y_pos - 15, "(наименование)")
    
    # Серия и номер
    y_pos -= CELL_HEIGHT + 20
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "Серия")
    draw_char_cells(c, MARGIN_LEFT + 50, y_pos, data.get("passport_series", ""), 7)
    c.drawString(MARGIN_LEFT + 150, y_pos + 5, "№")
    draw_char_cells(c, MARGIN_LEFT + 170, y_pos, data.get("passport_number", ""), 9)
    
    # Дата выдачи паспорта
    y_pos -= CELL_HEIGHT + 20
    issue_date = format_date(data.get("issue_date", ""))
    day = issue_date.split(".")[0] if len(issue_date.split(".")) > 0 else ""
    month = issue_date.split(".")[1] if len(issue_date.split(".")) > 1 else ""
    year = issue_date.split(".")[2] if len(issue_date.split(".")) > 2 else ""
    
    c.drawString(MARGIN_LEFT, y_pos + 5, "Дата выдачи")
    
    # День
    draw_char_cells(c, MARGIN_LEFT + 70, y_pos, day, 2)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + 70 + CELL_WIDTH, y_pos - 15, "(число)")
    
    # Месяц
    draw_char_cells(c, MARGIN_LEFT + 70 + 3*CELL_WIDTH, y_pos, month, 2)
    c.drawCentredString(MARGIN_LEFT + 70 + 4*CELL_WIDTH, y_pos - 15, "(месяц)")
    
    # Год
    draw_char_cells(c, MARGIN_LEFT + 70 + 6*CELL_WIDTH, y_pos, year, 4)
    c.drawCentredString(MARGIN_LEFT + 70 + 8*CELL_WIDTH, y_pos - 15, "(год)")
    
    # Кем выдан (одна строка)
    y_pos -= CELL_HEIGHT + 20
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "Кем выдан")
    draw_char_cells(c, MARGIN_LEFT, y_pos - 25, data.get("passport_issued_by", ""), 42)

# Создаем страницу 2
def create_page_2(c, data):
    """Создает вторую страницу: Патент + профессия + место работы"""
    # Регистрируем шрифты
    font_name = register_fonts()
    
    # Устанавливаем базовый шрифт
    c.setFont("CyrillicFont", FONT_SIZE)
    
    # 2. Сведения о патенте
    y_pos = PAGE_HEIGHT - 70
    c.drawString(MARGIN_LEFT, y_pos + 5, "2. Сведения о патенте, на основании которого иностранный гражданин (лицо")
    c.drawString(MARGIN_LEFT, y_pos - 15, "без гражданства) осуществляет трудовую деятельность")
    
    # Серия, номер и дата выдачи патента
    y_pos -= 50
    patent_date = format_date(data.get("patent_date", ""))
    day = patent_date.split(".")[0] if len(patent_date.split(".")) > 0 else ""
    month = patent_date.split(".")[1] if len(patent_date.split(".")) > 1 else ""
    year = patent_date.split(".")[2] if len(patent_date.split(".")) > 2 else ""
    
    c.drawString(MARGIN_LEFT, y_pos + 5, "Серия")
    draw_char_cells(c, MARGIN_LEFT + 50, y_pos, data.get("patent_series", ""), 7)  # ИСПРАВЛЕНИЕ 1: Правильное поле
    
    c.drawString(MARGIN_LEFT + 150, y_pos + 5, "№")
    draw_char_cells(c, MARGIN_LEFT + 170, y_pos, data.get("patent_number", ""), 10)
    
    c.drawString(MARGIN_LEFT + 350, y_pos + 5, "Дата")
    c.drawString(MARGIN_LEFT + 350, y_pos - 15, "выдачи")
    
    # День
    draw_char_cells(c, MARGIN_LEFT + 400, y_pos, day, 2)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + 400 + CELL_WIDTH, y_pos - 25, "(число)")
    
    # Месяц
    draw_char_cells(c, MARGIN_LEFT + 400 + 3*CELL_WIDTH, y_pos, month, 2)
    c.drawCentredString(MARGIN_LEFT + 400 + 4*CELL_WIDTH, y_pos - 25, "(месяц)")
    
    # Год
    draw_char_cells(c, MARGIN_LEFT + 400 + 6*CELL_WIDTH, y_pos, year, 4)
    c.drawCentredString(MARGIN_LEFT + 400 + 8*CELL_WIDTH, y_pos - 25, "(год)")
    
    # 3. Профессия
    y_pos -= CELL_HEIGHT + 50
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "3. Профессия (специальность, должность, вид трудовой деятельности) по трудовому")
    c.drawString(MARGIN_LEFT, y_pos - 15, "или гражданско-правовому договору:")
    
    # Большое поле для профессии (свободное, без клеток)
    y_pos -= 30
    position = data.get("position", "")
    c.setFont("CyrillicFont", 10)
    draw_char_cells(c, MARGIN_LEFT, y_pos, position, 42)
    draw_char_cells(c, MARGIN_LEFT, y_pos - CELL_HEIGHT - 5, "", 42)
    
    # 4. Сведения о месте осуществления трудовой деятельности
    y_pos -= CELL_HEIGHT + 30
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "4. Сведения о месте осуществления трудовой деятельности")
    
    # ИСПРАВЛЕНИЕ 2: Адрес работы (правильная разбивка на строки)
    y_pos -= CELL_HEIGHT + 10
    work_address = data.get("work_address", "")
    
    # Разбиваем адрес на строки для лучшего отображения
    work_address_lines = []
    if len(work_address) > 42:
        words = work_address.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 42:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    work_address_lines.append(current_line)
                current_line = word
        if current_line:
            work_address_lines.append(current_line)
    else:
        work_address_lines.append(work_address)
    
    # Выводим максимум 2 строки для адреса
    for i in range(2):
        line_text = work_address_lines[i] if i < len(work_address_lines) else ""
        draw_char_cells(c, MARGIN_LEFT, y_pos - i * (CELL_HEIGHT + 5), line_text, 42)
    
    # Пояснение к адресу
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 2*(CELL_HEIGHT + 5) - 5, 
                      "(населенный пункт, улица, № дома (строение), № комнаты (квартиры, помещения) (при наличии)")
    
    # 5. Трудовая деятельность осуществляется
    y_pos -= 2*(CELL_HEIGHT + 5) + 30
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "5. Трудовая деятельность осуществляется")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT - 50, y_pos + 5, "(нужное отметить")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos + 5, "X")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT - 20, y_pos + 5, "или")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos + 5, "V")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT + 10, y_pos + 5, "):")
    
    c.drawString(MARGIN_LEFT, y_pos - 15, "иностранным гражданином (лицом")
    c.drawString(MARGIN_LEFT, y_pos - 35, "без гражданства) на основании")
    
    # Чекбоксы для типа договора
    y_pos -= 60
    contract_type = data.get("contract_type", "ТРУДОВОЙ").upper()
    is_labor = "ТРУДОВ" in contract_type
    is_civil = "ГРАЖДАНСК" in contract_type
    is_verbal = "УСТ" in contract_type
    
    draw_checkbox(c, MARGIN_LEFT + 10, y_pos, checked=is_labor)
    c.drawString(MARGIN_LEFT + 30, y_pos + 5, "– трудового договора")
    
    y_pos -= CELL_HEIGHT + 10
    draw_checkbox(c, MARGIN_LEFT + 10, y_pos, checked=is_civil and not is_verbal)
    c.drawString(MARGIN_LEFT + 30, y_pos + 5, "– гражданско-правового договора на выполнение работ (оказание услуг)")
    
    y_pos -= CELL_HEIGHT + 10
    draw_checkbox(c, MARGIN_LEFT + 10, y_pos, checked=is_verbal)
    c.drawString(MARGIN_LEFT + 30, y_pos + 5, "– гражданско-правового договора на выполнение работ (оказание услуг), заключенного в устной форме")
    
    # ИСПРАВЛЕНИЕ 6: Пункт 6 для всех типов договоров согласно официальной форме
    y_pos -= CELL_HEIGHT + 20
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "6. Дата заключения гражданско-правового договора на")
    c.drawString(MARGIN_LEFT, y_pos - 15, "выполнение работ (оказание услуг) (указывается в")
    c.drawString(MARGIN_LEFT, y_pos - 35, "случае заключения в устной форме)")
    
    # ИСПРАВЛЕНИЕ: Дата из contract_date всегда заполняется
    contract_date = data.get("contract_date", "")
    if contract_date:
        day, month, year = parse_date_with_month_names(contract_date)
    else:
        day, month, year = "", "", ""
    
    # День
    y_pos -= 60
    draw_char_cells(c, MARGIN_LEFT, y_pos, day, 2)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + CELL_WIDTH, y_pos - 15, "(число)")
    
    # Месяц
    draw_char_cells(c, MARGIN_LEFT + 3*CELL_WIDTH, y_pos, month, 2)
    c.drawCentredString(MARGIN_LEFT + 4*CELL_WIDTH, y_pos - 15, "(месяц)")
    
    # Год
    draw_char_cells(c, MARGIN_LEFT + 6*CELL_WIDTH, y_pos, year, 4)
    c.drawCentredString(MARGIN_LEFT + 8*CELL_WIDTH, y_pos - 15, "(год)")
    
    y_pos -= CELL_HEIGHT + 30
    
    # 7. ИНН
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "7. ИНН")
    draw_char_cells(c, MARGIN_LEFT + 70, y_pos, data.get("inn", ""), 12)
    
    # 8. Сведения о полисе
    y_pos -= CELL_HEIGHT + 20
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "8. Сведения о действующем договоре (полисе) добровольного медицинского страхования,")
    c.drawString(MARGIN_LEFT, y_pos - 15, "либо договоре о предоставлении платных медицинских услуг, либо действующем полисе")
    c.drawString(MARGIN_LEFT, y_pos - 35, "обязательного медицинского страхования:")
    
    # ИСПРАВЛЕНИЕ 3: Название страхования (увеличиваем до 6 строк для полного отображения)
    y_pos -= CELL_HEIGHT + 40
    
    # Проверяем значение insurance_company перед использованием
    insurance_text = data.get("insurance_company", "")
    
    # Дополнительная проверка, что значение не является номером телефона
    import re
    if re.search(r'^\+?\d[\d\-\(\) ]{5,20}$', insurance_text):
        # Если это телефон, не используем его как страховую компанию
        insurance_text = "АЛЬФАСТРАХОВАНИЕ"
    
    # Разбиваем текст ДМС на строки с учетом длины
    insurance_lines = []
    if len(insurance_text) > 42:
        words = insurance_text.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 42:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    insurance_lines.append(current_line)
                current_line = word
        if current_line:
            insurance_lines.append(current_line)
    else:
        insurance_lines.append(insurance_text)
    
    # Выводим максимум 6 строк для полного ДМС текста
    for i in range(6):
        line_text = insurance_lines[i] if i < len(insurance_lines) else ""
        draw_char_cells(c, MARGIN_LEFT, y_pos - i * (CELL_HEIGHT + 5), line_text, 42)
    
    # Пояснение к полису (сдвигаем ниже из-за 6 строк)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 6*(CELL_HEIGHT + 5) - 5, "(наименование и реквизиты документа)")

# Создаем страницу 3
def create_page_3(c, data):
    """Создает третью страницу: Серия и номер полиса + контакты + заказчик"""
    # Регистрируем шрифты
    font_name = register_fonts()
    
    # Устанавливаем базовый шрифт
    c.setFont("CyrillicFont", FONT_SIZE)
    
    # Продолжение 8. Серия и номер полиса
    y_pos = PAGE_HEIGHT - 70
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "Серия")
    draw_char_cells(c, MARGIN_LEFT + 50, y_pos, data.get("insurance_series", ""), 5)
    
    c.drawString(MARGIN_LEFT + 150, y_pos + 5, "№")
    draw_char_cells(c, MARGIN_LEFT + 170, y_pos, data.get("insurance_number", ""), 12)
    
    # Дата выдачи полиса
    y_pos -= CELL_HEIGHT + 20
    insurance_date = format_date(data.get("insurance_date", ""))
    day = insurance_date.split(".")[0] if len(insurance_date.split(".")) > 0 else ""
    month = insurance_date.split(".")[1] if len(insurance_date.split(".")) > 1 else ""
    year = insurance_date.split(".")[2] if len(insurance_date.split(".")) > 2 else ""
    
    c.drawString(MARGIN_LEFT, y_pos + 5, "Дата выдачи")
    
    # День
    draw_char_cells(c, MARGIN_LEFT + 80, y_pos, day, 2)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + 80 + CELL_WIDTH, y_pos - 15, "(число)")
    
    # Месяц
    draw_char_cells(c, MARGIN_LEFT + 80 + 3*CELL_WIDTH, y_pos, month, 2)
    c.drawCentredString(MARGIN_LEFT + 80 + 4*CELL_WIDTH, y_pos - 15, "(месяц)")
    
    # Год
    draw_char_cells(c, MARGIN_LEFT + 80 + 6*CELL_WIDTH, y_pos, year, 4)
    c.drawCentredString(MARGIN_LEFT + 80 + 8*CELL_WIDTH, y_pos - 15, "(год)")
    
    # 9. Контактный телефон
    y_pos -= CELL_HEIGHT + 30
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "9. Контактный телефон")
    draw_char_cells(c, MARGIN_LEFT + 150, y_pos, data.get("contact_phone", ""), 25)
    
    # 10. Адрес электронной почты
    y_pos -= CELL_HEIGHT + 20
    c.drawString(MARGIN_LEFT, y_pos + 5, "10. Адрес электронной")
    c.drawString(MARGIN_LEFT, y_pos - 15, "почты")
    draw_char_cells(c, MARGIN_LEFT + 150, y_pos - 5, data.get("contact_email", ""), 34)
    
    # ИСПРАВЛЕНИЕ 7: Пункт 11 должен отображаться всегда (по форме из скриншота)
    contract_type = data.get("contract_type", "ТРУДОВОЙ").upper()
    is_verbal = "УСТ" in contract_type
    
    y_pos -= CELL_HEIGHT + 40
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "11. Сведения о заказчике работ (услуг) (указывается в случае заключения гражданско-")
    c.drawString(MARGIN_LEFT, y_pos - 15, "правового договора на выполнение работ (оказание услуг) в устной форме)")
    
    # ИСПРАВЛЕНИЕ: используем НЕПРЕРЫВНОЕ заполнение данных компании (как на образце)
    y_pos -= CELL_HEIGHT + 20
    
    # ИСПРАВЛЕНИЕ: формируем данные компании БЕЗ ИНН, ОГРН, КПП на странице 3
    # ИНН, ОГРН, КПП будут только на странице 4 отдельно
    company_name = data.get("company_name", "")
    company_address = data.get("company_address", "")
    
    # Формируем текст только с названием и адресом (без ИНН, ОГРН, КПП)
    all_company_data = ""
    if company_name:
        all_company_data += company_name
    if company_address:
        if all_company_data:
            all_company_data += " "
        all_company_data += company_address
    
    # Используем customer_info для устных договоров если нет данных компании
    customer_info = data.get("customer_info", "") if is_verbal else ""
    if not all_company_data and customer_info:
        all_company_data = customer_info
    
    # Заполняем непрерывно через все 3 строки (как на образце)
    lines_used = draw_continuous_char_cells(c, MARGIN_LEFT, y_pos, all_company_data, 42, total_lines=3)
    
    # Сдвигаем позицию вниз с учетом использованных строк
    y_pos -= (lines_used * (CELL_HEIGHT + 5))
    
    # Пояснительный текст под всеми строками
    y_pos -= 15
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "(полное наименование юридического лица/филиала иностранного юридического лица/представительства")
    
    y_pos -= 15
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "иностранного юридического лица, фамилия, имя, отчество (при их наличии) индивидуального")
    
    y_pos -= 15
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "предпринимателя/адвоката, учредившего адвокатский кабинет/частного нотариуса/физического лица –")
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                      "гражданина Российской Федерации)")

# Создаем страницу 4
def create_page_4(c, data):
    """Создает четвертую страницу: Продолжение пункта 11"""
    # Регистрируем шрифты
    font_name = register_fonts()
    
    # Устанавливаем базовый шрифт
    c.setFont("CyrillicFont", FONT_SIZE)
    
    # Начальная позиция Y - продолжение пункта 11 без заголовка
    y_pos = PAGE_HEIGHT - 70
    
    # ИСПРАВЛЕНИЕ: На странице 4 заполняем продолжение данных + ИНН/ОГРН/КПП + email
    company_name = data.get("company_name", "")
    company_address = data.get("company_address", "")
    # ИСПРАВЛЕНИЕ: используем правильное поле для ИНН компании
    inn = data.get("company_inn", "") or data.get("inn", "")
    ogrn = data.get("ogrn", "")
    kpp = data.get("kpp", "")
    
    # Формируем ТОЛЬКО название и адрес компании (без ИНН, ОГРН, КПП)
    name_and_address = ""
    if company_name:
        name_and_address += company_name
    if company_address:
        if name_and_address:
            name_and_address += " "
        name_and_address += company_address
    
    # Рассчитываем что уже было на предыдущей странице (3 строки по 42 символа = 126 символов)
    chars_on_page3 = 126
    remaining_text = name_and_address[chars_on_page3:] if len(name_and_address) > chars_on_page3 else ""
    
    # Формируем данные для страницы 4
    page4_text = ""
    
    # Сначала добавляем продолжение названия/адреса, если есть
    if remaining_text:
        page4_text = remaining_text
    
    # ИСПРАВЛЕНИЕ: ИНН, ОГРН, КПП НЕ добавляем здесь, так как они будут добавлены позже в отдельной строке
    # ЗАКОММЕНТИРОВАНО для предотвращения дублирования
    # if inn and ogrn and kpp:
    #     inn_ogrn_kpp = f"ИНН {inn} ОГРН {ogrn} КПП {kpp}"
    #     
    #     # Добавляем с пробелом если уже есть текст
    #     if page4_text:
    #         page4_text += " "
    #     page4_text += inn_ogrn_kpp
    
    # Добавляем email только для ООО "ЭЛЕНВКВ" (после ИНН, ОГРН, КПП)
    if data.get("company_inn") == "7733450363" or data.get("inn") == "7733450363":
        if page4_text:
            page4_text += " "
        page4_text += "fms.gosuslugi@yandex.ru"
    
    # Заполняем данные на странице 4 (3 строки)
    if page4_text:
        lines_used = draw_continuous_char_cells(c, MARGIN_LEFT, y_pos, page4_text, 42, total_lines=3)
        y_pos -= (lines_used * (CELL_HEIGHT + 5))
    else:
        # Если данных нет - рисуем пустые строки
        lines_used = draw_continuous_char_cells(c, MARGIN_LEFT, y_pos, "", 42, total_lines=3)
        y_pos -= (lines_used * (CELL_HEIGHT + 5))
    
    # Пояснительные тексты под всеми строками пункта 11
    y_pos -= 20
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "(для юридических лиц – государственный регистрационный номер записи в Едином государственном")
    
    y_pos -= 15
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "реестре юридических лиц, для филиалов или представительств иностранных юридических лиц –")
    
    y_pos -= 15
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "номер документа, подтверждающего факт аккредитации филиала или представительства иностранного")
    
    # Седьмая строка клеточек
    y_pos -= 20
    draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
    
    # Пояснительный текст под седьмой строкой
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "юридического лица, для индивидуальных предпринимателей – государственный регистрационный")
    
    # Восьмая строка клеточек
    y_pos -= 20
    draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
    
    # Пояснительный текст под восьмой строкой
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "номер записи в Едином государственном реестре индивидуальных предпринимателей,")
    
    # Девятая строка клеточек
    y_pos -= 20
    draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
    
    # Пояснительный текст под девятой строкой
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "для частных нотариусов – номер лицензии на право нотариальной деятельности, для физического лица –")
    
    # Десятая строка клеточек
    y_pos -= 20
    draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
    
    # Пояснительный текст под десятой строкой
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "наименование документа, удостоверяющего личность, его серия и номер, кем и когда выдан)")
    
    # ИСПРАВЛЕНИЕ 5: Одиннадцатая строка клеточек - ИНН, ОГРН и КПП
    y_pos -= 20
    # Формируем строку с ИНН, ОГРН и КПП для отображения на странице 4
    inn = data.get("company_inn", "") or data.get("inn", "")
    ogrn = data.get("ogrn", "")
    kpp = data.get("kpp", "")
    
    inn_ogrn_kpp_line = ""
    if inn:
        inn_ogrn_kpp_line += f"ИНН {inn}"
    if ogrn:
        if inn_ogrn_kpp_line:
            inn_ogrn_kpp_line += " "
        inn_ogrn_kpp_line += f"ОГРН {ogrn}"
    if kpp:
        if inn_ogrn_kpp_line:
            inn_ogrn_kpp_line += " "
        inn_ogrn_kpp_line += f"КПП {kpp}"
    
    draw_char_cells(c, MARGIN_LEFT, y_pos, inn_ogrn_kpp_line, 42)
    
    # Пояснительный текст под одиннадцатой строкой
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "ИНН, место нахождение (для физического лица - адрес фактического места жительства) работодателя")
    
    # Двенадцатая строка клеточек
    y_pos -= 20
    draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
    
    # Пояснительный текст под двенадцатой строкой
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "или заказчика работ (услуг): индекс, субъект Российской Федерации, район, город / населенный пункт,")
    
    # Тринадцатая строка клеточек
    y_pos -= 20
    draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
    
    # Пояснительный текст под тринадцатой строкой
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, 
                      "улица, дом, квартира/офис)")
    
    # Контактный телефон заказчика
    y_pos -= 40
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos + 5, "Контактный телефон:")
    draw_char_cells(c, MARGIN_LEFT + 150, y_pos, "", 25)
    
    # Подпись и дата в конце пункта 11
    y_pos -= 60
    c.line(MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_RIGHT, y_pos)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 10, 
                      "(подпись и фамилия, имя, отчество (при наличии) иностранного гражданина (лица без гражданства)")
    
    # Дата подписания
    y_pos -= 40
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT + 20, y_pos, "«")
    c.drawString(MARGIN_LEFT + 40, y_pos, "»")
    c.drawString(MARGIN_LEFT + 140, y_pos, "20")
    c.drawString(MARGIN_LEFT + 170, y_pos, "г.")

def create_page_5(c, data):
    """Создает пятую страницу: Справка (Приложение № 3) с ФИО из патента"""
    # Регистрируем шрифты
    font_name = register_fonts()
    
    # Устанавливаем базовый шрифт
    c.setFont("CyrillicFont", FONT_SIZE)
    
    # Заголовок справки - правый верхний угол
    y_pos = PAGE_HEIGHT - 60
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "Приложение № 3")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "к Порядку подачи иностранным")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "гражданином или лицом без")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "гражданства, получившим патент,")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "уведомления об осуществлении")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "трудовой деятельности в")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "территориальный орган")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "МВД России, выдавший патент,")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "установленному приказом")
    y_pos -= 15
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "МВД России от 05.09.2023 № 655")
    
    # Справка - заголовок по центру
    y_pos = PAGE_HEIGHT - 280
    c.setFont("CyrillicFont", 12)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, "Справка")
    
    # Номер справки
    y_pos -= 50
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos, "№ ")
    # Линия для номера справки
    c.line(MARGIN_LEFT + 20, y_pos - 2, MARGIN_LEFT + 350, y_pos - 2)
    
    # Пояснительный текст под номером
    y_pos -= 20
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + 185, y_pos, "(регистрационный номер уведомления)")
    
    # ИСПРАВЛЕНИЕ 4: ФИО из патента на справке
    # Получаем ФИО из патента (приоритет) или из паспорта
    patent_fio = ""
    if data.get("lastname") and data.get("firstname"):
        # Формируем ФИО из отдельных полей (из патента)
        patent_fio = f"{data.get('lastname', '')} {data.get('firstname', '')} {data.get('middlename', '')}".strip()
    elif data.get("fio"):
        # Используем полное ФИО если отдельные поля недоступны
        patent_fio = str(data.get("fio", "")).upper()
    
    # Текст справки - "дана" с ФИО
    y_pos -= 50
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos, "дана ")
    
    # Выводим ФИО на строке после "дана"
    if patent_fio:
        c.drawString(MARGIN_LEFT + 40, y_pos, patent_fio.upper())
    
    # Длинная линия для ФИО (остается для дополнения если нужно)
    c.line(MARGIN_LEFT + 40 + len(patent_fio) * 6 if patent_fio else MARGIN_LEFT + 40, 
           y_pos - 2, PAGE_WIDTH - MARGIN_RIGHT, y_pos - 2)
    
    # Пояснительный текст под первой линией ФИО
    y_pos -= 20
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, "(фамилия, имя, отчество (при наличии) иностранного")
    
    # Вторая линия для продолжения ФИО (если нужно)
    y_pos -= 25
    c.line(MARGIN_LEFT, y_pos - 2, PAGE_WIDTH - MARGIN_RIGHT, y_pos - 2)
    
    # Пояснительный текст под второй линией
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, "гражданина (лица без гражданства)")
    
    # Пустая строка для должности, фамилии и инициалов
    y_pos -= 50
    c.line(MARGIN_LEFT, y_pos - 2, PAGE_WIDTH - MARGIN_RIGHT, y_pos - 2)
    
    # Пояснительный текст под линией должности
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, "должность, фамилия и инициалы должностного лица")
    y_pos -= 15
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, "территориального органа")
    
    # Линия для МВД России с подписью справа
    y_pos -= 40
    c.line(MARGIN_LEFT, y_pos - 2, PAGE_WIDTH - MARGIN_RIGHT - 100, y_pos - 2)
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, "(подпись)")
    
    # Пояснительный текст под линией МВД
    y_pos -= 20
    c.drawCentredString(PAGE_WIDTH / 2 - 50, y_pos, "МВД России на региональном или районном уровнях,")
    y_pos -= 15
    c.drawCentredString(PAGE_WIDTH / 2 - 50, y_pos, "принявшего уведомление)")


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
        # Создаем директорию для уведомлений, если она не существует
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Формируем имя файла на основе данных компании и текущей даты/времени
        company_name = user_data.get("company_name", "Компания")
        # ИСПРАВЛЕНИЕ: Очищаем название компании от недопустимых символов
        safe_company_name = sanitize_filename(company_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"notification_{safe_company_name}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        # Создаем PDF
        return create_notification_pdf_by_template(user_data, output_path)
    
    except Exception as e:
        logging.error(f"Ошибка при создании уведомления из данных БД: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_notification_pdf_by_template(data, output_path):
    """
    Создает PDF уведомление по официальному шаблону МВД с точным позиционированием.
    
    Args:
        data (dict): Данные для заполнения формы
        output_path (str): Путь для сохранения PDF файла
        
    Returns:
        str: Путь к созданному файлу или None в случае ошибки
    """
    try:
        # Подготавливаем данные с автозаполнением
        prepared_data = prepare_data_for_pdf(data)
        
        # Создаем объект PDF
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # Создаем страницы по эталону
        create_page_1(c, prepared_data)
        c.showPage()
        
        create_page_2(c, prepared_data)
        c.showPage()
        
        create_page_3(c, prepared_data)
        c.showPage()
        
        create_page_4(c, prepared_data)
        c.showPage()
        
        create_page_5(c, prepared_data)
        
        # Сохраняем PDF
        c.save()
        logging.info(f"Создан PDF по официальному шаблону МВД: {output_path}")
        return output_path
    
    except Exception as e:
        logging.error(f"Ошибка при создании PDF: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return None

# Тестирование функции генерации PDF
if __name__ == "__main__":
    # Тестовые данные с новыми полями
    test_data = {
        "lastname": "ИВАНОВ",
        "firstname": "ИВАН",
        "middlename": "ИВАНОВИЧ",
        "citizenship": "РОССИЙСКАЯ ФЕДЕРАЦИЯ",
        "birthdate": "01.01.1980",
        "document_type": "ПАСПОРТ",
        "passport_number": "FK0207865",  # Серия и номер вместе для тестирования разделения
        "issue_date": "01.01.2000",
        "passport_issued_by": "ОТДЕЛОМ ВНУТРЕННИХ ДЕЛ РАЙОНА ИВАНОВСКИЙ Г. МОСКВЫ",
        "patent_number": "ПИР2500015683",  # Серия и номер патента вместе
        "patent_date": "01.01.2023",
        "position": "СПЕЦИАЛИСТ ПО ИНФОРМАЦИОННЫМ ТЕХНОЛОГИЯМ",
        "city": "ДМИТРОВ",  # Для автозаполнения региональных данных
        "contract_type": "ГРАЖДАНСКО-ПРАВОВОЙ (УСТНЫЙ)",
        "contract_date": "20.01.2023",
        "inn": "123456789012",
        
        # НОВЫЕ ПОЛЯ ДМС
        "dms_series": "26",  # Серия ДМС из новой колонки
        "dms_number": "0004315689",  # Номер ДМС из новой колонки
        "insurance_date": "15.01.2023",  # Дата выдачи ДМС
        
        # КОНТАКТНЫЕ ДАННЫЕ
        "contact_phone": "8 (800) 333-70-69",  # Поддержка любых форматов
        "contact_email": "info@renins.ru",
        "customer_info": "ООО 'ТЕСТОВАЯ КОМПАНИЯ'"
    }
    
    output_dir = "generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "official_notification.pdf")
    
    create_notification_pdf_by_template(test_data, output_path)
    print(f"Официальное уведомление создано: {output_path}")
