from aiogram import Router, types, F
from aiogram.filters import CommandStart
from keyboards.menu import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        f"🧁 <b>Добро пожаловать в «Стручок Ванили»!</b>\n\n"
        f"Мы печём с любовью с 2018 года ✨\n"
        f"📍 {message.bot.get('pickup_address', 'Москва, ул. Примерная, д. 1')}\n\n"
        f"Что делаем:\n"
        f"• Свежая выпечка ежедневно 🥐\n"
        f"• Торты на заказ 🎂\n"
        f"• Кофе и десерты с собой ☕\n\n"
        f"Выберите действие:"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@router.message(F.text.lower() == "помощь")
@router.message(CommandStart(deep_link="help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "🔹 /start — главное меню\n"
        "🔹 /menu — каталог товаров\n"
        "🔹 /cart — ваша корзина\n"
        "🔹 /pay — оплатить заказ (если есть активный)\n"
        "🔹 /support — связаться с менеджером\n\n"
        "📞 Телефон: +7 (495) 123-45-67\n"
        "🕒 Режим работы: 9:00–21:00",
        parse_mode="HTML"
    )