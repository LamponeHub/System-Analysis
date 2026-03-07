from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.menu_data import get_categories, get_items_by_category

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍰 Меню", callback_data="menu:categories")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart:view")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
        [InlineKeyboardButton(text="📞 Связаться", url="https://t.me/struchok_vanili_manager")]
    ])

def categories_keyboard():
    kb = [[InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")] for cat in get_categories()]
    kb.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart:view")])
    kb.append([InlineKeyboardButton(text="🏠 В главное меню", callback_data="start")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def items_keyboard(category: str):
    kb = [
        [InlineKeyboardButton(text=f"{item.name} — {item.price} ₽", callback_data=f"item:{item.id}")]
        for item in get_items_by_category(category)
    ]
    kb.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu:categories")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def item_detail_keyboard(item_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ В корзину", callback_data=f"cart:add:{item_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back_to_cat")]
    ])

def back_keyboard(callback_data: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])