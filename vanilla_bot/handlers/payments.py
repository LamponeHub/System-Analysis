from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from services.payment_gateway import PaymentGateway

router = Router()

@router.callback_query(F.data.startswith("payment:success"))
async def payment_success(cb: types.CallbackQuery, state: FSMContext):
    """Обработчик успешной оплаты (вызывается после возврата из платёжной системы)"""
    # В реальном проекте здесь проверяется подпись вебхука от платёжной системы
    order_data = (await state.get_data()).get("order_data")
    
    if not order_data:
        await cb.answer("⚠️ Данные заказа не найдены", show_alert=True)
        return
    
    # Уведомляем админа
    from services.order_notifier import notify_admin
    await notify_admin(cb.bot, order_data)
    
    # Очищаем корзину
    from services.cart_service import get_user_cart
    get_user_cart(cb.from_user.id).clear()
    
    await cb.message.edit_text(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"📋 Ваш заказ #{order_data['user_id']}_{int(order_data['created_at'].timestamp())} принят в работу.\n"
        f"📱 Менеджер свяжется с вами в ближайшее время.\n\n"
        f"Спасибо, что выбрали «Стручок Ванили»! 🧁✨",
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data.startswith("payment:fail"))
async def payment_fail(cb: types.CallbackQuery):
    await cb.message.edit_text(
        "❌ <b>Оплата не прошла</b>\n\n"
        "Возможные причины:\n"
        "• Недостаточно средств\n"
        "• Ошибка банка\n"
        "• Превышен лимит времени сессии\n\n"
        "Попробуйте ещё раз или выберите оплату при получении.",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔁 Повторить оплату", callback_data="checkout:start")],
            [types.InlineKeyboardButton(text="🏠 В меню", callback_data="menu:categories")]
        ])
    )