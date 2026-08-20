from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.faq import FAQ_ITEMS

BTN_ABOUT = "📌 Dastur haqida savol berish"
BTN_USAGE = "🛠 Dasturni ishlatish haqida savol"
BTN_FAQ = "❓ Ko'p beriladigan savollar"
BTN_BACK = "⬅️ Orqaga"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ABOUT)],
            [KeyboardButton(text=BTN_USAGE)],
            [KeyboardButton(text=BTN_FAQ)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo'limni tanlang",
    )


def back_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)]],
        resize_keyboard=True,
    )


def faq_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for index, item in enumerate(FAQ_ITEMS):
        buttons.append([
            InlineKeyboardButton(
                text=item["question"],
                callback_data=f"faq:{index}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
