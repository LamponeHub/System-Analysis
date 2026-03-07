from aiogram import Router, F, types
from aiogram.filters import Command
from config import ADMIN_CHAT_ID

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        await message.answer("🔐 Доступ запрещён")
        return
    
    await message.answer(
        "🛠️ <b>Панель администратора</b>\n\n"
        "Доступные команды:\n"
        "• /orders — последние заказы\n"
        "• /stats — статистика за день\n"
        "• /broadcast — рассылка клиентам",
        parse_mode="HTML"
    )

@router.message(Command("orders"))
async def cmd_orders(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    
    # В реальном проекте — запрос к БД
    await message.answer("📋 Список заказов (заглушка):\n• Заказ #123 — 1 200 ₽ — в работе\n• Заказ #124 — 850 ₽ — готов")