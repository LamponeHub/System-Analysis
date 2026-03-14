import random
import time
from datetime import datetime
from src.core.config import ENVIRONMENT_THRESHOLDS

class SensorDataPoint:
    def __init__(self, sensor_id: str, type_: str, value: float, timestamp: datetime):
        self.sensor_id = sensor_id
        self.type = type_ # 'noise', 'pm25', 'co2'
        self.value = value
        self.timestamp = timestamp

class SmartSensorsIntegration:
    """
    Интеграция с физическим миром.
    В продакшене заменяет эмуляцию на реальные вызовы MQTT/API шлюза.
    """
    
    def __init__(self):
        self.thresholds = ENVIRONMENT_THRESHOLDS

    def get_current_readings(self, zone_id: str) -> dict:
        """
        Получает текущие показания для зоны.
        Возвращает словарь: {'noise': db, 'pm25': mg/m3, 'co2': ppm}
        """
        # --- ЭМУЛЯЦИЯ ДЛЯ ТЕСТА ---
        # В реальности: requests.get(f"http://iot-gateway/zones/{zone_id}")
        
        current_hour = datetime.now().hour
        is_night = current_hour >= self.thresholds['NOISE']['NIGHT_START_HOUR'] or \
                   current_hour < self.thresholds['NOISE']['DAY_START_HOUR']
        
        base_noise = 25 if is_night else 35
        
        # Симуляция случайного события нарушения (для демонстрации работы триггеров)
        if random.random() < 0.05: # 5% шанс нарушения
            base_noise += 25 
            
        return {
            "zone_id": zone_id,
            "timestamp": datetime.now(),
            "noise_db": base_noise + random.uniform(-2, 2),
            "pm25_mg_m3": 0.010 + random.uniform(0, 0.005),
            "co2_ppm": 600 + random.randint(0, 200),
            "is_night_mode": is_night
        }

    def check_violations(self, readings: dict) -> list[str]:
        """
        Сравнивает показания с порогами из config.py.
        Возвращает список активных нарушений.
        """
        violations = []
        
        # Проверка шума
        limit = (self.thresholds['NOISE']['NIGHT_LIMIT_DB'] 
                 if readings['is_night_mode'] 
                 else self.thresholds['NOISE']['DAY_LIMIT_DB'])
        
        if readings['noise_db'] > limit:
            violations.append(f"NOISE_EXCEEDED: {readings['noise_db']:.1f} дБА (Лимит: {limit})")
            
        if readings['noise_db'] > self.thresholds['NOISE']['CRITICAL_SPIKE_DB']:
            violations.append(f"CRITICAL_NOISE_SPIKE: {readings['noise_db']:.1f} дБА")

        # Проверка воздуха
        if readings['pm25_mg_m3'] > self.thresholds['AIR']['PM25_LIMIT_MG_M3']:
            violations.append(f"AIR_QUALITY_LOW: PM2.5 {readings['pm25_mg_m3']} мг/м³")
            
        return violations

# Пример использования (для отладки)
if __name__ == "__main__":
    sensors = SmartSensorsIntegration()
    data = sensors.get_current_readings("zone_apt_101")
    print(f"Данные: {data}")
    print(f"Нарушения: {sensors.check_violations(data)}")