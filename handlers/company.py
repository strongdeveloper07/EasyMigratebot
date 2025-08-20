from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from states import COMPANY_INN, SELECT_SERVICE
from keyboards import SERVICE_OPTIONS

# Справочник компаний по ИНН
COMPANY_DATA_BY_INN = {
    "7733450363": {
        "name": "ООО \"ЭЛЕНВКВ\"",
        "full_name": "ООО \"ЭЛЕНВКВ\"",
        "legal_address": "Г. МОСКВА, ВН. ТЕР. Г. МУНИЦИПАЛЬНЫЙ ОКРУГ ЮЖНОЕ ТУШИНО, УЛ. ВАСИЛИЯ ПЕТУШКОВА, Д. 8, ПОМЕЩЕНИЕ 1/1А",
        "inn": "7733450363",
        "ogrn": "1247700503885",
        "kpp": "773301001"
    }
}

# Состояние ожидания названия компании для неизвестных ИНН
WAITING_COMPANY_NAME = "waiting_company_name"

async def get_company_inn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Проверяем, ожидаем ли мы название компании
    if context.user_data.get("state") == WAITING_COMPANY_NAME:
        context.user_data["company_name"] = text
        context.user_data.pop("state", None)  # Убираем временное состояние
        await update.message.reply_text(
            "🔍 Выберите тип услуги:",
            reply_markup=ReplyKeyboardMarkup(SERVICE_OPTIONS, resize_keyboard=True),
        )
        return SELECT_SERVICE
    
    # Обработка ИНН
    inn = text
    if not inn.isdigit() or len(inn) not in (10, 12):
        await update.message.reply_text("❌ Неверный ИНН. Введите 10 или 12 цифр:")
        return COMPANY_INN
    
    context.user_data["company_inn"] = inn
    
    # Автоматическое определение компании по ИНН
    if inn in COMPANY_DATA_BY_INN:
        company_info = COMPANY_DATA_BY_INN[inn]
        # Сохраняем ВСЕ данные компании в user_data для передачи в PDF
        context.user_data["company_name"] = company_info["name"]
        context.user_data["company_address"] = company_info["legal_address"]
        context.user_data["ogrn"] = company_info["ogrn"]
        context.user_data["kpp"] = company_info["kpp"]
        # ИНН уже сохранен выше
        
        await update.message.reply_text(
            f"✅ Компания найдена: {company_info['name']}\n\n"
            "🔍 Выберите тип услуги:",
            reply_markup=ReplyKeyboardMarkup(SERVICE_OPTIONS, resize_keyboard=True),
        )
        return SELECT_SERVICE
    else:
        # Для неизвестных ИНН просим ввести название
        context.user_data["state"] = WAITING_COMPANY_NAME
        await update.message.reply_text("🏢 Введите название вашей компании:")
        return COMPANY_INN
