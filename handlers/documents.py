import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputFile
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import DONE_UPLOADING
from states import UPLOAD_DOCUMENTS, MANUAL_INPUT
from utils.fields import get_field_description
from utils.gpt import extract_doc_fields_with_gpt
from utils.ocr import convert_pdf_to_png, gcv_ocr, gcv_ocr_multiple
from utils.parsers import (
    parse_passport_fields, parse_migration_fields, parse_patent_fields,
    parse_dms_fields, parse_contract_fields
)
from utils.prompts import (
    PROMPT_PASSPORT, PROMPT_MIGRATION, PROMPT_PATENT,
    PROMPT_DMS, PROMPT_CONTRACT
)
from utils.word import create_passport_translation_doc

# Логирование
logger = logging.getLogger(__name__)

async def upload_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает загрузку документов от пользователя.
    - Для услуги "Перевод паспорта" сразу выполняет перевод и завершает диалог.
    - Для остальных услуг собирает документы до нажатия кнопки "Завершить загрузку".
    """
    message = update.message
    user_data = context.user_data
    service_type = user_data.get('service')

    # --- Сценарий 1: Перевод паспорта ---
    if service_type == 'Перевод паспорта':
        if not (message.document or message.photo):
            await message.reply_text("Пожалуйста, прикрепите фото или PDF паспорта для перевода.")
            return UPLOAD_DOCUMENTS

        file_obj = await (message.document or message.photo[-1]).get_file()
        file_name = message.document.file_name if message.document else "photo.jpg"
        
        await message.reply_text(f"📥 Загружаю и обрабатываю: {file_name}...")
        try:
            file_bytes = await file_obj.download_as_bytearray()
            raw_text = gcv_ocr(bytes(file_bytes))
            if not raw_text:
                await message.reply_text("❌ Не удалось распознать текст. Попробуйте другой файл.")
                return UPLOAD_DOCUMENTS

            gpt_response = await extract_doc_fields_with_gpt(raw_text, PROMPT_PASSPORT)
            if "Ошибка" in gpt_response:
                await message.reply_text(f"❌ Ошибка GPT: {gpt_response}")
                return UPLOAD_DOCUMENTS

            fields = parse_passport_fields(gpt_response)
            word_bytes = create_passport_translation_doc(fields)
            
            await message.reply_document(
                document=InputFile(word_bytes, filename="Перевод_паспорта.docx"),
                caption="✅ Перевод паспорта готов!"
            )
            await message.reply_text("🏁 Работа завершена. Для нового оформления введите /start", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Ошибка при переводе паспорта: {e}", exc_info=True)
            await message.reply_text(f"❌ Произошла ошибка при обработке: {e}")
            return ConversationHandler.END

    # --- Сценарий 2: Остальные услуги ---
    # Нажатие кнопки "Завершить загрузку"
    if message.text and "завершить" in message.text.lower():
        required_docs = 4 if service_type == "Уведомление от работника иностранного гражданина" else 3
        current_docs = len(user_data.get('documents', []))
        if current_docs < required_docs:
            await message.reply_text(
                f"❌ Загружено {current_docs} из {required_docs} необходимых документов. Пожалуйста, загрузите остальные.",
                reply_markup=ReplyKeyboardMarkup(DONE_UPLOADING, resize_keyboard=True)
            )
            return UPLOAD_DOCUMENTS
        await message.reply_text("⏳ Начинаю обработку документов...", reply_markup=ReplyKeyboardRemove())
        return await process_documents(update, context)

    # Загрузка файла
    if message.document or message.photo:
        file_obj = await (message.document or message.photo[-1]).get_file()
        file_name = message.document.file_name if message.document else "photo.jpg"
        mime_type = message.document.mime_type if message.document else "image/jpeg"
        
        await message.reply_text(f"📥 Загружаю: {file_name}...")
        try:
            file_bytes = await file_obj.download_as_bytearray()
            user_data.setdefault('documents', []).append({
                'bytes': bytes(file_bytes), 'name': file_name, 'mime': mime_type
            })
            count = len(user_data['documents'])
            await message.reply_text(
                f"✅ Документ загружен! Всего: {count}\n"
                "Продолжайте или нажмите '🏁 Завершить загрузку'.",
                reply_markup=ReplyKeyboardMarkup(DONE_UPLOADING, resize_keyboard=True)
            )
        except Exception as e:
            logger.error(f"Ошибка загрузки файла: {e}", exc_info=True)
            await message.reply_text(f"❌ Ошибка при загрузке: {e}")
    else:
        await message.reply_text("Пожалуйста, загрузите документ или нажмите 'Завершить загрузку'.")

    return UPLOAD_DOCUMENTS


async def process_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает все загруженные документы, извлекает данные и запрашивает недостающие.
    """
    user_data = context.user_data
    documents = user_data.get('documents', [])
    service_type = user_data.get('service', '')

    # Инициализация словарей для данных
    user_data.update({
        'passport_fields': {}, 'migration_fields': {}, 'patent_fields': {},
        'dms_fields': {}, 'contract_fields': {}, 'manual_fields': {}, 'missing_fields': []
    })

    # Карта обработки: {ключевое_слово: (тип_документа, промпт, парсер, обязательные_поля)}
    processing_map = {
        'паспорт': ('passport', PROMPT_PASSPORT, parse_passport_fields, ['fio', 'birthdate', 'passport_number']),
        'патент': ('patent', PROMPT_PATENT, parse_patent_fields, ['patent_number', 'patent_date', 'patent_blank']),
    }

    # Определение обязательных документов и полей в зависимости от услуги
    if service_type == "Уведомление от работника иностранного гражданина":
        processing_map['патент'][3].append('inn') # Добавляем ИНН в обязательные для патента
        processing_map['дмс'] = ('dms', PROMPT_DMS, parse_dms_fields, ['policy_number', 'dms_insurer_phone', 'dms_insurer_email'])
        processing_map['договор'] = ('contract', PROMPT_CONTRACT, parse_contract_fields, ['position', 'contract_date'])
    else: # Для других услуг
        processing_map['миграцион'] = ('migration', PROMPT_MIGRATION, parse_migration_fields, ['migration_card_number', 'migration_card_date'])


    processed_docs_indices = set()

    for keyword, (doc_type, prompt, parser, req_fields) in processing_map.items():
        processed_this_type = False
        for i, doc in enumerate(documents):
            if i in processed_docs_indices:
                continue
            
            # Ищем по нескольким ключевым словам
            search_keywords = [keyword]
            if keyword == 'договор':
                search_keywords.append('тд')
            if keyword == 'дмс':
                search_keywords.append('страхов')

            if any(kw in doc['name'].lower() for kw in search_keywords):
                await update.message.reply_text(f"🔍 Обрабатываю: {doc['name']}...")
                try:
                    if doc['mime'] == 'application/pdf':
                        png_pages = convert_pdf_to_png(doc['bytes'])
                        raw_text = gcv_ocr_multiple(png_pages) if png_pages else ""
                    else:
                        raw_text = gcv_ocr(doc['bytes'])

                    if raw_text:
                        fields_raw = await extract_doc_fields_with_gpt(raw_text, prompt)
                        data = parser(fields_raw)
                        user_data[f'{doc_type}_fields'] = data
                        
                        # Проверка обязательных полей
                        for field in req_fields:
                            if not data.get(field) or data.get(field) == 'Не найдено':
                                user_data['missing_fields'].append((doc_type, field))
                        
                        processed_this_type = True
                        processed_docs_indices.add(i)
                        await update.message.reply_text(f"✅ Обработано: {doc['name']}")
                        break # Переходим к следующему типу документа
                except Exception as e:
                    logger.error(f"Ошибка обработки '{doc['name']}': {e}", exc_info=True)
                    await update.message.reply_text(f"❌ Ошибка обработки документа: {doc['name']}. Попробую запросить данные вручную.")
        
        if not processed_this_type:
            await update.message.reply_text(f"⚠️ Не найден или не удалось обработать документ типа '{keyword.capitalize()}'. Запрошу данные вручную.")
            # Добавляем все обязательные поля этого типа как недостающие
            for field in req_fields:
                user_data['missing_fields'].append((doc_type, field))

    # Убираем дубликаты из недостающих полей, сохраняя порядок
    unique_missing_fields = []
    seen = set()
    for item in user_data['missing_fields']:
        if item not in seen:
            unique_missing_fields.append(item)
            seen.add(item)
    user_data['missing_fields'] = unique_missing_fields

    # Запрос недостающих полей
    if user_data['missing_fields']:
        next_field_type, next_field_name = user_data['missing_fields'][0]
        field_desc = get_field_description(next_field_type, next_field_name)
        await update.message.reply_text(f"📝 Пожалуйста, введите: {field_desc}")
        return MANUAL_INPUT

    # Если все на месте, сохраняем
    from handlers.manual import save_application
    return await save_application(update, context)
