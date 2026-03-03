import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from yookassa import Configuration, Payment

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"
YOOKASSA_SHOP_ID = "ВАШ_SHOP_ID"
YOOKASSA_SECRET_KEY = "ВАШ_SECRET_KEY"
ADMIN_ID = 123456789  # Ваш числовой ID в Telegram

# Настройка ЮKassa
Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

# Примерный прайс-лист (чтобы бот знал цену продукта)
# Если продукта нет в списке, бот выставит счет на 1000р по умолчанию
PRODUCT_PRICES = {
    "натальная карта": 3000,
    "прогноз на год": 5000,
    "расклад таро": 2500,
    "карта дня": 500,
    # Добавьте сюда свои продукты и цены
}

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- МАШИНА СОСТОЯНИЙ (FSM) ---
class OrderForm(StatesGroup):
    service_type = State()       # Выбор: Астрология или Таро
    product_name = State()       # Ввод названия продукта
    
    # Ветка Астрологии
    astro_birth_date = State()
    astro_birth_time = State()
    astro_birth_city = State()
    astro_birth_country = State()
    
    # Ветка Таро
    taro_situation = State()

# --- КЛАВИАТУРЫ ---
def get_service_keyboard():
    kb = [
        [KeyboardButton(text="🔮 Астрология / Натальная карта")],
        [KeyboardButton(text="🃏 Таро / Гадание")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_keyboard():
    kb = [[KeyboardButton(text="❌ Отменить заказ")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ХЕНДЛЕРЫ (ОБРАБОТЧИКИ) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Добро пожаловать в @laboratorio_lampone! ✨\n\n"
        f"Я помогу оформить заказ. Выберите направление:",
        reply_markup=get_service_keyboard()
    )

@dp.message(F.text == "❌ Отменить заказ")
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Заказ отменен. Чтобы начать заново, нажмите /start", reply_markup=types.ReplyKeyboardRemove())

# 1. Выбор типа услуги
@dp.message(OrderForm.service_type)
async def process_service_type(message: types.Message, state: FSMContext):
    text = message.text
    if "Астрология" in text:
        await state.update_data(service="Астрология")
        await message.answer("Введите название продукта (например: Натальная карта, Соляр):", reply_markup=get_cancel_keyboard())
        await state.set_state(OrderForm.product_name)
    elif "Таро" in text:
        await state.update_data(service="Таро")
        await message.answer("Введите название продукта (например: Расклад на отношения):", reply_markup=get_cancel_keyboard())
        await state.set_state(OrderForm.product_name)
    else:
        await message.answer("Пожалуйста, выберите вариант из кнопок ниже:", reply_markup=get_service_keyboard())

# 2. Ввод названия продукта
@dp.message(OrderForm.product_name)
async def process_product_name(message: types.Message, state: FSMContext):
    await state.update_data(product=message.text)
    data = await state.get_data()
    
    if data['service'] == "Астрология":
        await message.answer("Введите дату рождения (ДД.ММ.ГГГГ):")
        await state.set_state(OrderForm.astro_birth_date)
    else:
        await message.answer("Введите дату рождения (ДД.ММ.ГГГГ) для уточнения энергий:")
        # Для Таро тоже часто нужна дата, но если строго по ТЗ, то переходим к описанию.
        # Я оставил дату для Таро как опциональную, но в ТЗ её нет, поэтому сразу к описанию:
        await message.answer("Опишите вашу ситуацию или вопрос:")
        await state.set_state(OrderForm.taro_situation)

# --- ВЕТКА АСТРОЛОГИИ ---

@dp.message(OrderForm.astro_birth_date)
async def process_astro_date(message: types.Message, state: FSMContext):
    # Тут можно добавить валидацию даты
    await state.update_data(birth_date=message.text)
    await message.answer("Введите точное время рождения (ЧЧ:ММ):")
    await state.set_state(OrderForm.astro_birth_time)

@dp.message(OrderForm.astro_birth_time)
async def process_astro_time(message: types.Message, state: FSMContext):
    await state.update_data(birth_time=message.text)
    await message.answer("Введите город рождения:")
    await state.set_state(OrderForm.astro_birth_city)

@dp.message(OrderForm.astro_birth_city)
async def process_astro_city(message: types.Message, state: FSMContext):
    await state.update_data(birth_city=message.text)
    await message.answer("Введите страну рождения:")
    await state.set_state(OrderForm.astro_birth_country)

@dp.message(OrderForm.astro_birth_country)
async def process_astro_country(message: types.Message, state: FSMContext):
    await state.update_data(birth_country=message.text)
    await finalize_order(message, state)

# --- ВЕТКА ТАРО ---

@dp.message(OrderForm.taro_situation)
async def process_taro_situation(message: types.Message, state: FSMContext):
    await state.update_data(situation=message.text)
    await finalize_order(message, state)

# --- ФИНАЛИЗАЦИЯ И ОПЛАТА ---

async def finalize_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Формируем текст заказа
    order_text = f"🆕 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
    order_text += f"👤 Клиент: @{message.from_user.username} ({message.from_user.first_name})\n"
    order_text += f"💎 Услуга: {data['service']}\n"
    order_text += f"📦 Продукт: {data['product']}\n"
    
    if data['service'] == "Астрология":
        order_text += f"📅 Дата рождения: {data['birth_date']}\n"
        order_text += f"⏰ Время: {data['birth_time']}\n"
        order_text += f"🌍 Место: {data['birth_city']}, {data['birth_country']}\n"
    else:
        order_text += f"📝 Ситуация: {data['situation']}\n"

    # Определение цены
    product_name_lower = data['product'].lower()
    price = 1000 # Цена по умолчанию
    found_price = False
    
    # Ищем цену в словаре (простой поиск по вхождению)
    for key, val in PRODUCT_PRICES.items():
        if key in product_name_lower:
            price = val
            found_price = True
            break
            
    if not found_price:
        order_text += f"⚠️ <b>Цена не найдена в базе, выставлена стандартная: {price} RUB</b>\n"
    else:
        order_text += f"💰 К оплате: {price} RUB\n"

    # Отправляем данные админу
    try:
        await bot.send_message(ADMIN_ID, order_text)
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение админу: {e}")

    # Создаем платеж в ЮKassa
    try:
        payment = Payment.create({
            "amount": {
                "value": str(price),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/laboratorio_lampone" # Куда вернется пользователь после оплаты
            },
            "capture": True,
            "description": f"Оплата заказа: {data['product']}"
        })
        
        # Отправляем ссылку пользователю
        if payment.confirmation.confirmation_url:
            await message.answer(
                f"✅ Данные приняты!\n\n"
                f"Для подтверждения заказа необходимо произвести оплату.\n"
                f"Сумма: <b>{price} RUB</b>\n\n"
                f"Нажмите кнопку ниже для оплаты:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Оплатить заказ", url=payment.confirmation.confirmation_url)]
                ])
            )
        else:
            await message.answer("Ошибка создания платежа. Пожалуйста, напишите администратору.")
            
    except Exception as e:
        logging.error(f"Ошибка ЮKassa: {e}")
        await message.answer("Произошла ошибка при создании счета. Пожалуйста, свяжитесь с поддержкой.")

    await state.clear()

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())