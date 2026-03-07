import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, LOG_LEVEL

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8", mode="a")
    ]
)
logger = logging.getLogger(__name__)

# Импорт роутеров после настройки логов, чтобы избежать циклических зависимостей
from handlers import start, catalog, cart, payment, admin

async def on_startup(dp: Dispatcher):
    logger.info("✅ Бот запущен")
    try:
        await dp.bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔁 Webhook очищен (polling-режим)")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось очистить webhook: {e}")

async def on_shutdown(dp: Dispatcher):
    logger.info("🛑 Бот остановлен")
    await dp.bot.session.close()

def create_bot() -> Bot:
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    
    # Fallback-обработчик
    @dp.message()
    async def fallback(message: types.Message):
        await message.answer(
            "🧁 Чтобы сделать заказ, используйте меню:\n"
            "• Нажмите /start\n"
            "• Или выберите команду в меню клавиатуры"
        )
    
    return dp

async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан в .env!")
        return
    
    bot = create_bot()
    dp = create_dispatcher()
    
    logger.info("🚀 Запуск polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Прервано пользователем")
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка: {e}")