import platform
import socket
import psutil
import json
import csv
import datetime
import os
from typing import Dict, List

class SecurityAuditCollector:
    """
    Инструмент для сбора базовой информации о системе в целях аудита безопасности.
    Используется для инвентаризации активов и подготовки отчетов.
    
    ВАЖНО: Использовать только на системах, на которые есть разрешение!
    """

    def __init__(self):
        self.timestamp = datetime.datetime.now().isoformat()
        self.data = {
            "audit_timestamp": self.timestamp,
            "hostname": socket.gethostname(),
            "os_info": {},
            "network_info": [],
            "users_info": [],
            "processes_summary": {},
            "security_checks": []
        }

    def collect_os_info(self):
        """Сбор информации об ОС (версия, архитектура)"""
        self.data["os_info"] = {
            "system": platform.system(),
            "version": platform.version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }

    def collect_network_info(self):
        """Сбор информации о сетевых интерфейсах и адресах"""
        try:
            addrs = psutil.net_if_addrs()
            for interface_name, interface_addresses in addrs.items():
                for addr in interface_addresses:
                    if addr.family == socket.AF_INET:
                        self.data["network_info"].append({
                            "interface": interface_name,
                            "ip_address": addr.address,
                            "netmask": addr.netmask
                        })
        except Exception as e:
            self.data["network_info"].append({"error": str(e)})

    def collect_users_info(self):
        """Сбор информации о залогиненных пользователях"""
        try:
            users = psutil.users()
            for user in users:
                self.data["users_info"].append({
                    "name": user.name,
                    "terminal": user.terminal,
                    "host": user.host,
                    "started": user.started
                })
        except Exception as e:
            self.data["users_info"].append({"error": str(e)})

    def collect_processes_summary(self):
        """Сводка по процессам (без деталей, чтобы не перегружать)"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            self.data["processes_summary"] = {
                "total_count": len(processes),
                "unique_names": len(set(p['name'] for p in processes)),
                # Топ-5 самых частых процессов
                "top_processes": sorted(
                    {p['name'] for p in processes}, 
                    key=lambda x: sum(1 for p in processes if p['name'] == x), 
                    reverse=True
                )[:5]
            }
        except Exception as e:
            self.data["processes_summary"] = {"error": str(e)}

    def run_security_checks(self):
        """Базовые эвристические проверки (пример для портфолио)"""
        # Проверка 1: Запущен ли от имени администратора/root
        is_admin = False
        try:
            is_admin = os.getuid() == 0  # Linux/Mac
        except AttributeError:
            try:
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0  # Windows
            except Exception:
                pass
        
        self.data["security_checks"].append({
            "check": "Privilege Level",
            "status": "WARNING" if is_admin else "OK",
            "details": "Running as Admin/Root" if is_admin else "Running as User"
        })

        # Проверка 2: Количество сетевых интерфейсов
        iface_count = len(self.data["network_info"])
        self.data["security_checks"].append({
            "check": "Network Interfaces",
            "status": "INFO",
            "details": f"Active IPv4 interfaces: {iface_count}"
        })

    def save_to_json(self, filename: str = "audit_report.json"):
        """Сохранение отчета в JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        print(f"[+] Отчет сохранен в {filename}")

    def save_to_csv(self, filename: str = "audit_processes.csv"):
        """Сохранение списка процессов в CSV для BI"""
        # Для примера сохраняем только сводку, но можно расширить
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if processes:
                    writer = csv.DictWriter(f, fieldnames=processes[0].keys())
                    writer.writeheader()
                    writer.writerows(processes)
            print(f"[+] Данные процессов сохранены в {filename}")
        except Exception as e:
            print(f"[-] Ошибка сохранения CSV: {e}")

    def run_full_audit(self):
        """Запуск всех сборщиков"""
        print("[*] Запуск аудита системы...")
        self.collect_os_info()
        self.collect_network_info()
        self.collect_users_info()
        self.collect_processes_summary()
        self.run_security_checks()
        
        self.save_to_json()
        self.save_to_csv()
        print("[*] Аудит завершен.")

if __name__ == "__main__":
    # Требует установки библиотеки: pip install psutil
    try:
        auditor = SecurityAuditCollector()
        auditor.run_full_audit()
    except ImportError:
        print("[-] Ошибка: Не установлена библиотека psutil. Выполните: pip install psutil")