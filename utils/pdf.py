import os
import logging
from io import BytesIO
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

try:
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
except:
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    except:
        pass

def generate_notification_pdf(data: dict, city: str):
    """
    Генерирует PDF-уведомление на основе данных и города.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Устанавливаем шрифт
    try:
        p.setFont('Arial', 10)
    except:
        p.setFont('Helvetica', 10)

    # --- Статические данные для каждого города ---
    city_data = {
        "Волжский": {
            "recipient": "Управление по вопросам миграции ГУ МВД России по Волгоградской области",
            "work_address": "Волгоградская область, г. Волжский, пр-кт Металлургов, д.6",
            "customer_info": f"{data.get('company_name', '')}, ИНН {data.get('company_inn', '')}"
        },
        "Долгопрудный": {
            "recipient": "Отдел по вопросам миграции МУ МВД России \"Мытищинское\"",
            "work_address": "Московская обл., г. Долгопрудный, Лихачевское шоссе, д.27",
            "customer_info": f"{data.get('company_name', '')}, ИНН {data.get('company_inn', '')}"
        },
        "Дмитров": {
            "recipient": "Отдел по вопросам миграции УМВД России по Дмитровскому городскому округу",
            "work_address": "Московская обл., Дмитровский р-н, д. Ивашево",
            "customer_info": f"{data.get('company_name', '')}, ИНН {data.get('company_inn', '')}"
        }
    }
    
    selected_city_data = city_data.get(city, {})

    # --- Заполнение полей PDF (координаты примерные, нужно будет настроить) ---
    
    # Шапка (предполагается, что она есть в шаблоне, здесь мы её не рисуем)
    
    # 1. Получатель
    p.drawString(100, 750, "Настоящее уведомление представляется в:")
    p.drawString(120, 735, selected_city_data.get("recipient", ""))

    # 2. Данные сотрудника
    fio_parts = data.get('fio', '').split()
    p.drawString(100, 700, f"Фамилия: {fio_parts[0] if len(fio_parts) > 0 else ''}")
    p.drawString(100, 685, f"Имя: {fio_parts[1] if len(fio_parts) > 1 else ''}")
    p.drawString(100, 670, f"Отчество: {fio_parts[2] if len(fio_parts) > 2 else ''}")
    p.drawString(100, 655, f"Гражданство: {data.get('issuer_country', '')}")
    p.drawString(100, 640, f"Дата рождения: {data.get('birthdate', '')}")

    # 3. Паспорт
    passport_series = data.get('passport_series', '')
    passport_number = data.get('passport_number', '')
    passport_info = f"ПАСПОРТ {passport_number}" if data.get('issuer_country', '').upper() == 'ТАДЖИКИСТАН' else f"ПАСПОРТ {passport_series} {passport_number}"
    p.drawString(100, 610, f"Документ, удостоверяющий личность: {passport_info}")
    p.drawString(120, 595, f"Дата выдачи: {data.get('issue_date', '')}")
    p.drawString(120, 580, f"Кем выдан: {data.get('issuer', '')}")

    # 4. Патент
    p.drawString(100, 550, f"Сведения о патенте: {data.get('patent_series', '')} {data.get('patent_number', '')}")

    # 5. Работа
    p.drawString(100, 520, f"Профессия: {data.get('position', '')}")
    p.drawString(100, 505, f"Место осуществления трудовой деятельности: {selected_city_data.get('work_address', '')}")
    
    # Галочка для трудового договора (рисуем 'V')
    p.drawString(100, 480, "Трудовая деятельность осуществляется на основании:")
    p.drawString(120, 465, "[V] трудового договора")
    p.drawString(120, 450, "[ ] гражданско-правового договора")

    p.drawString(100, 420, f"Дата заключения договора: {data.get('contract_date', '')}")
    p.drawString(100, 405, f"ИНН: {data.get('inn', '')}")

    # 6. ДМС
    p.drawString(100, 375, f"Сведения о ДМС: {data.get('dms_series', '')} {data.get('dms_policy_number', '')}")
    p.drawString(120, 360, f"Дата выдачи: {data.get('dms_start_date', '')}")
    p.drawString(120, 345, f"Контактный телефон: {data.get('dms_insurer_phone', '')}") # Нужно добавить это поле
    p.drawString(120, 330, f"Email: {data.get('dms_insurer_email', '')}") # Нужно добавить это поле

    # 7. Заказчик
    p.drawString(100, 300, "Сведения о заказчике работ (услуг):")
    p.drawString(120, 285, selected_city_data.get("customer_info", ""))

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def fill_notification_form(data: dict, city: str):
    try:
        templates = {
            "Волжский": {
                "fields": {
                    "1.1. Фамилия": data['fio'].split()[0] if data['fio'] else "",
                    "1.2. Имя": data['fio'].split()[1] if len(data['fio'].split()) > 1 else "",
                    "1.3. Отчество": data['fio'].split()[2] if len(data['fio'].split()) > 2 else "",
                    "1.4. Гражданство": data.get('issuer_country', ''),
                    "1.5. Дата рождения": data.get('birthdate', ''),
                    "1.6. Документ, удостоверяющий личность": f"ПАСПОРТ {data.get('passport_series', '')} {data.get('passport_number', '')}",
                    "Кем выдан": data.get('issuer', ''),
                    "Дата выдачи": data.get('issue_date', ''),
                    "2. Сведения о патенте": f"{data.get('patent_series', '')} {data.get('patent_number', '')}",
                    "Дата выдачи патента": data.get('patent_date', ''),
                    "Кем выдан патент": data.get('patent_issuer', ''),
                    "7. ИНН": data.get('inn', ''),
                    "8. Сведения о ДМС": f"{data.get('dms_series', '')} {data.get('dms_policy_number', '')}",
                    "Дата выдачи ДМС": data.get('dms_start_date', ''),
                    "9. Контактный телефон": "",
                    "11. Сведения о заказчике": f"{data.get('company_name', '')} ИНН {data.get('company_inn', '')}",
                    "Подпись": data.get('fio', '')
                },
                "positions": {
                    "1.1. Фамилия": (100, 650),
                    "1.2. Имя": (100, 620),
                    "1.3. Отчество": (100, 590),
                    "1.4. Гражданство": (100, 560),
                    "1.5. Дата рождения": (100, 530),
                    "1.6. Документ, удостоверяющий личность": (100, 500),
                    "Кем выдан": (100, 470),
                    "Дата выдачи": (300, 470),
                    "2. Сведения о патенте": (100, 400),
                    "Дата выдачи патента": (100, 370),
                    "Кем выдан патент": (100, 340),
                    "7. ИНН": (100, 280),
                    "8. Сведения о ДМС": (100, 250),
                    "Дата выдачи ДМС": (300, 250),
                    "9. Контактный телефон": (100, 220),
                    "11. Сведения о заказчике": (100, 190),
                    "Подпись": (100, 100)
                }
            },
            # ... шаблоны для других городов ...
        }
        template = templates.get(city, templates["Волжский"])
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            filename = tmp_file.name
        c = canvas.Canvas(filename, pagesize=letter)
        try:
            c.setFont("Arial", 10)
        except:
            c.setFont("Helvetica", 10)
        for field_name in template["fields"]:
            value = template["fields"][field_name]
            x, y = template["positions"][field_name]
            c.drawString(x, y, value)
        c.save()
        with open(filename, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(filename)
        return BytesIO(pdf_bytes)
    except Exception as e:
        logger.error(f"Ошибка при генерации PDF: {e}", exc_info=True)
        return None
