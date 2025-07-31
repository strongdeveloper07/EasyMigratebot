from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import DONE_UPLOADING
from states import UPLOAD_DOCUMENTS

async def select_stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stage"] = update.message.text.strip()
    instruction = (
        "📎 <b>Прикрепите следующие документы:</b>\n\n"
        "1. Паспорт иностранного гражданина (все страницы с отметками)\n"
        "2. Миграционная карта\n"
        "3. Патент (обе стороны)\n"
        "4. Миграционный учет (если есть)\n\n"
        "⚠️ <b>Требования к документам:</b>\n"
        "- Цветные сканы в формате PDF или JPEG\n"
        "- Страницы в горизонтальной ориентации\n"
        "- Четкий текст без затемнений\n"
        "- Паспорт: первая страница должна быть первой в файле\n"
        "- Патент и миграционный учет: обе стороны документа\n\n"
        "Вы можете загружать документы по одному или несколько сразу. "
        "После загрузки всех документов нажмите <b>'🏁 Завершить загрузку'</b>."
    )
    await update.message.reply_text(
        instruction,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(DONE_UPLOADING, resize_keyboard=True)
    )
    context.user_data['documents'] = []
    return UPLOAD_DOCUMENTS
