"""
StatementFlow — Модуль конфигурации
Загружает настройки из переменных окружения и .env файла
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Основные настройки приложения
    """
    
    # 🔐 Безопасность
    SECRET_KEY: str = "your_super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 🗄 База данных
    DATABASE_URL: str = "sqlite:///./statements.db"
    
    # 🤖 Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    
    # 🌐 Сервер
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # 📧 Email (опционально)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # 📊 Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # 📁 Пути
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMPLATES_DIR: str = os.path.join(BASE_DIR, "templates")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    """
    Настройки базы данных
    """
    
    DATABASE_URL: str = "sqlite:///./statements.db"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 1800
    
    class Config:
        env_file = ".env"
        env_prefix = "DB_"


class SecuritySettings(BaseSettings):
    """
    Настройки безопасности
    """
    
    SECRET_KEY: str = "your_super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        env_prefix = "SEC_"


@lru_cache()
def get_settings() -> Settings:
    """
    Возвращает кэшированный экземпляр настроек
    """
    return Settings()


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """
    Возвращает настройки базы данных
    """
    return DatabaseSettings()


@lru_cache()
def get_security_settings() -> SecuritySettings:
    """
    Возвращает настройки безопасности
    """
    return SecuritySettings()


# Глобальный экземпляр настроек
settings = get_settings()
db_settings = get_db_settings()
security_settings = get_security_settings()


def validate_settings() -> bool:
    """
    Проверяет корректность настроек
    Возвращает True если всё OK, иначе выбрасывает исключение
    """
    if len(settings.SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY должен быть не менее 32 символов!")
    
    if not settings.TELEGRAM_BOT_TOKEN:
        print("⚠️  WARNING: TELEGRAM_BOT_TOKEN не установлен. Бот не будет работать.")
    
    if settings.DEBUG:
        print("⚠️  WARNING: Режим DEBUG включён. Не используйте в продакшене!")
    
    return True


if __name__ == "__main__":
    # Тестирование конфигурации
    print("🔍 Проверка конфигурации StatementFlow...\n")
    
    try:
        validate_settings()
        print("✅ Все настройки корректны!\n")
        
        print("📋 Активные настройки:")
        print(f"   SECRET_KEY: {settings.SECRET_KEY[:10]}...{'*' * 22}")
        print(f"   ALGORITHM: {settings.ALGORITHM}")
        print(f"   ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        print(f"   DATABASE_URL: {settings.DATABASE_URL}")
        print(f"   TELEGRAM_BOT_TOKEN: {'Установлен' if settings.TELEGRAM_BOT_TOKEN else 'Не установлен'}")
        print(f"   HOST: {settings.HOST}")
        print(f"   PORT: {settings.PORT}")
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   LOG_LEVEL: {settings.LOG_LEVEL}")
        
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        exit(1)