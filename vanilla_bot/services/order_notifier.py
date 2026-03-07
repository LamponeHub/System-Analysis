import logging
from aiogram import Bot
from typing import Dict, List
from config import ADMIN_CHAT_ID

logger = logging.getLogger(__name__)

async def notify_admin(bot: Bot, order_data: Dict):
    """Отправляет уведомление о новом заказе в админ-чат"""
    if not ADMIN_CHAT_ID:
        logger.warning("⚠️ ADMIN_CHAT_ID не задан — уведомление пропущено")
        return
    
    items_text = "\n".join(
        f"  • {item['name']} × {item['qty']} = {item['subtotal']} ₽"
        for item in order_data.get("items", [])
    )
    
    delivery_text = (
        f"🚚 {order_data['delivery_type']}" 
        + (f": {order_data['address']}" if order_data.get("address") else "")
    )
    
    text = (
        f"🔔 <b>Новый заказ #{order_data['user_id']}_{int(order_data['created_at'].timestamp())}</b>\n\n"
        f"👤 <b>Клиент:</b> {order_data.get('full_name', '—')} "
        f"(@{order_data.get('username', '—')})\n"
        f"📞 {order_data.get('phone', '—')}\n\n"
        f"📦 <b>Товары:</b>\n{items_text}\n\n"
        f"📦 Подытог: {order_data.get('subtotal', 0)} ₽\n"
        f"{f"🚚 Доставка: {order_data.get('delivery_fee', 0)} ₽\n" if order_data.get('delivery_fee', 0) > 0 else ''}"
        f"💰 <b>Итого: {order_data.get('total', 0)} ₽</b>\n\n"
        f"{delivery_text}\n\n"
        f"🕒 {order_data.get('created_at', '—')}"
    )
    
    try:
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
        logger.info(f"📤 Уведомление отправлено админу: заказ #{order_data['user_id']}")
    except Exception as e:
        logger.error(f"❌ Не удалось отправить уведомление: {e}")

async def notify_client(bot: Bot, user_id: int, message: str, parse_mode: str = "HTML"):
    """Безопасная отправка сообщения клиенту (с обработкой, если бот заблокирован)"""
    try:
        await bot.send_message(user_id, message, parse_mode=parse_mode)
        return True
    except Exception as e:
        logger.warning(f"⚠️ Не удалось уведомить клиента {user_id}: {e}")
        return False