import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# === Telegram ===
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0"))

# === Платежи (ЮKassa — пример) ===
YOOKASSA_SHOP_ID: Optional[str] = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY: Optional[str] = os.getenv("YOOKASSA_SECRET_KEY")
PAYMENT_RETURN_URL: str = os.getenv("PAYMENT_RETURN_URL", "https://t.me/StruchokVaniliBot")
PAYMENT_CURRENCY: str = "RUB"

# === Доставка ===
DELIVERY_FEE: int = int(os.getenv("DELIVERY_FEE", "150"))  # ₽
FREE_DELIVERY_THRESHOLD: int = int(os.getenv("FREE_DELIVERY_THRESHOLD", "2000"))  # ₽
PICKUP_ADDRESS: str = os.getenv("PICKUP_ADDRESS", "Москва, ул. Примерная, д. 1")

# === База данных (опционально) ===
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")  # sqlite:///bot.db или postgresql://...
REDIS_URL: Optional[str] = os.getenv("REDIS_URL")  # redis://localhost:6379

# === Прочее ===
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()