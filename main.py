import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters
from config import TELEGRAM_TOKEN
from handlers.start import start
from handlers.company import get_company_inn
from handlers.service import select_service
from handlers.city import select_city
from handlers.stage import select_stage
from handlers.documents import upload_documents
from handlers.manual import manual_input
from handlers.employee import add_another_employee
from handlers.cancel import cancel


# Состояния диалога импортируются из states.py
from states import COMPANY_INN, SELECT_SERVICE, SELECT_CITY, SELECT_STAGE, UPLOAD_DOCUMENTS, PROCESS_DOCUMENTS, MANUAL_INPUT, ADD_ANOTHER_EMPLOYEE

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not TELEGRAM_TOKEN:
        logger.error("Ошибка: Не задан TELEGRAM_TOKEN")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            COMPANY_INN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company_inn)],
            SELECT_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_service)],
            SELECT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_city)],
            SELECT_STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_stage)],
            UPLOAD_DOCUMENTS: [
                MessageHandler(filters.Document.ALL | filters.PHOTO, upload_documents),
                MessageHandler(filters.TEXT & filters.Regex(r'^🏁 Завершить загрузку$'), upload_documents)
            ],
            MANUAL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, manual_input)],
            ADD_ANOTHER_EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_another_employee)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    logger.info("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
