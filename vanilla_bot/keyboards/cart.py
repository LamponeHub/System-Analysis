from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def cart_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="cart:clear")],
        [InlineKeyboardButton(text="🔙 Продолжить покупки", callback_data="menu:categories")]
    ])

def checkout_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout:start")],
        [InlineKeyboardButton(text="🔙 Продолжить покупки", callback_data="menu:categories")]
    ])