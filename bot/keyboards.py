from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Добавить купон')],
    [KeyboardButton(text='Информация о розыгрыше')],
    [KeyboardButton(text='FAQ')],
    [KeyboardButton(text='Мои купоны')],
])