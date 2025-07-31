from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from states import COMPANY_NAME

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Добро пожаловать в EasyMigrateBot!\n\n"
        "Введите название вашей компании:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return COMPANY_NAME
