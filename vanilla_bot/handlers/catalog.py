from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from keyboards.menu import categories_keyboard, items_keyboard, item_detail_keyboard, back_keyboard
from services.menu_data import get_categories, get_items_by_category, get_item_by_id
from services.cart_service import get_user_cart

router = Router()

@router.callback_query(F.data == "menu:categories")
@router.message(F.text.lower() == "меню")
async def show_categories(cb_or_msg: types.CallbackQuery | types.Message):
    categories = get_categories()
    if not categories:
        text = " Каталог временно недоступен. Попробуйте позже."
    else:
        text = "🧁 <b>Категории:</b>\n\nВыберите раздел:"
    
    if isinstance(cb_or_msg, types.CallbackQuery):
        await cb_or_msg.message.edit_text(text, reply_markup=categories_keyboard(), parse_mode="HTML")
    else:
        await cb_or_msg.answer(text, reply_markup=categories_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("cat:"))
async def show_items(cb: types.CallbackQuery):
    category = cb.data.split(":", 1)[1]
    items = get_items_by_category(category)
    
    if not items:
        await cb.answer("🚫 В этой категории пока нет товаров", show_alert=True)
        return
    
    text = f"🍰 <b>{category}</b>\n\nДоступно товаров: {len(items)}"
    await cb.message.edit_text(text, reply_markup=items_keyboard(category), parse_mode="HTML")

@router.callback_query(F.data.startswith("item:"))
async def show_item(cb: types.CallbackQuery):
    item_id = cb.data.split(":", 1)[1]
    item = get_item_by_id(item_id)
    
    if not item or not item.available:
        await cb.answer("❌ Товар недоступен", show_alert=True)
        return
    
    text = (
        f"<b>{item.name}</b>\n"
        f"{item.description}\n\n"
        f"💰 <b>{item.price} ₽</b>"
    )
    
    # Если есть изображение — отправляем как фото
    if item.image_url:
        await cb.message.edit_media(
            types.MediaMedia(
                media=types.InputMediaPhoto(media=item.image_url, caption=text),
                reply_markup=item_detail_keyboard(item_id)
            ),
            parse_mode="HTML"
        )
    else:
        await cb.message.edit_text(text, reply_markup=item_detail_keyboard(item_id), parse_mode="HTML")

@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart(cb: types.CallbackQuery):
    item_id = cb.data.split(":", 2)[2]
    item = get_item_by_id(item_id)
    
    if not item:
        await cb.answer("❌ Ошибка: товар не найден", show_alert=True)
        return
    
    cart = get_user_cart(cb.from_user.id)
    cart.add_item(item_id)
    
    await cb.answer(f"✅ {item.name} добавлен в корзину", show_alert=False)
    
    # Опционально: показать мини-подтверждение с кнопкой "Перейти в корзину"
    # (реализуется через редактирование сообщения или отправку нового)