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
CELL_WIDTH = 13.5
CELL_HEIGHT = 13.5

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
def draw_char_cells(c, x, y, text, num_cells, cell_width=CELL_WIDTH, cell_height=CELL_HEIGHT, font_size=FONT_SIZE):
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
    
    # Клетки для ввода территориального органа МВД (3 строки)
    y_pos = PAGE_HEIGHT - 250
    for i in range(3):
        draw_char_cells(c, MARGIN_LEFT, y_pos - i * (CELL_HEIGHT + 5), "", 42)
    
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
    draw_char_cells(c, MARGIN_LEFT + 50, y_pos, data.get("patent_blank_series", ""), 7)
    
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
    
    # Адрес работы (2 строки)
    y_pos -= CELL_HEIGHT + 10
    work_address = data.get("work_address", "")
    draw_char_cells(c, MARGIN_LEFT, y_pos, work_address, 42)
    draw_char_cells(c, MARGIN_LEFT, y_pos - CELL_HEIGHT - 5, "", 42)
    
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
    
    # 6. Дата заключения устного договора (если устный)
    if is_verbal:
        y_pos -= CELL_HEIGHT + 20
        c.setFont("CyrillicFont", FONT_SIZE)
        c.drawString(MARGIN_LEFT, y_pos + 5, "6. Дата заключения гражданско-правового договора на выполнение работ (оказание услуг)")
        c.drawString(MARGIN_LEFT, y_pos - 15, "(указывается в случае заключения в устной форме)")
        
        contract_date = format_date(data.get("contract_date", ""))
        day = contract_date.split(".")[0] if len(contract_date.split(".")) > 0 else ""
        month = contract_date.split(".")[1] if len(contract_date.split(".")) > 1 else ""
        year = contract_date.split(".")[2] if len(contract_date.split(".")) > 2 else ""
        
        # День
        draw_char_cells(c, MARGIN_LEFT, y_pos - 35, day, 2)
        c.setFont("CyrillicFont", TINY_FONT_SIZE)
        c.drawCentredString(MARGIN_LEFT + CELL_WIDTH, y_pos - 50, "(число)")
        
        # Месяц
        draw_char_cells(c, MARGIN_LEFT + 3*CELL_WIDTH, y_pos - 35, month, 2)
        c.drawCentredString(MARGIN_LEFT + 4*CELL_WIDTH, y_pos - 50, "(месяц)")
        
        # Год
        draw_char_cells(c, MARGIN_LEFT + 6*CELL_WIDTH, y_pos - 35, year, 4)
        c.drawCentredString(MARGIN_LEFT + 8*CELL_WIDTH, y_pos - 50, "(год)")
        
        y_pos -= CELL_HEIGHT + 50
    else:
        y_pos -= CELL_HEIGHT + 20
    
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
    
    # Поля для информации о полисе (3 строки)
    y_pos -= CELL_HEIGHT + 40
    insurance_name = data.get("insurance_company", "")
    draw_char_cells(c, MARGIN_LEFT, y_pos, insurance_name, 42)
    draw_char_cells(c, MARGIN_LEFT, y_pos - CELL_HEIGHT - 5, "", 42)
    draw_char_cells(c, MARGIN_LEFT, y_pos - 2*(CELL_HEIGHT + 5), "", 42)
    
    # Пояснение к полису
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 3*(CELL_HEIGHT + 5) - 5, "(наименование и реквизиты документа)")

