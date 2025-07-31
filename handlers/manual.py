import logging
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import ADD_EMPLOYEE_OPTION
from states import MANUAL_INPUT, ADD_ANOTHER_EMPLOYEE
from utils.fields import get_field_description
from utils.supabase import save_to_supabase
from utils.word_notification import generate_notification_word

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
    }
    # Собираем данные из всех словарей по документам
    for doc_type in ['passport', 'migration', 'patent', 'dms', 'contract']:
        full_data.update(user_data.get(f'{doc_type}_fields', {}))
    
    # Обновляем данными из ручного ввода, если они есть
    manual_data = user_data.get('manual_fields', {})
    for (doc_type, field), value in manual_data.items():
        full_data[field] = value

    # --- Подготовка данных к сохранению ---
    # Приводим ФИО к верхнему регистру
    if 'fio' in full_data:
        full_data['fio'] = str(full_data.get('fio', '')).upper()
    if 'fio_latin' in full_data:
        full_data['fio_latin'] = str(full_data.get('fio_latin', '')).upper()
    
    # Обработка бланка патента
    blank = full_data.get('patent_blank', '')
    if blank:
        letters = ''.join([c for c in blank if c.isalpha()])
        digits = ''.join([c for c in blank if c.isdigit()])
        full_data['patent_blank_series'] = letters.upper()
        full_data['patent_blank_number'] = digits

    # Списки допустимых столбцов для таблиц Supabase
    passport_fields_allowed = [
        "company_name", "company_inn", "service", "stage", "fio", "fio_latin", "birthdate", "birth_place", "sex",
        "passport_series", "passport_number", "doc_number", "issue_date", "passport_until", "issuer", "issuer_country",
        "migration_card_series", "migration_card_number", "migration_card_date", "migration_card_purpose",
        "patent_series", "patent_number", "patent_date", "patent_until", "patent_issuer", 
        "patent_blank_series", "patent_blank_number", "status"
    ]
    notification_fields_allowed = [
        "company_name", "company_inn", "service", "fio", "fio_latin", "birthdate", "birth_place", "sex",
        "passport_series", "passport_number", "doc_number", "issue_date", "passport_until", "issuer", "issuer_country",
        "patent_series", "patent_number", "patent_date", "patent_until", "patent_issuer", 
        "patent_blank_series", "patent_blank_number", "inn", "dms_number", "dms_issue_date", "contract_date", 
        "position", "dms_start_date", "dms_end_date", "dms_series", "dms_policy_number",
        "dms_insurer_phone", "dms_insurer_email"
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
        city_data = {
            "Волжский": "Управление по вопросам миграции ГУ МВД России по Волгоградской области",
            "Долгопрудный": "Отдел по вопросам миграции МУ МВД России \"Мытищинское\"",
            "Дмитров": "Отдел по вопросам миграции УМВД России по Дмитровскому городскому округу"
        }
        city = user_data.get("city", "")
        full_data['recipient'] = city_data.get(city, "")

        await update.message.reply_text("⏳ Генерирую Word-документ...")
        try:
            template_path = r"C:\Users\Святослав\Desktop\tg_bot_final\Уведомление+от+ИГ+Пустой.docx"
            word_bytes = generate_notification_word(full_data, template_path)
            if word_bytes:
                await update.message.reply_document(
                    document=InputFile(word_bytes, filename="Уведомление.docx"),
                    caption="✅ Уведомление успешно сформировано!"
                )
            else:
                await update.message.reply_text("❌ Не удалось создать Word-файл. Проверьте, что шаблон 'Уведомление+от+ИГ+Пустой.docx' находится в папке проекта и не поврежден.")
        except Exception as e:
            logger.error(f"Ошибка генерации Word: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Не удалось создать Word-файл: {e}")

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
