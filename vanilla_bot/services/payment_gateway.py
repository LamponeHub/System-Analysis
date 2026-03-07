import aiohttp
import logging
from typing import Optional
from config import (
    YOOKASSA_SHOP_ID, 
    YOOKASSA_SECRET_KEY, 
    PAYMENT_RETURN_URL, 
    PAYMENT_CURRENCY
)

logger = logging.getLogger(__name__)

class PaymentGateway:
    """Интеграция с ЮKassa (пример). Легко адаптируется под другие системы."""
    
    YOOKASSA_API = "https://api.yookassa.ru/v3/payments"
    
    @classmethod
    async def create_payment(
        cls,
        order_id: str,
        amount: int,
        description: str,
        user_email: Optional[str] = None,
        save_payment_method: bool = False
    ) -> Optional[str]:
        """
        Создаёт платёж в ЮKassa.
        
        :param order_id: Уникальный идентификатор заказа в вашей системе
        :param amount: Сумма в рублях (целое число)
        :param description: Описание платежа
        :param user_email: Email покупателя (для фискализации)
        :param save_payment_method: Сохранять ли карту для будущих платежей
        :return: URL для оплаты или None при ошибке
        """
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            logger.warning("⚠️ Платёжные данные не настроены — возврат заглушки")
            return None  # или вернуть тестовый URL
        
        auth = aiohttp.BasicAuth(login=YOOKASSA_SHOP_ID, password=YOOKASSA_SECRET_KEY)
        
        payload = {
            "amount": {"value": f"{amount:.2f}", "currency": PAYMENT_CURRENCY},
            "confirmation": {
                "type": "redirect",
                "return_url": f"{PAYMENT_RETURN_URL}?order_id={order_id}"
            },
            "capture": True,  # сразу списывать, не холдировать
            "description": description,
            "metadata": {"order_id": order_id},
            "save_payment_method": save_payment_method
        }
        
        # Фискализация (54-ФЗ) — упростите под ваши нужды
        if user_email:
            payload["receipt"] = {
                "customer": {"email": user_email},
                "items": [{
                    "description": description,
                    "quantity": 1,
                    "amount": {"value": f"{amount:.2f}", "currency": PAYMENT_CURRENCY},
                    "vat_code": "2"  # НДС 20%
                }]
            }
        
        try:
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.post(cls.YOOKASSA_API, json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        confirmation_url = data.get("confirmation", {}).get("confirmation_url")
                        logger.info(f"✅ Платёж создан: {order_id} → {confirmation_url}")
                        return confirmation_url
                    else:
                        error_text = await resp.text()
                        logger.error(f"❌ Ошибка ЮKassa ({resp.status}): {error_text}")
                        return None
        except Exception as e:
            logger.exception(f"💥 Исключение при создании платежа: {e}")
            return None
    
    @classmethod
    async def verify_payment(cls, payment_id: str, order_id: str) -> bool:
        """Проверка статуса платежа (для вебхука)"""
        # Реализация зависит от требований безопасности
        # В продакшене: проверять подпись, сверять сумму и order_id
        return True  # заглушка