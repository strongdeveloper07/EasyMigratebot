from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from states import COMPANY_INN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Добро пожаловать в EasyMigrateBot!\n\n"
        "📝 Введите ИНН вашей компании (10 или 12 цифр):",
        reply_markup=ReplyKeyboardRemove(),
    )
    return COMPANY_INN
