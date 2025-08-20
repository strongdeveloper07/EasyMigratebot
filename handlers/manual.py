import logging
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import ADD_EMPLOYEE_OPTION
from states import MANUAL_INPUT, ADD_ANOTHER_EMPLOYEE
from utils.fields import get_field_description
from utils.supabase import save_to_supabase
from utils.template_notification_pdf import create_notification_from_db_data

logger = logging.getLogger(__name__)

async def save_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Собирает все данные, сохраняет в Supabase и генерирует итоговый документ.
    """
    user_data = context.user_data
    service_type = user_data.get('service', '')
    
    # --- Сбор всех данных в один словарь ---
    full_data = {
        "company_name": user_data.get("company_name", ""),
        "company_inn": user_data.get("company_inn", ""),
        "service": service_type,
        "stage": user_data.get("stage", ""),
        "city": user_data.get("city", ""),
        # ИСПРАВЛЕНИЕ: Добавляем данные компании из диалога бота
        "company_address": user_data.get("company_address", ""),
        "ogrn": user_data.get("ogrn", ""),
        "kpp": user_data.get("kpp", ""),
        "inn": user_data.get("company_inn", ""),  # ИНН для пункта 11
    }
    # Собираем данные из всех словарей по документам
    for doc_type in ['passport', 'migration', 'patent', 'dms', 'contract']:
        doc_fields = user_data.get(f'{doc_type}_fields', {})
        for field, value in doc_fields.items():
            if value and str(value).strip():  # Сохраняем только непустые значения
                full_data[field] = value
    
    # Специальный маппинг для паспортных полей в соответствии с колонками таблицы
    passport_fields = user_data.get('passport_fields', {})
    if passport_fields:
        field_mapping = {
            'authority': 'passport_issued_by',  # Кем выдан паспорт
            'birthdate': 'birthdate',          # Дата рождения
            'issue_date': 'issue_date',        # Дата выдачи паспорта
            'birth_place': 'birth_place',      # Место рождения
            'passport_series': 'passport_series', # Серия паспорта
            'passport_number': 'passport_number', # Номер паспорта
            'nationality': 'citizenship',       # Гражданство
            'expiry_date': 'passport_until'     # Срок действия паспорта
        }
        for original_field, table_field in field_mapping.items():
            if original_field in passport_fields and passport_fields[original_field]:
                full_data[table_field] = passport_fields[original_field]
    
    # ФИО только из patent_fields
    patent_fields = user_data.get('patent_fields', {})
    if 'fio' in patent_fields and patent_fields['fio']:
        fio_raw = patent_fields['fio'].upper()
        full_data['fio'] = fio_raw
        fio_parts = fio_raw.split()
        if fio_parts:
            full_data['lastname'] = fio_parts[0] if len(fio_parts) > 0 else ''
            full_data['firstname'] = fio_parts[1] if len(fio_parts) > 1 else ''
            full_data['middlename'] = ' '.join(fio_parts[2:]) if len(fio_parts) > 2 else ''
    
    # Извлекаем дополнительные поля из DMS
    dms_fields = user_data.get('dms_fields', {})
    if dms_fields:
        # Маппинг полей DMS в соответствующие колонки таблицы
        dms_mapping = {
            'insurance_company': 'insurance_company', 
            'insurance_date': 'insurance_date',
            'insurance_expiry': 'insurance_expiry',
            'dms_number': 'dms_number'  # ИСПРАВЛЕНИЕ 7: Добавляем поле для номера ДМС
        }
        for dms_field, table_field in dms_mapping.items():
            if dms_field in dms_fields and dms_fields[dms_field]:
                full_data[table_field] = dms_fields[dms_field]
    
    # Извлекаем дополнительные поля из контракта
    contract_fields = user_data.get('contract_fields', {})
    if contract_fields:
        contract_mapping = {
            'work_address': 'work_address',
            'position': 'position',
            'contract_date': 'contract_date',
            'phone': 'contact_phone',
            'contact_phone': 'contact_phone'
        }
        for contract_field, table_field in contract_mapping.items():
            if contract_field in contract_fields and contract_fields[contract_field]:
                full_data[table_field] = contract_fields[contract_field]
    
    # Обновляем данными из ручного ввода, если они есть
    manual_data = user_data.get('manual_fields', {})
    for (doc_type, field), value in manual_data.items():
        if value and value.strip():  # Сохраняем только непустые значения
            full_data[field] = value

    # --- Подготовка данных к сохранению ---
    # Приводим ФИО к верхнему регистру
    if 'fio' in full_data:
        full_data['fio'] = str(full_data.get('fio', '')).upper()
    
    # Обработка бланка патента
    blank = full_data.get('patent_blank', '')
    if blank:
        letters = ''.join([c for c in blank if c.isalpha()])
        digits = ''.join([c for c in blank if c.isdigit()])
        full_data['patent_blank_series'] = letters.upper()
        full_data['patent_blank_number'] = digits

    # Списки допустимых столбцов для таблиц Supabase
    passport_fields_allowed = [
        "company_name", "company_inn", "service", "stage", "fio", "birthdate", "birth_place", "sex",
        "passport_series", "passport_number", "doc_number", "issue_date", "passport_until", "issuer", "issuer_country",
        "migration_card_series", "migration_card_number", "migration_card_date", "migration_card_purpose",
        "patent_series", "patent_number", "patent_date", "patent_until", "patent_issuer", 
        "patent_blank_series", "patent_blank_number", "status"
    ]
    notification_fields_allowed = [
        # Основная информация
        "company_name", "company_inn", "service", "city", 
        
        # ИСПРАВЛЕНИЕ: Добавляем поля компании для пункта 11
        "company_address", "ogrn", "kpp", "inn",
        
        # Персональные данные
        "lastname", "firstname", "middlename", "fio", "citizenship", "birthdate", "birth_place",
        
        # Паспортные данные
        "passport_series", "passport_number", "issue_date", "passport_issued_by",
        
        # Данные патента
        "patent_series", "patent_number", "patent_date",
        
        # Трудовые данные
        "position", "work_address", "contract_date", "inn",
        
        # Медицинские данные - ИСПРАВЛЕНИЕ 7: Добавляем dms_number
        "insurance_company", "insurance_date", "insurance_expiry", "dms_number",
        
        # Контактные данные
        "contact_phone", "contact_email"
    ]

    if service_type == "Уведомление от работника иностранного гражданина":
        table_name = "notifications"
        allowed_cols = notification_fields_allowed
    else:
        table_name = "passport_applications"
        allowed_cols = passport_fields_allowed

    data_to_save = {k: v for k, v in full_data.items() if k in allowed_cols}

    # --- Сохранение в Supabase ---
    saved = save_to_supabase(data_to_save, table_name)
    if not saved:
        await update.message.reply_text("⚠️ Ошибка при сохранении данных в базу. Пожалуйста, попробуйте позже.")
        return ConversationHandler.END

    await update.message.reply_text("✅ Данные успешно сохранены в базу!")

    # --- Генерация документа ---
    if service_type == "Уведомление от работника иностранного гражданина":
        await update.message.reply_text("⏳ Генерирую официальный PDF-документ по форме МВД России от 05.09.2023 г. № 655...")
        try:
            # Создаем уведомление по официальному шаблону МВД
            template_pdf_path = create_notification_from_db_data(full_data)
            if template_pdf_path:
                with open(template_pdf_path, 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=InputFile(pdf_file, filename="Уведомление_МВД.pdf"),
                        caption="✅ Уведомление успешно сформировано в формате PDF по официальной форме!\n"
                               "📋 Форма соответствует Приложению №1 к приказу МВД России от 05.09.2023 г. № 655"
                    )
                # Удаляем временный файл
                import os
                os.remove(template_pdf_path)
            else:
                await update.message.reply_text("❌ Не удалось создать PDF-файл по форме МВД.")
        except Exception as e:
            logger.error(f"Ошибка генерации PDF: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Не удалось создать PDF-файл: {e}")

    # --- Завершение ---
    await update.message.reply_text(
        "Что делаем дальше?",
        reply_markup=ReplyKeyboardMarkup(ADD_EMPLOYEE_OPTION, resize_keyboard=True)
    )
    return ADD_ANOTHER_EMPLOYEE


async def manual_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает поочередный ручной ввод недостающих данных.
    """
    user_data = context.user_data
    current_field_type, current_field_name = user_data['missing_fields'][0]
    
    # Сохраняем введенное значение
    user_data.setdefault('manual_fields', {})[(current_field_type, current_field_name)] = update.message.text.strip()
    
    # Удаляем обработанное поле из списка
    user_data['missing_fields'].pop(0)
    
    # Если остались еще поля для ввода
    if user_data['missing_fields']:
        next_field_type, next_field_name = user_data['missing_fields'][0]
        field_desc = get_field_description(next_field_type, next_field_name)
        await update.message.reply_text(f"✅ Принято. Теперь введите: {field_desc}")
        return MANUAL_INPUT
    else:
        # Если все поля введены, переходим к сохранению
        await update.message.reply_text("✅ Все данные собраны, сохраняю...")
        return await save_application(update, context)