# Создаем страницу 3
def create_page_3(c, data):
    """Создает третью страницу: Продолжение полиса + контакты + заказчик"""
    # Регистрируем шрифты
    font_name = register_fonts()
    
    # Устанавливаем базовый шрифт
    c.setFont("CyrillicFont", FONT_SIZE)
    
    # Продолжение 8. Сведения о полисе
    y_pos = PAGE_HEIGHT - 70
    c.drawString(MARGIN_LEFT, y_pos + 5, "8. Сведения о действующем договоре (полисе) добровольного медицинского страхования,")
    c.drawString(MARGIN_LEFT, y_pos - 15, "либо договоре о предоставлении платных медицинских услуг, либо действующем полисе")
    c.drawString(MARGIN_LEFT, y_pos - 35, "обязательного медицинского страхования:")
    
    # Серия и номер полиса
    y_pos -= CELL_HEIGHT + 40
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
    
    # 11. Сведения о заказчике работ (услуг)
    contract_type = data.get("contract_type", "ТРУДОВОЙ").upper()
    is_verbal = "УСТ" in contract_type
    
    if is_verbal:
        y_pos -= CELL_HEIGHT + 40
        c.setFont("CyrillicFont", FONT_SIZE)
        c.drawString(MARGIN_LEFT, y_pos + 5, "11. Сведения о заказчике работ (услуг) (указывается в случае заключения гражданско-")
        c.drawString(MARGIN_LEFT, y_pos - 15, "правового договора на выполнение работ (оказание услуг) в устной форме)")
        
        # Поля для информации о заказчике (3 строки с клетками)
        y_pos -= CELL_HEIGHT + 20
        customer_info = data.get("customer_info", "")
        draw_char_cells(c, MARGIN_LEFT, y_pos, customer_info, 42)
        c.setFont("CyrillicFont", TINY_FONT_SIZE)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - CELL_HEIGHT - 5, 
                          "(полное наименование юридического лица/филиала иностранного юридического лица/представительства")
        
        y_pos -= CELL_HEIGHT + 20
        draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - CELL_HEIGHT - 5, 
                          "иностранного юридического лица, фамилия, имя, отчество (при их наличии) индивидуального")
        
        y_pos -= CELL_HEIGHT + 20
        draw_char_cells(c, MARGIN_LEFT, y_pos, "", 42)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - CELL_HEIGHT - 5, 
                          "предпринимателя/адвоката, учредившего адвокатский кабинет/частного нотариуса/физического лица –")
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - CELL_HEIGHT - 20, 
                          "гражданина Российской Федерации)")

