import logging
from datetime import datetime, timedelta
from src.core.config import ACCESS_CONTROL_CONFIG

logger = logging.getLogger("ether.access")

class AccessControlSystem:
    """
    Управление электронными замками и пропусками.
    Реализует автоматические санкции за нарушение среды.
    """
    
    def __init__(self):
        # В реальности здесь было бы подключение к СКУД (например, Sigur, Hikvision)
        self.active_locks = {} # { user_id: unlock_time }
        self.violation_counts = {} # { user_id: count }

    def trigger_lock(self, user_id: str, reason: str, duration_minutes: int = None):
        """
        Блокирует доступ для пользователя (гостя или резидента).
        """
        if duration_minutes is None:
            duration_minutes = ACCESS_CONTROL_CONFIG['AUTO_LOCK_DURATION_MINUTES']
            
        unlock_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        self.active_locks[user_id] = unlock_time
        self.violation_counts[user_id] = self.violation_counts.get(user_id, 0) + 1
        
        logger.warning(f"🔒 ДОСТУП ЗАБЛОКИРОВАН: User {user_id}. Причина: {reason}. До: {unlock_time}")
        
        # Проверка на рецидив
        if self.violation_counts[user_id] >= ACCESS_CONTROL_CONFIG['MAX_VIOLATIONS_BEFORE_PERMANENT_BLOCK']:
            logger.critical(f"⛔ ПЕРМАНЕНТНАЯ БЛОКИРОВКА: User {user_id} превысил лимит нарушений.")
            # Здесь логика вызова юриста или расторжения договора
            
        return {
            "status": "locked",
            "user_id": user_id,
            "until": unlock_time.isoformat(),
            "reason": reason,
            "violation_count": self.violation_counts[user_id]
        }

    def check_access(self, user_id: str) -> bool:
        """
        Проверяет, имеет ли пользователь право входа в данный момент.
        """
        if user_id in self.active_locks:
            if datetime.now() < self.active_locks[user_id]:
                return False # Доступ закрыт
            else:
                # Время вышло, снимаем блокировку
                del self.active_locks[user_id]
                logger.info(f"🔓 Доступ автоматически восстановлен для {user_id}")
                
        return True

    def grant_guest_pass(self, host_id: str, guest_id: str, valid_hours: int = 24):
        """
        Выдает временный пропуск гостю.
        """
        if not self.check_access(host_id):
            raise PermissionError(f"Хозяин {host_id} находится в состоянии блокировки. Гости запрещены.")
            
        logger.info(f"🎫 Пропуск выдан: Гость {guest_id} для хозяина {host_id}")
        return {"status": "granted", "valid_until": (datetime.now() + timedelta(hours=valid_hours)).isoformat()}