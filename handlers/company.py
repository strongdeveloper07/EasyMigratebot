from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from states import COMPANY_INN, SELECT_SERVICE
from keyboards import SERVICE_OPTIONS

async def get_company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["company_name"] = update.message.text.strip()
    await update.message.reply_text("📝 Введите ИНН вашей компании (10 или 12 цифр):")
    return COMPANY_INN

async def get_company_inn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inn = update.message.text.strip()
    if not inn.isdigit() or len(inn) not in (10, 12):
        await update.message.reply_text("❌ Неверный ИНН. Введите 10 или 12 цифр:")
        return COMPANY_INN
    context.user_data["company_inn"] = inn
    await update.message.reply_text(
        "🔍 Выберите тип услуги:",
        reply_markup=ReplyKeyboardMarkup(SERVICE_OPTIONS, resize_keyboard=True),
    )
    return SELECT_SERVICE