# Создаем страницу 4
def create_page_4(c, data):
    """Создает четвертую страницу: Реквизиты заказчика + справка"""
    # Регистрируем шрифты
    font_name = register_fonts()
    
    # Устанавливаем базовый шрифт
    c.setFont("CyrillicFont", FONT_SIZE)
    
    # Продолжение 11. Сведения о заказчике
    contract_type = data.get("contract_type", "ТРУДОВОЙ").upper()
    is_verbal = "УСТ" in contract_type
    
    if is_verbal:
        y_pos = PAGE_HEIGHT - 70
        c.drawString(MARGIN_LEFT, y_pos + 5, "11. Сведения о заказчике работ (услуг) (указывается в случае заключения гражданско-")
        c.drawString(MARGIN_LEFT, y_pos - 15, "правового договора на выполнение работ (оказание услуг) в устной форме)")
        
        # Реквизиты заказчика (без клеток)
        y_pos -= 50
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.setFont("CyrillicFont", TINY_FONT_SIZE)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "(для юридических лиц – государственный регистрационный номер записи в Едином государственном")
        
        y_pos -= 30
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "реестре юридических лиц, для филиалов или представительств иностранных юридических лиц –")
        
        y_pos -= 30
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "номер документа, подтверждающего факт аккредитации филиала или представительства иностранного")
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 30, 
                          "юридического лица, для индивидуальных предпринимателей – государственный регистрационный")
        
        y_pos -= 45
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "номер записи в Едином государственном реестре индивидуальных предпринимателей,")
        
        y_pos -= 30
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "для частных нотариусов – номер лицензии на право нотариальной деятельности, для физического лица –")
        
        y_pos -= 30
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "наименование документа, удостоверяющего личность, его серия и номер, кем и когда выдан)")
        
        y_pos -= 30
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "ИНН, место нахождение (для физического лица - адрес фактического места жительства) работодателя")
        
        y_pos -= 30
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "или заказчика работ (услуг): индекс, субъект Российской Федерации, район, город / населенный пункт,")
        
        y_pos -= 30
        draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
        c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, 
                          "улица, дом, квартира/офис)")
        
        # Контактный телефон заказчика
        y_pos -= 40
        c.setFont("CyrillicFont", FONT_SIZE)
        c.drawString(MARGIN_LEFT, y_pos + 5, "Контактный телефон:")
        draw_lines(c, MARGIN_LEFT + 150, y_pos, 200, 1)
        
        y_pos -= 50
    
    # СПРАВКА (Приложение № 3)
    c.setFont("CyrillicFont", FONT_SIZE)
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
    
    y_pos -= 30
    c.setFont("CyrillicFont", 10)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos, "Справка")
    
    # Поля справки
    y_pos -= 50
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos, "№")
    draw_lines(c, MARGIN_LEFT + 20, y_pos, 300, 1)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(MARGIN_LEFT + 170, y_pos - 15, "(регистрационный номер уведомления)")
    
    y_pos -= 40
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT, y_pos, "дана")
    draw_lines(c, MARGIN_LEFT + 50, y_pos, 400, 1)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, "(фамилия, имя, отчество (при наличии) иностранного")
    
    y_pos -= 30
    draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, "гражданина (лица без гражданства)")
    
    y_pos -= 40
    draw_lines(c, MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 1)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, "должность, фамилия и инициалы должностного лица")
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 30, "территориального органа")
    
    y_pos -= 50
    draw_lines(c, MARGIN_LEFT, y_pos, 300, 1)
    draw_lines(c, PAGE_WIDTH - 120, y_pos, 70, 1)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 15, "МВД России на региональном или районном уровнях,")
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos - 15, "(подпись)")
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 30, "принявшего уведомление)")
    
    # Место для подписи
    y_pos -= 80
    c.line(MARGIN_LEFT, y_pos, PAGE_WIDTH - MARGIN_RIGHT, y_pos)
    c.setFont("CyrillicFont", TINY_FONT_SIZE)
    c.drawCentredString(PAGE_WIDTH / 2, y_pos - 10, 
                      "(подпись и фамилия, имя, отчество (при наличии) иностранного гражданина (лица без гражданства))")
    
    # Дата подписания
    y_pos -= 40
    c.setFont("CyrillicFont", FONT_SIZE)
    c.drawString(MARGIN_LEFT + 20, y_pos, "«")
    c.drawString(MARGIN_LEFT + 40, y_pos, "»")
    c.drawString(MARGIN_LEFT + 140, y_pos, "20")
    c.drawString(MARGIN_LEFT + 170, y_pos, "г.")

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
        # Создаем объект PDF
        c = canvas.Canvas(output_path, pagesize=A4)
        
        # Создаем страницы по эталону
        create_page_1(c, data)
        c.showPage()
        
        create_page_2(c, data)
        c.showPage()
        
        create_page_3(c, data)
        c.showPage()
        
        create_page_4(c, data)
        
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
    # Тестовые данные
    test_data = {
        "lastname": "ИВАНОВ",
        "firstname": "ИВАН",
        "middlename": "ИВАНОВИЧ",
        "citizenship": "РОССИЙСКАЯ ФЕДЕРАЦИЯ",
        "birthdate": "01.01.1980",
        "document_type": "ПАСПОРТ",
        "passport_series": "1234",
        "passport_number": "567890",
        "issue_date": "01.01.2000",
        "passport_issued_by": "ОТДЕЛОМ ВНУТРЕННИХ ДЕЛ РАЙОНА ИВАНОВСКИЙ Г. МОСКВЫ",
        "patent_blank_series": "АВ",
        "patent_number": "1234567890",
        "patent_date": "01.01.2023",
        "position": "СПЕЦИАЛИСТ ПО ИНФОРМАЦИОННЫМ ТЕХНОЛОГИЯМ",
        "work_address": "Г. МОСКВА, УЛ. ТВЕРСКАЯ, Д. 1",
        "contract_type": "ГРАЖДАНСКО-ПРАВОВОЙ (УСТНЫЙ)",
        "contract_date": "20.01.2023",
        "inn": "123456789012",
        "insurance_company": "СТРАХОВАЯ КОМПАНИЯ 'РЕСО-ГАРАНТИЯ'",
        "insurance_series": "ДМС",
        "insurance_number": "1234567890",
        "insurance_date": "15.01.2023",
        "contact_phone": "+79991234567",
        "contact_email": "ivanov@example.com",
        "customer_info": "ООО 'ТЕСТОВАЯ КОМПАНИЯ'"
    }
    
    output_dir = "generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "official_notification.pdf")
    
    create_notification_pdf_by_template(test_data, output_path)
    print(f"Официальное уведомление создано: {output_path}")
