from telegram import Update
from telegram.ext import ContextTypes
from states import MANUAL_INPUT, UPLOAD_DOCUMENTS
from handlers.manual import save_application
from handlers.documents import get_field_description
from utils.ocr import convert_pdf_to_png, gcv_ocr, gcv_ocr_multiple
from utils.prompts import PROMPT_PASSPORT, PROMPT_MIGRATION, PROMPT_PATENT, PROMPT_DMS
from utils.gpt import extract_doc_fields_with_gpt
from utils.parsers import parse_passport_fields, parse_migration_fields, parse_patent_fields, parse_dms_fields
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

async def process_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    documents = user_data.get('documents', [])
    service_type = user_data.get('service', '')
    
    if not documents:
        await update.message.reply_text("❌ Нет документов для обработки. Попробуйте еще раз.")
        return UPLOAD_DOCUMENTS
    
    user_data['passport_fields'] = {}
    user_data['migration_fields'] = {}
    user_data['patent_fields'] = {}
    user_data['dms_fields'] = {}
    user_data['manual_fields'] = {}
    user_data['missing_fields'] = []
    
    # 1. Обработка паспорта (без использования ФИО — оно берётся только из патента)
    passport_processed = False
    for doc in documents:
        if 'паспорт' in doc['name'].lower() or 'passport' in doc['name'].lower():
            await update.message.reply_text("🔍 Обрабатываю паспорт...")
            try:
                if doc['mime'] == 'application/pdf':
                    png_pages = convert_pdf_to_png(doc['bytes'], pages=[1])
                    raw_text = gcv_ocr(png_pages[0]) if png_pages else ""
                else:
                    raw_text = gcv_ocr(doc['bytes'])
                if raw_text:
                    fields_raw = await extract_doc_fields_with_gpt(raw_text, PROMPT_PASSPORT)
                    passport_data = parse_passport_fields(fields_raw)
                    # Удаляем ФИО, чтобы гарантировать использование патента
                    passport_data.pop('fio', None)
                    required_fields = ['birthdate', 'passport_number']  # fio убран
                    for field in required_fields:
                        if not passport_data.get(field) or passport_data.get(field) in ['Не найдено', 'не найден', 'не указано', 'нет', 'n/a', 'none', 'null', '-', '—']:
                            user_data['missing_fields'].append(('passport', field))
                    user_data['passport_fields'] = passport_data
                    passport_processed = True
                    break
            except Exception as e:
                logger.error(f"Ошибка обработки паспорта: {e}", exc_info=True)
    if not passport_processed:
        await update.message.reply_text("❌ Не удалось обработать паспорт. Введите данные вручную.")
        user_data['missing_fields'].extend([
            # fio не запрашиваем на этапе паспорта
            ('passport', 'birthdate'),
            ('passport', 'passport_number')
        ])
    
    # 2. Обработка миграционной карты
    migration_processed = False
    if service_type != "Уведомление от работника иностранного гражданина":
        for doc in documents:
            if 'миграцион' in doc['name'].lower() or 'migration' in doc['name'].lower():
                await update.message.reply_text("🔍 Обрабатываю миграционную карту...")
                try:
                    if doc['mime'] == 'application/pdf':
                        png_pages = convert_pdf_to_png(doc['bytes'], pages=[1])
                        raw_text = gcv_ocr(png_pages[0]) if png_pages else ""
                    else:
                        raw_text = gcv_ocr(doc['bytes'])
                    
                    if raw_text:
                        fields_raw = await extract_doc_fields_with_gpt(raw_text, PROMPT_MIGRATION)
                        migration_data = parse_migration_fields(fields_raw)
                        
                        required_fields = ['migration_card_number', 'migration_card_date']
                        for field in required_fields:
                            if not migration_data.get(field) or migration_data.get(field) in ['Не найдено', 'не найден', 'не указано', 'нет', 'n/a', 'none', 'null', '-', '—']:
                                user_data['missing_fields'].append(('migration', field))
                        
                        user_data['migration_fields'] = migration_data
                        migration_processed = True
                        break
                except Exception as e:
                    logger.error(f"Ошибка обработки миграционной карты: {e}", exc_info=True)
    
        if not migration_processed:
            await update.message.reply_text("❌ Не удалось обработать миграционную карту. Введите данные вручную.")
            user_data['missing_fields'].extend([
                ('migration', 'migration_card_number'),
                ('migration', 'migration_card_date')
            ])
    
    # 3. Обработка патента (fio обязательно тут)
    patent_processed = False
    for doc in documents:
        if 'патент' in doc['name'].lower() or 'patent' in doc['name'].lower():
            await update.message.reply_text("🔍 Обрабатываю патент...")
            try:
                if doc['mime'] == 'application/pdf':
                    png_pages = convert_pdf_to_png(doc['bytes'], pages=[1, 2])
                    raw_text = gcv_ocr_multiple(png_pages)
                else:
                    raw_text = gcv_ocr(doc['bytes'])
                if raw_text:
                    fields_raw = await extract_doc_fields_with_gpt(raw_text, PROMPT_PATENT)
                    patent_data = parse_patent_fields(fields_raw)

                    passport_fields = user_data['passport_fields']
                    # ФИО используем ТОЛЬКО из патента, не копируем в passport_fields
                    if patent_data.get('fio'):
                        patent_data['fio'] = patent_data['fio'].upper()
                    # Обязательные поля: fio теперь проверяется здесь
                    if service_type == "Уведомление от работника иностранного гражданина":
                        required_fields = ['fio', 'patent_number', 'patent_date', 'inn']
                    else:
                        required_fields = ['fio', 'patent_number', 'patent_date', 'patent_blank']
                    for field in required_fields:
                        if not patent_data.get(field) or patent_data.get(field) in ['Не найдено', 'не найден', 'не указано', 'нет', 'n/a', 'none', 'null', '-', '—']:
                            user_data['missing_fields'].append(('patent', field))
                    if patent_data.get('patent_date'):
                        try:
                            issue_date = datetime.strptime(patent_data['patent_date'], '%d.%m.%Y')
                            patent_data['patent_until'] = (issue_date + timedelta(days=365)).strftime('%d.%m.%Y')
                        except:
                            patent_data['patent_until'] = 'Не определено'
                    user_data['patent_fields'] = patent_data
                    patent_processed = True
                    break
            except Exception as e:
                logger.error(f"Ошибка обработки патента: {e}", exc_info=True)
    if not patent_processed:
        await update.message.reply_text("❌ Не удалось обработать патент. Введите данные вручную.")
        if service_type == "Уведомление от работника иностранного гражданина":
            user_data['missing_fields'].extend([
                ('patent', 'patent_number'),
                ('patent', 'patent_date'),
                ('patent', 'inn')
            ])
        else:
            user_data['missing_fields'].extend([
                ('patent', 'patent_number'),
                ('patent', 'patent_date'),
                ('patent', 'patent_blank')
            ])
    # 4. Обработка ДМС
    dms_processed = False
    if service_type == "Уведомление от работника иностранного гражданина":
        for doc in documents:
            if 'дмс' in doc['name'].lower() or 'страхован' in doc['name'].lower() or 'dms' in doc['name'].lower():
                await update.message.reply_text("🔍 Обрабатываю полис ДМС...")
                try:
                    if doc['mime'] == 'application/pdf':
                        png_pages = convert_pdf_to_png(doc['bytes'], pages=[1])
                        raw_text = gcv_ocr(png_pages[0]) if png_pages else ""
                    else:
                        raw_text = gcv_ocr(doc['bytes'])
                    
                    if raw_text:
                        fields_raw = await extract_doc_fields_with_gpt(raw_text, PROMPT_DMS)
                        dms_data = parse_dms_fields(fields_raw)
                        
                        required_fields = ['dms_number', 'insurance_expiry', 'insurance_date']
                        for field in required_fields:
                            if not dms_data.get(field) or dms_data.get(field) in ['Не найдено', 'не найден', 'не указано', 'нет', 'n/a', 'none', 'null', '-', '—']:
                                user_data['missing_fields'].append(('dms', field))
                        
                        user_data['dms_fields'] = dms_data
                        dms_processed = True
                        break
                except Exception as e:
                    logger.error(f"Ошибка обработки полиса ДМС: {e}", exc_info=True)
    
        if not dms_processed:
            await update.message.reply_text("❌ Не удалось обработать полис ДМС. Введите данные вручную.")
            user_data['missing_fields'].extend([
                ('dms', 'dms_number'),
                ('dms', 'insurance_expiry'),
                ('dms', 'insurance_date'),
            ])
    
    if user_data['missing_fields']:
        next_field = user_data['missing_fields'][0]
        field_desc = get_field_description(next_field[0], next_field[1])
        await update.message.reply_text(f"📝 Пожалуйста, введите {field_desc}:")
        return MANUAL_INPUT
    
    from handlers.manual import save_application
    return await save_application(update, context)
