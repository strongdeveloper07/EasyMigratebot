from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import SERVICE_OPTIONS, CITY_OPTIONS, STAGE_OPTIONS
from states import SELECT_CITY, SELECT_STAGE

async def select_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text.strip()
    context.user_data["service"] = service
    if service == "Уведомление от работника иностранного гражданина":
        await update.message.reply_text(
            "🏙 Выберите город для уведомления:",
            reply_markup=ReplyKeyboardMarkup(CITY_OPTIONS, resize_keyboard=True),
        )
        return SELECT_CITY
    elif service == "Перевод паспорта":
        await update.message.reply_text(
            "📎 Прикрепите фото или PDF паспорта для перевода.",
            reply_markup=None
        )
        context.user_data['documents'] = []
        from states import UPLOAD_DOCUMENTS
        return UPLOAD_DOCUMENTS
    else:
        await update.message.reply_text(
            "📅 Выберите этап оформления:",
            reply_markup=ReplyKeyboardMarkup(STAGE_OPTIONS, resize_keyboard=True),
        )
        return SELECT_STAGE
