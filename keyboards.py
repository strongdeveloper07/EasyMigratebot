from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

SERVICE_OPTIONS = [
    ["Постановка на учет"],
    ["Заключение трудового договора"],
    ["Расторжение трудового договора"],
    ["Снятие с учета"],
    ["Уведомление от работника иностранного гражданина"],
    ["Перевод паспорта"]
]
CITY_OPTIONS = [["Волжский"], ["Долгопрудный"], ["Дмитров"]]
STAGE_OPTIONS = [["Первичная"], ["Продление"]]
ADD_EMPLOYEE_OPTION = [["✅ Добавить еще сотрудника"], ["🏁 Завершить"]]
DONE_UPLOADING = [["🏁 Завершить загрузку"]]

def back_to_menu_kb():
    """
    Создает клавиатуру с кнопкой возврата в главное меню
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой возврата
    """
    keyboard = [["🏠 Вернуться в главное меню"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
