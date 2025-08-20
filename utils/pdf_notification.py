"""
Модуль для генерации PDF уведомлений с точным позиционированием символов
"""
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Размеры страницы A4 в пунктах
PAGE_WIDTH, PAGE_HEIGHT = A4

# Настройки шрифта для точного позиционирования
FONT_NAME = "Courier"  # Моноширинный шрифт
FONT_SIZE = 10
CHAR_WIDTH = 6  # Ширина одного символа в пунктах
LINE_HEIGHT = 12  # Высота строки в пунктах

# Маппинг городов и их данных для шапки
CITY_HEADERS = {
    "Волжский": {
        "region": "Волгоградская область",
        "city": "г. Волжский",
        "department": "ОТДЕЛ ПО ВОПРОСАМ МИГРАЦИИ ОМВД РОССИИ ПО Г. ВОЛЖСКОМУ",
        "address": "404130, Волгоградская область, г. Волжский, ул. Карбышева, 47а"
    },
    "Долгопрудный": {
        "region": "Московская область", 
        "city": "г. Долгопрудный",
        "department": "ОТДЕЛ ПО ВОПРОСАМ МИГРАЦИИ УМВД РОССИИ ПО Г.О. ДОЛГОПРУДНЫЙ",
        "address": "141701, Московская область, г. Долгопрудный, ул. Первомайская, 54"
    },
    "Дмитров": {
        "region": "Московская область",
        "city": "г. Дмитров", 
        "department": "ОТДЕЛ ПО ВОПРОСАМ МИГРАЦИИ УМВД РОССИИ ПО Г.О. ДМИТРОВ",
        "address": "141800, Московская область, г. Дмитров, ул. Профессиональная, 15"
    }
}


def format_field_value(value, max_length):
    """
    Форматирует значение поля для точного позиционирования.
    Каждый символ должен занимать ровно одну позицию.
    """
    if not value:
        value = ""
    
    # Конвертируем в строку и обрезаем до максимальной длины
    str_value = str(value)
    if len(str_value) > max_length:
        str_value = str_value[:max_length]
    
    # Дополняем пробелами до нужной длины для сохранения структуры
    return str_value.ljust(max_length)


def draw_form_field(canvas_obj, x, y, width, height, text, max_chars=None):
    """
    Рисует поле формы с рамкой и текстом внутри.
    Каждый символ помещается в отдельную клетку для точного позиционирования.
    """
    if max_chars:
        # Рисуем отдельные клетки для каждого символа
        cell_width = width / max_chars
        for i in range(max_chars):
            cell_x = x + i * cell_width
            # Рамка клетки
            canvas_obj.rect(cell_x, y, cell_width, height)
            # Символ в клетке
            if i < len(text):
                char_x = cell_x + cell_width / 2 - 3  # Центрируем символ
                char_y = y + height / 2 - 3
                canvas_obj.drawString(char_x, char_y, text[i])
    else:
        # Обычное поле без клеток
        canvas_obj.rect(x, y, width, height)
        canvas_obj.drawString(x + 5, y + height / 2 - 3, text)


def draw_char_by_char(canvas_obj, text, start_x, start_y, char_spacing=CHAR_WIDTH):
    """
    Рисует текст символ за символом с точным позиционированием.
    """
    current_x = start_x
    for char in text:
        canvas_obj.drawString(current_x, start_y, char)
        current_x += char_spacing


def draw_checkbox(canvas_obj, x, y, size=10, checked=False):
    """Рисует чекбокс"""
    canvas_obj.rect(x, y, size, size)
    if checked:
        # Рисуем галочку
        canvas_obj.line(x + 2, y + 5, x + 4, y + 2)
        canvas_obj.line(x + 4, y + 2, x + 8, y + 8)


def create_notification_header(canvas_obj, city_name):
    """
    Создает шапку уведомления для выбранного города.
    """
    if city_name not in CITY_HEADERS:
        logger.error(f"Неизвестный город: {city_name}")
        return PAGE_HEIGHT - 200
    
    city_data = CITY_HEADERS[city_name]
    
    # Координаты для шапки (примерные, нужно будет подстроить под реальный шаблон)
    y_position = PAGE_HEIGHT - 100
    
    # Название департамента
    canvas_obj.setFont(FONT_NAME, 10)
    text_width = canvas_obj.stringWidth(city_data["department"], FONT_NAME, 10)
    canvas_obj.drawString((PAGE_WIDTH - text_width) / 2, y_position, city_data["department"])
    
    # Адрес
    y_position -= LINE_HEIGHT * 2
    text_width = canvas_obj.stringWidth(city_data["address"], FONT_NAME, 10)
    canvas_obj.drawString((PAGE_WIDTH - text_width) / 2, y_position, city_data["address"])
    
    # Заголовок "УВЕДОМЛЕНИЕ"
    y_position -= LINE_HEIGHT * 3
    canvas_obj.setFont(FONT_NAME, 12)
    text_width = canvas_obj.stringWidth("УВЕДОМЛЕНИЕ", FONT_NAME, 12)
    canvas_obj.drawString((PAGE_WIDTH - text_width) / 2, y_position, "УВЕДОМЛЕНИЕ")
    
    return y_position - LINE_HEIGHT * 2  # Возвращаем Y позицию для начала основного контента


