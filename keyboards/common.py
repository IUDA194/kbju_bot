from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Мои БЖУ сегодня")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def record_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Записать в граммах", callback_data="record:grams")
    builder.button(text="📥 Записать в порциях", callback_data="record:servings")
    builder.adjust(1)
    return builder.as_markup()


def track_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Трек", callback_data="record:track")
    return builder.as_markup()
