from states import SELECT_SERVICE
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from keyboards import SERVICE_OPTIONS, ADD_EMPLOYEE_OPTION

async def add_another_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    if "добавить" in answer.lower():
        company_name = context.user_data['company_name']
        company_inn = context.user_data['company_inn']
        context.user_data.clear()
        context.user_data['company_name'] = company_name
        context.user_data['company_inn'] = company_inn
        await update.message.reply_text(
            "👤 Начнем добавление нового сотрудника!\n"
            "Выберите тип услуги:",
            reply_markup=ReplyKeyboardMarkup(SERVICE_OPTIONS, resize_keyboard=True)
        )
        return SELECT_SERVICE
    else:
        await update.message.reply_text(
            "🏁 Работа завершена. Для нового оформления введите /start",
            reply_markup=ReplyKeyboardRemove()
        )
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