def generate_notification_pdf(data, output_path):
    """
    Генерирует PDF уведомление с данными из базы.
    
    Args:
        data (dict): Данные для заполнения формы
        output_path (str): Путь для сохранения PDF файла
        
    Returns:
        str: Путь к созданному файлу или None в случае ошибки
    """
    try:
        # Создаем PDF документ
        c = canvas.Canvas(output_path, pagesize=A4)
        c.setFont(FONT_NAME, FONT_SIZE)
        
        # Получаем город из данных
        city_name = data.get('city', 'Волжский')
        
        # Создаем шапку
        content_start_y = create_notification_header(c, city_name)
        
        # Текущая позиция для контента
        current_y = content_start_y
        
        # === ОСНОВНОЙ ТЕКСТ УВЕДОМЛЕНИЯ ===
        c.setFont(FONT_NAME, 10)
        
        # Уведомляем о...
        current_y -= LINE_HEIGHT
        c.drawString(50, current_y, "Уведомляем Вас о принятии на работу иностранного гражданина:")
        current_y -= LINE_HEIGHT * 2
        
        # === ДАННЫЕ О РАБОТНИКЕ ===
        
        # ФИО
        lastname = format_field_value(data.get('lastname', ''), 35)
        firstname = format_field_value(data.get('firstname', ''), 35) 
        middlename = format_field_value(data.get('middlename', ''), 35)
        
        c.drawString(50, current_y, "1. Фамилия, имя, отчество:")
        current_y -= LINE_HEIGHT
        draw_char_by_char(c, f"   {lastname} {firstname} {middlename}", 50, current_y)
        current_y -= LINE_HEIGHT * 2
        
        # Дата и место рождения
        birth_date = format_field_value(data.get('birth_date', ''), 10)
        birth_place = format_field_value(data.get('birth_place', ''), 60)
        
        c.drawString(50, current_y, "2. Дата рождения:")
        draw_char_by_char(c, f"   {birth_date}", 50, current_y - LINE_HEIGHT)
        
        c.drawString(50, current_y - LINE_HEIGHT * 2, "3. Место рождения:")
        draw_char_by_char(c, f"   {birth_place}", 50, current_y - LINE_HEIGHT * 3)
        current_y -= LINE_HEIGHT * 5
        
        # Пол
        gender = format_field_value(data.get('gender', ''), 10)
        c.drawString(50, current_y, "4. Пол:")
        draw_char_by_char(c, f"   {gender}", 50, current_y - LINE_HEIGHT)
        current_y -= LINE_HEIGHT * 3
        
        # Гражданство
        citizenship = format_field_value(data.get('issuer_country', 'УЗБЕКИСТАН'), 20)
        c.drawString(50, current_y, "5. Гражданство:")
        draw_char_by_char(c, f"   {citizenship}", 50, current_y - LINE_HEIGHT)
        current_y -= LINE_HEIGHT * 3
        
        # === ДОКУМЕНТЫ ===
        
        # Документ, удостоверяющий личность
        passport_series = format_field_value(data.get('passport_series', ''), 10)
        passport_number = format_field_value(data.get('passport_number', ''), 15)
        passport_issue_date = format_field_value(data.get('passport_issue_date', ''), 10)
        passport_issued_by = format_field_value(data.get('passport_issued_by', ''), 80)
        
        c.drawString(50, current_y, "6. Документ, удостоверяющий личность:")
        current_y -= LINE_HEIGHT
        c.drawString(70, current_y, "Серия:")
        draw_char_by_char(c, passport_series, 110, current_y)
        c.drawString(200, current_y, "Номер:")
        draw_char_by_char(c, passport_number, 240, current_y)
        current_y -= LINE_HEIGHT
        c.drawString(70, current_y, "Дата выдачи:")
        draw_char_by_char(c, passport_issue_date, 150, current_y)
        current_y -= LINE_HEIGHT
        c.drawString(70, current_y, "Кем выдан:")
        draw_char_by_char(c, passport_issued_by, 130, current_y)
        current_y -= LINE_HEIGHT * 2
        
        # Миграционная карта
        migration_series = format_field_value(data.get('migration_card_series', ''), 10)
        migration_number = format_field_value(data.get('migration_card_number', ''), 15)
        migration_date = format_field_value(data.get('migration_card_date', ''), 10)
        
        c.drawString(50, current_y, "7. Миграционная карта:")
        current_y -= LINE_HEIGHT
        c.drawString(70, current_y, "Серия:")
        draw_char_by_char(c, migration_series, 110, current_y)
        c.drawString(200, current_y, "Номер:")
        draw_char_by_char(c, migration_number, 240, current_y)
        current_y -= LINE_HEIGHT
        c.drawString(70, current_y, "Дата выдачи:")
        draw_char_by_char(c, migration_date, 150, current_y)
        current_y -= LINE_HEIGHT * 2
        
        # Разрешение на работу / патент
        patent_series = format_field_value(data.get('patent_series', ''), 10)
        patent_number = format_field_value(data.get('patent_number', ''), 15)
        patent_date = format_field_value(data.get('patent_date', ''), 10)
        patent_until = format_field_value(data.get('patent_until', ''), 10)
        
        c.drawString(50, current_y, "8. Разрешение на работу/патент:")
        current_y -= LINE_HEIGHT
        c.drawString(70, current_y, "Серия:")
        draw_char_by_char(c, patent_series, 110, current_y)
        c.drawString(200, current_y, "Номер:")
        draw_char_by_char(c, patent_number, 240, current_y)
        current_y -= LINE_HEIGHT
        c.drawString(70, current_y, "Действует с:")
        draw_char_by_char(c, patent_date, 150, current_y)
        c.drawString(270, current_y, "по:")
        draw_char_by_char(c, patent_until, 290, current_y)
        current_y -= LINE_HEIGHT * 2
        
        # === ИНФОРМАЦИЯ О ТРУДОУСТРОЙСТВЕ ===
        
        # Должность
        position = format_field_value(data.get('position', 'РАБОЧИЙ'), 50)
        c.drawString(50, current_y, "9. Замещаемая должность:")
        draw_char_by_char(c, f"   {position}", 50, current_y - LINE_HEIGHT)
        current_y -= LINE_HEIGHT * 3
        
        # Дата начала работы
        contract_date = format_field_value(data.get('contract_date', ''), 10)
        c.drawString(50, current_y, "10. Дата начала осуществления трудовой деятельности:")
        draw_char_by_char(c, f"    {contract_date}", 50, current_y - LINE_HEIGHT)
        current_y -= LINE_HEIGHT * 3
        
        # === ПОДПИСЬ И ДАТА ===
        current_y -= LINE_HEIGHT * 2
        
        # Дата заполнения
        current_date = datetime.now().strftime("%d.%m.%Y")
        c.drawString(50, current_y, f"Дата: {current_date}")
        
        # Место для подписи
        c.drawString(350, current_y, "Подпись руководителя: _______________")
        current_y -= LINE_HEIGHT * 2
        
        # М.П.
        c.drawString(350, current_y, "М.П.")
        
        # Сохраняем PDF
        c.save()
        
        logger.info(f"PDF уведомление успешно создано: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Ошибка при создании PDF уведомления: {e}", exc_info=True)
        return None


