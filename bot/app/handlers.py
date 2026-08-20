from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db import Database
from app.faq import FAQ_ITEMS
from app.keyboards import (
    BTN_ABOUT,
    BTN_BACK,
    BTN_FAQ,
    BTN_USAGE,
    back_menu,
    faq_keyboard,
    main_menu,
)
from app.states import AppealForm

router = Router()


async def save_message_user(db: Database, message: Message) -> None:
    user = message.from_user
    if not user:
        return

    await db.save_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    await save_message_user(db, message)

    await message.answer(
        "Assalomu alaykum! CRM support botiga xush kelibsiz.\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_BACK)
async def back_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu())


@router.message(F.text.in_({BTN_ABOUT, BTN_USAGE}))
async def appeal_start_handler(message: Message, state: FSMContext, db: Database) -> None:
    await save_message_user(db, message)

    category = "Dastur haqida savol" if message.text == BTN_ABOUT else "Dasturni ishlatish haqida savol"

    await state.set_state(AppealForm.full_name)
    await state.update_data(category=category)

    await message.answer(
        "Ism familiyangizni yozing.\n\n"
        "Masalan: Ali Valiyev",
        reply_markup=back_menu(),
    )


@router.message(F.text == BTN_FAQ)
async def faq_list_handler(message: Message, db: Database) -> None:
    await save_message_user(db, message)
    await message.answer(
        "Ko'p beriladigan savollar ro'yxati:",
        reply_markup=faq_keyboard(),
    )


@router.callback_query(F.data.startswith("faq:"))
async def faq_answer_handler(callback: CallbackQuery) -> None:
    try:
        index = int(callback.data.split(":", 1)[1])
        item = FAQ_ITEMS[index]
    except (ValueError, IndexError):
        await callback.answer("Savol topilmadi", show_alert=True)
        return

    await callback.message.answer(
        f"<b>{escape(item['question'])}</b>\n\n{escape(item['answer'])}",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AppealForm.full_name)
async def full_name_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()

    if len(text) < 3:
        await message.answer("Ism familiya juda qisqa. Iltimos, to'liqroq yozing.")
        return

    await state.update_data(full_name=text)
    await state.set_state(AppealForm.phone)

    await message.answer(
        "Telefon raqamingizni yozing.\n\n"
        "Masalan: +998901234567",
        reply_markup=back_menu(),
    )


@router.message(AppealForm.phone)
async def phone_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()

    digits_count = sum(char.isdigit() for char in text)
    if digits_count < 9:
        await message.answer("Telefon raqam noto'g'ri ko'rinyapti. Qayta yozing. Masalan: +998901234567")
        return

    await state.update_data(phone=text)
    await state.set_state(AppealForm.question)

    await message.answer(
        "Murojaatingizni yozing.\n\n"
        "Muammoni iloji boricha tushunarli qilib yozing.",
        reply_markup=back_menu(),
    )


@router.message(AppealForm.question)
async def question_handler(message: Message, state: FSMContext, bot: Bot, db: Database, support_group_id: int) -> None:
    user = message.from_user
    if not user:
        return

    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer("Murojaat juda qisqa. Iltimos, muammoni to'liqroq yozing.")
        return

    data = await state.get_data()

    ticket_id = await db.create_ticket(
        user_telegram_id=user.id,
        category=data["category"],
        full_name=data["full_name"],
        phone=data["phone"],
        question=text,
    )

    username_text = f"@{user.username}" if user.username else "username yo'q"

    group_text = (
        f"🆕 <b>Yangi murojaat #{ticket_id}</b>\n\n"
        f"📂 <b>Bo'lim:</b> {escape(data['category'])}\n"
        f"👤 <b>F.I.O:</b> {escape(data['full_name'])}\n"
        f"📞 <b>Telefon:</b> {escape(data['phone'])}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"🔗 <b>Username:</b> {escape(username_text)}\n\n"
        f"📝 <b>Murojaat:</b>\n{escape(text)}\n\n"
        f"Javob berish uchun shu xabarga reply qiling."
    )

    sent_to_group = await bot.send_message(
        chat_id=support_group_id,
        text=group_text,
        parse_mode="HTML",
    )

    await db.set_ticket_group_message(ticket_id=ticket_id, group_message_id=sent_to_group.message_id)

    sent_to_user = await message.answer(
        f"✅ Murojaatingiz qabul qilindi.\n\n"
        f"Murojaat raqami: <b>#{ticket_id}</b>\n"
        f"Support javobini kuting.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )

    await db.add_message_link(
        ticket_id=ticket_id,
        user_telegram_id=user.id,
        group_message_id=sent_to_group.message_id,
        user_message_id=sent_to_user.message_id,
    )

    await state.clear()


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def group_reply_handler(message: Message, bot: Bot, db: Database) -> None:
    if not message.reply_to_message:
        return

    if not message.text:
        await message.reply("Hozircha faqat matnli javob yuboriladi.")
        return

    ticket = await db.get_ticket_by_group_message(message.reply_to_message.message_id)
    if not ticket:
        return

    answer_text = (
        f"📩 <b>Support javobi</b>\n"
        f"Murojaat raqami: <b>#{ticket['id']}</b>\n\n"
        f"{escape(message.text)}\n\n"
        f"Yana savolingiz bo'lsa, shu xabarga reply qilib yozing."
    )

    sent_to_user = await bot.send_message(
        chat_id=ticket["user_telegram_id"],
        text=answer_text,
        parse_mode="HTML",
    )

    await db.add_message_link(
        ticket_id=ticket["id"],
        user_telegram_id=ticket["user_telegram_id"],
        group_message_id=message.message_id,
        user_message_id=sent_to_user.message_id,
    )

    await message.reply("✅ Javob mijozga yuborildi.")


@router.message(F.chat.type == "private", F.reply_to_message)
async def user_reply_to_support_handler(message: Message, bot: Bot, db: Database, support_group_id: int) -> None:
    user = message.from_user
    if not user or not message.reply_to_message:
        return

    if not message.text:
        await message.answer("Hozircha faqat matnli xabar yuboriladi.")
        return

    ticket = await db.get_ticket_by_user_message(
        user_telegram_id=user.id,
        user_message_id=message.reply_to_message.message_id,
    )
    if not ticket:
        return

    group_text = (
        f"💬 <b>Mijozdan yangi javob #{ticket['id']}</b>\n\n"
        f"👤 <b>F.I.O:</b> {escape(ticket['full_name'])}\n"
        f"📞 <b>Telefon:</b> {escape(ticket['phone'])}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n\n"
        f"📝 <b>Xabar:</b>\n{escape(message.text)}\n\n"
        f"Javob berish uchun shu xabarga reply qiling."
    )

    sent_to_group = await bot.send_message(
        chat_id=support_group_id,
        text=group_text,
        parse_mode="HTML",
    )

    await db.add_message_link(
        ticket_id=ticket["id"],
        user_telegram_id=user.id,
        group_message_id=sent_to_group.message_id,
        user_message_id=message.message_id,
    )

    await message.answer("✅ Xabaringiz support guruhga yuborildi.")


@router.message(F.chat.type == "private")
async def private_unknown_handler(message: Message, db: Database) -> None:
    await save_message_user(db, message)
    await message.answer(
        "Kerakli bo'limni tanlang yoki /start bosing.",
        reply_markup=main_menu(),
    )
