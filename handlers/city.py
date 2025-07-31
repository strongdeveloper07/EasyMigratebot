from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import DONE_UPLOADING
from states import UPLOAD_DOCUMENTS

async def select_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    context.user_data["city"] = city
    instruction = (
        "📎 <b>Прикрепите следующие документы:</b>\n\n"
        "1. Паспорт иностранного гражданина (все страницы с отметками)\n"
        "2. Патент (обе стороны)\n"
        "3. Трудовой договор\n"
        "4. ДМС (полис добровольного медицинского страхования)\n\n"
        "⚠️ <b>Требования к документам:</b>\n"
        "- Цветные сканы в формате PDF или JPEG\n"
        "- Страницы в горизонтальной ориентации\n"
        "- Четкий текст без затемнений\n"
        "- Многостраничные документы загружайте полностью\n"
        "- Патент: обе стороны документа\n\n"
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
