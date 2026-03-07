from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.cart import cart_keyboard, checkout_keyboard
from services.cart_service import get_user_cart, Cart
from services.menu_data import get_item_by_id
from services.order_notifier import notify_admin
from config import DELIVERY_FEE, FREE_DELIVERY_THRESHOLD, PICKUP_ADDRESS

router = Router()

class Checkout(StatesGroup):
    waiting_for_delivery_type = State()
    waiting_for_address = State()
    waiting_for_phone = State()
    waiting_for_payment_confirm = State()

@router.callback_query(F.data == "cart:view")
@router.message(F.text.lower() == "корзина")
async def view_cart(cb_or_msg: types.CallbackQuery | types.Message, bot: Bot):
    user_id = cb_or_msg.from_user.id if isinstance(cb_or_msg, types.CallbackQuery) else cb_or_msg.from_user.id
    cart = get_user_cart(user_id)
    
    if cart.is_empty():
        text = "🛒 Ваша корзина пуста.\nДобавьте что-нибудь вкусное из меню!"
        kb = None
    else:
        items = cart.get_summary()
        subtotal = cart.get_total()
        delivery = DELIVERY_FEE if subtotal < FREE_DELIVERY_THRESHOLD else 0
        total = subtotal + delivery
        
        text = f"🛒 <b>Ваш заказ</b>\n\n" + "\n".join(
            f"• {item['name']} × {item['qty']} = {item['subtotal']} ₽"
            for item in items
        ) + f"\n\n📦 Подытог: {subtotal} ₽"
        
        if delivery > 0:
            text += f"\n🚚 Доставка: {delivery} ₽"
        else:
            text += "\n🎁 Доставка: бесплатно!"
        
        text += f"\n💰 <b>Итого: {total} ₽</b>"
        kb = checkout_keyboard()
    
    if isinstance(cb_or_msg, types.CallbackQuery):
        await cb_or_msg.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await cb_or_msg.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "cart:clear")
async def clear_cart(cb: types.CallbackQuery):
    cart = get_user_cart(cb.from_user.id)
    cart.clear()
    await cb.answer("🗑️ Корзина очищена", show_alert=False)
    await view_cart(cb)  # обновить вид

@router.callback_query(F.data == "checkout:start")
async def start_checkout(cb: types.CallbackQuery, state: FSMContext):
    cart = get_user_cart(cb.from_user.id)
    if cart.is_empty():
        await cb.answer("❌ Сначала добавьте товары в корзину", show_alert=True)
        return
    
    await state.set_state(Checkout.waiting_for_delivery_type)
    await cb.message.edit_text(
        "🚚 <b>Способ получения</b>\n\nВыберите вариант:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🏠 Самовывоз", callback_data="delivery:pickup")],
            [types.InlineKeyboardButton(text="🚕 Доставка (+150 ₽)", callback_data="delivery:ship")],
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="cart:view")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("delivery:"))
async def select_delivery(cb: types.CallbackQuery, state: FSMContext):
    delivery_type = cb.data.split(":")[1]
    await state.update_data(delivery_type=delivery_type)
    
    if delivery_type == "pickup":
        await cb.message.edit_text(
            f"✅ <b>Самовывоз</b>\n\n"
            f"📍 Адрес: {PICKUP_ADDRESS}\n"
            f"🕒 Готовность: 30–45 минут\n\n"
            f"Введите ваш номер телефона для связи:",
            reply_markup=back_keyboard("checkout:start"),
            parse_mode="HTML"
        )
        await state.set_state(Checkout.waiting_for_phone)
    else:
        await cb.message.edit_text(
            "🚕 <b>Доставка</b>\n\n"
            "Введите адрес доставки (улица, дом, подъезд, код домофона):",
            reply_markup=back_keyboard("checkout:start"),
            parse_mode="HTML"
        )
        await state.set_state(Checkout.waiting_for_address)

@router.message(Checkout.waiting_for_address)
async def receive_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("📞 Введите ваш номер телефона для связи:")
    await state.set_state(Checkout.waiting_for_phone)

@router.message(Checkout.waiting_for_phone)
async def receive_phone(message: types.Message, state: FSMContext, bot: Bot):
    phone = message.text.strip()
    if not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
        await message.answer("❌ Пожалуйста, введите корректный номер телефона")
        return
    
    data = await state.get_data()
    delivery_type = data.get("delivery_type")
    
    # Формируем заказ
    user_cart = get_user_cart(message.from_user.id)
    items = user_cart.get_summary()
    subtotal = user_cart.get_total()
    delivery_fee = DELIVERY_FEE if (delivery_type == "ship" and subtotal < FREE_DELIVERY_THRESHOLD) else 0
    total = subtotal + delivery_fee
    
    order_data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "full_name": message.from_user.full_name,
        "phone": phone,
        "delivery_type": "Самовывоз" if delivery_type == "pickup" else "Доставка",
        "address": data.get("address", PICKUP_ADDRESS) if delivery_type == "ship" else PICKUP_ADDRESS,
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "created_at": message.date.isoformat()
    }
    
    # Сохраняем заказ (в продакшене — в БД)
    # Здесь просто передаём в оплату
    
    # Создаём платёж (если подключена ЮKassa)
    from services.payment_gateway import PaymentGateway
    payment_url = await PaymentGateway.create_payment(
        order_id=f"ORD_{message.from_user.id}_{int(message.date.timestamp())}",
        amount=total,
        description=f"Заказ в «Стручок Ванили»",
        user_email=None  # можно запросить ранее
    )
    
    if payment_url:
        await message.answer(
            f"💳 <b>Оплата заказа</b>\n\n"
            f"Сумма: {total} ₽\n"
            f"Нажмите кнопку ниже для оплаты:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
                [types.InlineKeyboardButton(text="❌ Отмена", callback_data="order:cancel")]
            ]),
            parse_mode="HTML"
        )
        await state.set_state(Checkout.waiting_for_payment_confirm)
        await state.update_data(order_data=order_data)
    else:
        # Фолбэк: заказ без онлайн-оплаты (наличными/при получении)
        await notify_admin(bot, order_data)
        user_cart.clear()
        await message.answer(
            f"✅ <b>Заказ принят!</b>\n\n"
            f"📋 Номер: #{order_data['user_id']}_{int(order_data['created_at'].timestamp())}\n"
            f"💰 Сумма: {total} ₽\n"
            f"🚚 {order_data['delivery_type']}: {order_data['address']}\n\n"
            f"Менеджер свяжется с вами в течение 15 минут для подтверждения. 📞",
            parse_mode="HTML"
        )
        await state.clear()

@router.callback_query(F.data == "order:cancel")
async def cancel_order(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❌ Оплата отменена. Вы можете оформить заказ позже.")
    await state.clear()