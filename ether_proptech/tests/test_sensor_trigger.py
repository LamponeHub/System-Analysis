import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Импорты модулей системы
from src.integrations.smart_sensors import SmartSensorsIntegration, SensorDataPoint
from src.integrations.access_control import AccessControlSystem
from src.core.config import ENVIRONMENT_THRESHOLDS, ACCESS_CONTROL_CONFIG

class TestSensorTriggers:
    """
    Тестирование логики срабатывания триггеров среды.
    Проверяет, что система корректно реагирует на превышение порогов шума и загрязнения воздуха.
    """

    @pytest.fixture
    def sensors(self):
        return SmartSensorsIntegration()

    @pytest.fixture
    def access_system(self):
        return AccessControlSystem()

    def test_night_noise_violation_detection(self, sensors):
        """
        Сценарий: Ночное время (02:00), шум 45 дБА.
        Ожидание: Нарушение должно быть зафиксировано (Лимит ночи 30 дБА).
        """
        # Эмулируем показания датчика вручную для чистоты теста
        night_readings = {
            "zone_id": "apt_101",
            "timestamp": datetime.now().replace(hour=2, minute=0),
            "noise_db": 45.0,
            "pm25_mg_m3": 0.010,
            "co2_ppm": 600,
            "is_night_mode": True
        }

        violations = sensors.check_violations(night_readings)

        assert len(violations) > 0, "Нарушение тишины ночью не было зафиксировано!"
        assert any("NOISE_EXCEEDED" in v for v in violations), "Неверный тип нарушения."
        assert "30" in str(violations), "В отчете должен быть указан лимит (30 дБА)."

    def test_day_noise_allowed(self, sensors):
        """
        Сценарий: Дневное время (14:00), шум 38 дБА.
        Ожидание: Нарушений нет (Лимит дня 40 дБА).
        """
        day_readings = {
            "zone_id": "apt_102",
            "timestamp": datetime.now().replace(hour=14, minute=0),
            "noise_db": 38.0,
            "pm25_mg_m3": 0.010,
            "co2_ppm": 600,
            "is_night_mode": False
        }

        violations = sensors.check_violations(day_readings)
        
        assert len(violations) == 0, f"Ложное срабатывание днем при нормальном шуме. Нарушения: {violations}"

    def test_critical_noise_spike(self, sensors):
        """
        Сценарий: Критический скачок шума (>55 дБА) в любое время.
        Ожидание: Специфическое нарушение CRITICAL_NOISE_SPIKE.
        """
        spike_readings = {
            "zone_id": "apt_103",
            "timestamp": datetime.now(),
            "noise_db": 60.0, # Выше критического порога
            "pm25_mg_m3": 0.010,
            "co2_ppm": 600,
            "is_night_mode": False # Даже днем такой шум критичен
        }

        violations = sensors.check_violations(spike_readings)
        
        assert any("CRITICAL_NOISE_SPIKE" in v for v in violations), "Критический скачок шума не детектирован."

    def test_smoke_detection_trigger(self, sensors):
        """
        Сценарий: Появление дыма (PM2.5 выше нормы).
        Ожидание: Нарушение AIR_QUALITY_LOW.
        """
        smoke_readings = {
            "zone_id": "apt_104",
            "timestamp": datetime.now(),
            "noise_db": 30.0,
            "pm25_mg_m3": 0.020, # Выше лимита 0.015
            "co2_ppm": 600,
            "is_night_mode": False
        }

        violations = sensors.check_violations(smoke_readings)
        
        assert any("AIR_QUALITY_LOW" in v for v in violations), "Задымление не было зафиксировано."