def create_notification_from_db_data(user_data, output_dir="notifications"):
    """
    Создает уведомление на основе данных из базы данных.
    
    Args:
        user_data (dict): Данные пользователя и документов
        output_dir (str): Директория для сохранения файлов
        
    Returns:
        str: Путь к созданному файлу или None в случае ошибки
    """
    try:
        # Создаем директорию если её нет
        os.makedirs(output_dir, exist_ok=True)
        
        # Формируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_name_safe = "".join(c for c in user_data.get('company_name', 'company') if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"notification_{company_name_safe}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        # Собираем данные для формы из разных источников
        form_data = {}
        
        # Основные данные
        form_data.update({
            'company_name': user_data.get('company_name', ''),
            'company_inn': user_data.get('company_inn', ''),
            'city': user_data.get('city', ''),
            'service': user_data.get('service', ''),
        })
        
        # Данные паспорта
        passport_fields = user_data.get('passport_fields', {})
        form_data.update({
            'lastname': passport_fields.get('lastname', ''),
            'firstname': passport_fields.get('firstname', ''),
            'middlename': passport_fields.get('middlename', ''),
            'birth_date': passport_fields.get('birth_date', ''),
            'birth_place': passport_fields.get('birth_place', ''),
            'gender': passport_fields.get('gender', ''),
            'passport_series': passport_fields.get('passport_series', ''),
            'passport_number': passport_fields.get('passport_number', ''),
            'passport_issued_by': passport_fields.get('passport_issued_by', ''),
            'passport_issue_date': passport_fields.get('passport_issue_date', ''),
        })
        
        # Данные из других документов (миграционная карта, патент и т.д.)
        migration_fields = user_data.get('migration_fields', {})
        patent_fields = user_data.get('patent_fields', {})
        manual_fields = user_data.get('manual_fields', {})
        
        # Объединяем все поля
        form_data.update(migration_fields)
        form_data.update(patent_fields)
        form_data.update(manual_fields)
        
        # Генерируем PDF
        return generate_notification_pdf(form_data, output_path)
        
    except Exception as e:
        logger.error(f"Ошибка при создании уведомления из данных БД: {e}", exc_info=True)
        return None
