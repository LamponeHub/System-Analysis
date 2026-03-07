from typing import Dict, List
from .menu_data import MenuItem, get_item_by_id

class Cart:
    """Простая корзина в памяти. Для продакшена заменить на Redis/БД."""
    
    def __init__(self):
        self.items: Dict[str, int] = {}  # {item_id: quantity}
    
    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        item = get_item_by_id(item_id)
        if not item or not item.available:
            return False
        self.items[item_id] = self.items.get(item_id, 0) + quantity
        return True
    
    def remove_item(self, item_id: str) -> bool:
        return self.items.pop(item_id, None) is not None
    
    def update_quantity(self, item_id: str, quantity: int) -> bool:
        if quantity <= 0:
            return self.remove_item(item_id)
        if not get_item_by_id(item_id):
            return False
        self.items[item_id] = quantity
        return True
    
    def clear(self):
        self.items.clear()
    
    def get_total(self) -> int:
        """Сумма заказа в рублях"""
        return sum(
            (item.price * qty) 
            for item_id, qty in self.items.items() 
            if (item := get_item_by_id(item_id))
        )
    
    def get_summary(self) -> List[Dict]:
        """Детализация заказа для отображения и оплаты"""
        summary = []
        for item_id, qty in self.items.items():
            item = get_item_by_id(item_id)
            if item:
                summary.append({
                    "id": item.id,
                    "name": item.name,
                    "price": item.price,
                    "qty": qty,
                    "subtotal": item.price * qty
                })
        return summary
    
    def is_empty(self) -> bool:
        return not self.items
    
    def __len__(self) -> int:
        return sum(self.items.values())

# === Хранилище корзин (в памяти — для демо) ===
# ⚠️ В продакшене использовать Redis: aioredis, или БД: SQLAlchemy
_user_carts: Dict[int, Cart] = {}

def get_user_cart(user_id: int) -> Cart:
    if user_id not in _user_carts:
        _user_carts[user_id] = Cart()
    return _user_carts[user_id]

def cleanup_inactive_carts(max_age_hours: int = 24):
    """Очистка неактивных корзин (вызывать периодически)"""
    # В реальной реализации — по таймстампу последней активности
    pass