class TestAccessControlIntegration:
    """
    Тестирование реакции системы доступа на нарушения.
    Проверяет цепочку: Нарушение -> Блокировка -> Проверка статуса.
    """

    @pytest.fixture
    def access_system(self):
        return AccessControlSystem()

    def test_auto_lock_on_violation(self, access_system):
        """
        Сценарий: Зафиксировано нарушение, система должна заблокировать гостевой доступ.
        """
        user_id = "guest_bad_behavior_001"
        reason = "NOISE_EXCEEDED: 55 дБА"

        # Имитация вызова блокировки системой при инциденте
        result = access_system.trigger_lock(user_id, reason, duration_minutes=60)

        assert result["status"] == "locked"
        assert result["violation_count"] == 1
        assert "until" in result
        
        # Проверка, что доступ действительно закрыт
        is_allowed = access_system.check_access(user_id)
        assert is_allowed is False, "Доступ должен быть заблокирован сразу после нарушения."

    def test_access_restored_after_time(self, access_system):
        """
        Сценарий: Время блокировки истекло.
        Ожидание: Доступ автоматически восстанавливается.
        """
        user_id = "guest_temp_block_002"
        
        # Блокируем на 1 минуту для теста
        access_system.trigger_lock(user_id, "TEST", duration_minutes=1)
        
        assert access_system.check_access(user_id) is False

        # Эмулируем passage времени (в реальном коде это ждет datetime.now())
        # В классе AccessControlSystem проверка идет по datetime.now(), 
        # поэтому нам нужно либо ждать, либо замокать время. 
        # Для простоты теста проверим логику снятия блокировки при повторном запросе ПОСЛЕ времени.
        # Но так как мы не можем ускорить время в этом тесте без mock, 
        # проверим внутреннее состояние замков (это допустимо в unit-тестах логики).
        
        # Принудительно меняем время разблокировки в прошлом (хак для теста)
        from datetime import datetime, timedelta
        access_system.active_locks[user_id] = datetime.now() - timedelta(minutes=5)

        # Теперь доступ должен открыться
        is_allowed = access_system.check_access(user_id)
        assert is_allowed is True, "Доступ не восстановился после истечения времени блокировки."
        assert user_id not in access_system.active_locks, "Запись о блокировке должна быть удалена."

    def test_permanent_block_on_recidivism(self, access_system):
        """
        Сценарий: Пользователь нарушает правила 3 раза.
        Ожидание: Логирование критического события (перманентный бан).
        """
        user_id = "recidivist_003"
        
        # 3 нарушения
        for i in range(3):
            access_system.trigger_lock(user_id, f"VIOLATION_{i}", duration_minutes=10)

        assert access_system.violation_counts[user_id] == 3
        # В реальном коде здесь был бы вызов метода увольнения/выселения
        # Проверяем, что счетчик достиг лимита
        assert access_system.violation_counts[user_id] >= ACCESS_CONTROL_CONFIG['MAX_VIOLATIONS_BEFORE_PERMANENT_BLOCK']

def test_full_integration_flow(sensors, access_system):
    """
    Интеграционный тест: От датчика до блокировки.
    1. Датчик фиксирует шум.
    2. Система определяет нарушение.
    3. Система блокирует доступ.
    """
    # 1. Данные с датчика (Ночь, громко)
    readings = {
        "zone_id": "apt_integration_test",
        "timestamp": datetime.now().replace(hour=3, minute=0),
        "noise_db": 50.0,
        "pm25_mg_m3": 0.010,
        "co2_ppm": 600,
        "is_night_mode": True
    }

    # 2. Проверка нарушений
    violations = sensors.check_violations(readings)
    assert len(violations) > 0, "Интеграционный тест провален: нарушение не найдено."

    # 3. Реакция (Блокировка условного нарушителя из этой квартиры)
    offender_id = "user_apt_integration_test"
    if violations:
        access_system.trigger_lock(offender_id, "; ".join(violations))

    # 4. Верификация результата
    assert access_system.check_access(offender_id) is False, "Блокировка не сработала в интеграционном тесте."
    
    print("✅ Полный цикл 'Датчик -> Блокировка' прошел успешно.")