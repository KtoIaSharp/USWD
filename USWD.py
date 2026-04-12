#!/usr/bin/env python3
"""
Universal Steam Workshop Downloader by KtoIa v1.3
Скачивание коллекций модов через SteamCMD
"""

import subprocess
import sys
import os
import zipfile
import urllib.request
import shutil
import time
import threading
import re
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import json

# Цвета для терминала
class Colors:
    """Класс для управления цветами в консоли"""
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    current_color = CYAN
    
    @classmethod
    def set_color(cls, color_name):
        colors = {
            'красный': cls.RED,
            'зеленый': cls.GREEN,
            'желтый': cls.YELLOW,
            'синий': cls.BLUE,
            'фиолетовый': cls.MAGENTA,
            'голубой': cls.CYAN,
            'белый': cls.WHITE
        }
        if color_name.lower() in colors:
            cls.current_color = colors[color_name.lower()]
            return True
        return False
    
    @classmethod
    def colorize(cls, text, color=None):
        if color:
            return f"{color}{text}{cls.RESET}"
        return f"{cls.current_color}{text}{cls.RESET}"
    
    @classmethod
    def header(cls, text):
        return f"{cls.BOLD}{cls.current_color}{text}{cls.RESET}"
    
    @classmethod
    def success(cls, text):
        return f"{cls.BRIGHT_GREEN}{text}{cls.RESET}"
    
    @classmethod
    def error(cls, text):
        return f"{cls.BRIGHT_RED}{text}{cls.RESET}"
    
    @classmethod
    def warning(cls, text):
        return f"{cls.BRIGHT_YELLOW}{text}{cls.RESET}"
    
    @classmethod
    def info(cls, text):
        return f"{cls.BRIGHT_CYAN}{text}{cls.RESET}"


# Класс для управления очисткой консоли
class ConsoleManager:
    """Управление консолью (очистка, история)"""
    
    # Режим автоочистки (по умолчанию ВКЛЮЧЕН)
    auto_clear_enabled = True
    
    @classmethod
    def clear(cls):
        """Очищает консоль"""
        if cls.auto_clear_enabled:
            # Для Windows
            if sys.platform == "win32":
                os.system('cls')
            # Для Linux/Mac
            else:
                os.system('clear')
    
    @classmethod
    def set_auto_clear(cls, enabled: bool):
        """Включает/выключает автоочистку консоли"""
        cls.auto_clear_enabled = enabled
        # Сохраняем настройку
        settings_file = Path.cwd() / "console_settings.txt"
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(f"AUTO_CLEAR={enabled}")
    
    @classmethod
    def load_settings(cls):
        """Загружает настройки автоочистки"""
        settings_file = Path.cwd() / "console_settings.txt"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if "AUTO_CLEAR=True" in content:
                        cls.auto_clear_enabled = True
                    elif "AUTO_CLEAR=False" in content:
                        cls.auto_clear_enabled = False
            except:
                pass
    
    @classmethod
    def clear_and_show_header(cls, title: str, subtitle: str = None):
        """Очищает консоль и показывает красивый заголовок"""
        cls.clear()
        print("="*60)
        print(Colors.header(f"  {title}"))
        if subtitle:
            print(Colors.colorize(f"  {subtitle}"))
        print("="*60)


# Класс для логирования
class Logger:
    """Логирование в файл"""
    def __init__(self):
        self.log_dir = Path.cwd() / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.start_new_session()
        self.current_mod_ids = []
    
    def start_new_session(self):
        """Начинает новую сессию логирования"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = self.log_dir / f"download_{timestamp}.log"
        self.log(f"=== НОВАЯ СЕССИЯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    def log(self, message: str, level: str = "INFO"):
        """Записывает сообщение в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        
        try:
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + "\n")
        except:
            pass
    
    def info(self, message: str):
        self.log(message, "INFO")
    
    def error(self, message: str):
        self.log(message, "ERROR")
    
    def warning(self, message: str):
        self.log(message, "WARNING")
    
    def success(self, message: str):
        self.log(message, "SUCCESS")


# Класс для прогресс-бара
class ProgressBar:
    """Визуальный прогресс-бар"""
    def __init__(self, total: int, prefix: str = "", suffix: str = "", length: int = 50):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.current = 0
        self.start_time = None
        self.last_update_time = None
        self.last_current = 0
        self.lock = threading.Lock()
    
    def start(self):
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_current = 0
    
    def update(self, current: int = None, increment: int = None):
        with self.lock:
            if current is not None:
                self.current = min(current, self.total)
            elif increment is not None:
                self.current = min(self.current + increment, self.total)
            
            self._draw()
    
    def _draw(self):
        percent = self.current / self.total
        filled = int(self.length * percent)
        bar = '█' * filled + '░' * (self.length - filled)
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Оценка оставшегося времени
        eta_str = ""
        if self.current > 0 and elapsed > 0:
            speed = self.current / elapsed
            remaining_items = self.total - self.current
            eta_seconds = remaining_items / speed if speed > 0 else 0
            
            if eta_seconds < 60:
                eta_str = f" ~{eta_seconds:.0f} сек"
            elif eta_seconds < 3600:
                eta_str = f" ~{eta_seconds/60:.0f} мин"
            else:
                eta_str = f" ~{eta_seconds/3600:.1f} ч"
        
        # Время выполнения
        time_str = ""
        if elapsed < 60:
            time_str = f"{elapsed:.0f} сек"
        elif elapsed < 3600:
            time_str = f"{elapsed/60:.1f} мин"
        else:
            time_str = f"{elapsed/3600:.1f} ч"
        
        print(f'\r{self.prefix} |{Colors.colorize(bar)}| {percent*100:.1f}% {self.suffix} [{self.current}/{self.total}] ⏱ {time_str}{eta_str}', end='', flush=True)
    
    def finish(self):
        print()
        elapsed = time.time() - self.start_time if self.start_time else 0
        if elapsed < 60:
            print(Colors.success(f"✅ Завершено за {elapsed:.1f} сек"))
        elif elapsed < 3600:
            print(Colors.success(f"✅ Завершено за {elapsed/60:.1f} мин"))
        else:
            print(Colors.success(f"✅ Завершено за {elapsed/3600:.1f} ч"))


# Класс для управления режимом вывода
class OutputMode:
    """Управление режимом вывода (тихий/лог)"""
    SILENT = "silent"  # Показывать только прогресс
    NORMAL = "normal"  # Показывать всё
    DEBUG = "debug"    # Показывать всё + логи SteamCMD
    
    current_mode = NORMAL
    
    @classmethod
    def set_mode(cls, mode: str):
        if mode in [cls.SILENT, cls.NORMAL, cls.DEBUG]:
            cls.current_mode = mode
            return True
        return False
    
    @classmethod
    def should_show_detail(cls) -> bool:
        return cls.current_mode in [cls.NORMAL, cls.DEBUG]
    
    @classmethod
    def should_show_steam_output(cls) -> bool:
        return cls.current_mode == cls.DEBUG


# ID игр
GAMES = {
    "rimworld": {"name": "RimWorld", "app_id": "294100"},
}

STEAMCMD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"


class SteamWorkshopDownloader:
    def __init__(self):
        self.steamcmd_path = None
        self.game_name = "RimWorld"
        self.game_id = "294100"
        self.download_dir = None
        self.workshop_dir = None
        self.game_mods_path = None
        self.logger = Logger()
        self.download_start_time = None
        
        # Загружаем сохраненные настройки
        self.load_settings()
        self.load_output_mode()
        ConsoleManager.load_settings()

    def validate_mod_folder(self, mod_path: Path) -> bool:
        return any(mod_path.iterdir())
    
    def download_appid_list(self) -> Path:
        """Скачивает файл со списком App ID игр (основной + резервный источник)"""
        import requests

        # Источники (по приоритету)
        sources = [
            {
                "name": "jsnli/steamappidlist (ежедневно)",
                "urls": [
                    "https://raw.githubusercontent.com/jsnli/steamappidlist/master/data/games_appid.json",
                    "https://raw.githubusercontent.com/jsnli/steamappidlist/main/data/games_appid.json"
                ],
                "max_size_mb": 50
            },
            {
                "name": "dgibbs64/SteamCMD-AppID-List (архив 2023)",
                "urls": [
                    "https://raw.githubusercontent.com/dgibbs64/SteamCMD-AppID-List/master/steamcmd_appid.json"
                ],
                "max_size_mb": 20
            }
        ]

        cache_file = Path.cwd() / "steam_appid_list.json"
        info_file = Path.cwd() / "steam_appid_source.txt"

        # Проверяем, нужно ли обновлять (если файл старше 7 дней)
        need_update = True
        if cache_file.exists():
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age < 7 * 24 * 3600:  # 7 дней
                need_update = False
                source_info = "неизвестно"
                if info_file.exists():
                    try:
                        source_info = info_file.read_text(encoding='utf-8').strip()
                    except:
                        pass
                print(Colors.success(f"✅ Использую локальный список игр (от {datetime.fromtimestamp(cache_file.stat().st_mtime).strftime('%d.%m.%Y')}, источник: {source_info})"))

        if need_update:
            for i, source in enumerate(sources, 1):
                # Пробуем каждый URL из списка
                for url in source['urls']:
                    print(Colors.info(f"📡 Попытка: скачиваю список из {source['name']}..."))
                    try:
                        response = requests.get(url, timeout=120)
                        response.raise_for_status()

                        # Проверяем размер
                        content_size = len(response.content)
                        content_size_mb = content_size / (1024 * 1024)

                        if content_size_mb > source['max_size_mb']:
                            print(Colors.warning(f"⚠ Файл слишком большой ({content_size_mb:.1f} МБ), пропускаю"))
                            break  # Переходим к следующему источнику

                        with open(cache_file, 'wb') as f:
                            f.write(response.content)

                        # Сохраняем информацию об источнике
                        info_file.write_text(source['name'], encoding='utf-8')

                        print(Colors.success(f"✅ Список игр успешно загружен! ({content_size_mb:.1f} МБ)"))
                        return cache_file

                    except requests.exceptions.Timeout:
                        print(Colors.warning(f"⚠ Таймаут подключения"))
                        continue
                    except requests.exceptions.RequestException as e:
                        print(Colors.warning(f"⚠ Ошибка сети: {e}"))
                        continue
                    except Exception as e:
                        print(Colors.warning(f"⚠ Не удалось скачать: {e}"))
                        continue

            # Если все источники не сработали
            if cache_file.exists():
                print(Colors.warning("⚠ Не удалось скачать свежий список"))
                print(Colors.info("💡 Использую сохраненную копию"))
                return cache_file
            else:
                print(Colors.error("❌ Нет локальной копии. Поиск будет недоступен."))
                return None

        return cache_file

    def search_game_by_name(self, query: str) -> List[Tuple[str, str]]:
        """Ищет игру по названию в локальном JSON-файле (без API)"""
        import json

        if not query or len(query.strip()) < 2:
            print(Colors.error("❌ Введите хотя бы 2 символа для поиска"))
            return []

        query_lower = query.lower().strip()
        print(Colors.info(f"🔍 Поиск игры: '{query}'"))

        # Скачиваем или загружаем локальный файл
        cache_file = self.download_appid_list()
        if not cache_file or not cache_file.exists():
            print(Colors.error("❌ Нет списка игр для поиска"))
            return []

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Определяем формат файла
            # Формат 1: {"appid": "name"} или {"123": "Game Name"} (dgibbs64)
            # Формат 2: [{"appid": 123, "name": "Game Name"}] (список словарей)
            # Формат 3: {"apps": [{"appid": 123, "name": "Game Name"}]} (Steam API)

            results = []

            if isinstance(data, list):
                # Формат: список словарей [{"appid": 123, "name": "Game", ...}]
                for item in data:
                    if isinstance(item, dict):
                        app_id = str(item.get("appid", ""))
                        name = str(item.get("name", ""))
                        if not name or not app_id:
                            continue
                    else:
                        continue

                    name_lower = name.lower()

                    if name_lower == query_lower:
                        results.insert(0, (name, app_id))
                    elif name_lower.startswith(query_lower):
                        results.append((name, app_id))
                    elif query_lower in name_lower:
                        results.append((name, app_id))

            elif isinstance(data, dict):
                # Проверяем, есть ли ключ "apps" (формат Steam API)
                if "apps" in data:
                    apps_list = data["apps"]
                    if isinstance(apps_list, list):
                        for app in apps_list:
                            if isinstance(app, dict):
                                app_id = str(app.get("appid", app.get("appId", "")))
                                name = app.get("name", "")
                                if not name or not app_id:
                                    continue

                                name_lower = name.lower()
                                if name_lower == query_lower:
                                    results.insert(0, (name, app_id))
                                elif name_lower.startswith(query_lower):
                                    results.append((name, app_id))
                                elif query_lower in name_lower:
                                    results.append((name, app_id))
                else:
                    # Формат: {"appid": "name"} (dgibbs64)
                    for app_id, name in data.items():
                        # Пропускаем нестроковые значения
                        if not isinstance(name, str):
                            continue

                        name_lower = name.lower()

                        if name_lower == query_lower:
                            results.insert(0, (name, str(app_id)))
                        elif name_lower.startswith(query_lower):
                            results.append((name, str(app_id)))
                        elif query_lower in name_lower:
                            results.append((name, str(app_id)))

            # Убираем дубликаты
            seen = set()
            unique_results = []
            for name, app_id in results:
                if app_id not in seen:
                    seen.add(app_id)
                    unique_results.append((name, app_id))

            # Сортируем
            def sort_key(item):
                name, _ = item
                name_lower_item = name.lower()
                if name_lower_item == query_lower:
                    return (0, len(name))
                elif name_lower_item.startswith(query_lower):
                    return (1, len(name))
                else:
                    return (2, len(name))

            unique_results.sort(key=sort_key)
            unique_results = unique_results[:100]  # Увеличено до 100 для лучшего охвата

            if not unique_results:
                print(Colors.warning(f"⚠ По запросу '{query}' ничего не найдено"))
                print(Colors.info("💡 Советы:"))
                print("   1. Попробуйте ввести название на английском")
                print("   2. Используйте более короткий запрос")
                print("   3. Найдите App ID игры на steamdb.info и укажите вручную")
                print()
                manual = input("Ввести App ID вручную? (y/n): ").lower()
                if manual == 'y':
                    app_id = input("   App ID: ").strip()
                    if app_id and app_id.isdigit():
                        # Попробуем найти название через Steam API
                        print(Colors.info("🔍 Определяю название игры..."))
                        try:
                            import requests
                            resp = requests.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}", timeout=10)
                            data = resp.json()
                            if app_id in data and data[app_id].get("success"):
                                game_name = data[app_id]["data"].get("name", f"App {app_id}")
                                print(Colors.success(f"✅ Найдена игра: {game_name}"))
                                return [(game_name, app_id)]
                            else:
                                print(Colors.warning("⚠ Не удалось определить название, использую App ID"))
                                return [(f"App {app_id}", app_id)]
                        except:
                            return [(f"App {app_id}", app_id)]
                    else:
                        print(Colors.error("❌ Неверный App ID"))
                return []

            print(Colors.success(f"\n✅ Найдено игр: {len(unique_results)}"))
            return unique_results

        except json.JSONDecodeError as e:
            print(Colors.error(f"❌ Ошибка чтения файла со списком игр: {e}"))
            return []
        except Exception as e:
            print(Colors.error(f"❌ Ошибка при поиске: {e}"))
            return []


    def export_mods_list(self, mod_ids: List[str], file_path: Path = None):
        """Экспортирует список ID модов в файл"""
        if not file_path:
            file_path = Path(input("💾 Имя файла для экспорта (например, my_mods.txt): ").strip())
        file_path.write_text("\n".join(mod_ids), encoding='utf-8')
        print(Colors.success(f"✅ Экспортировано {len(mod_ids)} модов в {file_path}"))

    def import_mods_list(self, file_path: Path = None) -> List[str]:
        """Импортирует список ID модов из файла"""
        if not file_path:
            file_path = Path(input("📂 Файл для импорта: ").strip())
        if not file_path.exists():
            print(Colors.error("Файл не найден"))
            return []
        lines = file_path.read_text(encoding='utf-8').strip().splitlines()
        mod_ids = [l.strip() for l in lines if l.strip().isdigit()]
        print(Colors.success(f"✅ Импортировано {len(mod_ids)} модов"))
        return mod_ids

    def download_mods_list(self, mod_ids: List[str]):
        """Скачивает список модов по ID"""
        for mod_id in mod_ids:
            self.download_single_mod(mod_id)

    def batch_download(self, file_path: Path = None):
        """Загружает список URL или ID из текстового файла (построчно)"""
        if not file_path:
            path_input = input("📁 Путь к файлу со списком (построчно): ").strip()
            if not path_input:
                print(Colors.error("❌ Путь не указан"))
                return
            file_path = Path(path_input)
    
        if not file_path.exists():
            print(Colors.error(f"❌ Файл не найден: {file_path}"))
            input("Нажмите Enter...")
            return
    
        lines = file_path.read_text(encoding='utf-8').strip().splitlines()
        items = [l.strip() for l in lines if l.strip()]
    
        collection_urls = [i for i in items if "steamcommunity.com" in i or "workshop" in i]
        mod_ids = [i for i in items if i.isdigit()]
    
        print(Colors.info(f"\n📊 Найдено коллекций: {len(collection_urls)}, модов: {len(mod_ids)}"))
    
        for url in collection_urls:
            self.download_collection(url)
    
        for mod_id in mod_ids:
            self.download_single_mod(mod_id)
    
        print(Colors.success("\n✅ Пакетная загрузка завершена"))
        input("Нажмите Enter...")

    def load_output_mode(self):
        """Загружает сохраненный режим вывода"""
        mode_file = Path.cwd() / "output_mode.txt"
        if mode_file.exists():
            try:
                with open(mode_file, 'r', encoding='utf-8') as f:
                    mode = f.read().strip()
                    OutputMode.set_mode(mode)
            except:
                pass
    
    def save_output_mode(self):
        """Сохраняет режим вывода"""
        mode_file = Path.cwd() / "output_mode.txt"
        with open(mode_file, 'w', encoding='utf-8') as f:
            f.write(OutputMode.current_mode)
    
    def console_menu(self):
        """Меню настройки консоли (очистка истории)"""
        while True:
            ConsoleManager.clear_and_show_header("🖥 НАСТРОЙКА КОНСОЛИ")
            
            print(f"\n  Текущий режим автоочистки: ", end="")
            if ConsoleManager.auto_clear_enabled:
                print(Colors.success("✅ ВКЛЮЧЕНА"))
                print(Colors.info("     (консоль очищается при каждом переходе между меню)"))
            else:
                print(Colors.warning("❌ ВЫКЛЮЧЕНА"))
                print(Colors.info("     (история консоли сохраняется между меню)"))
            
            print("\n" + "-"*60)
            print("1. 🧹 Включить автоочистку консоли (рекомендуется)")
            print("2. 📜 Выключить автоочистку (сохранять историю)")
            print("3. 🔄 Очистить консоль сейчас")
            print("4. ↩️ Назад")
            print("="*60)
            
            choice = input("\nВыберите действие (1-4): ").strip()
            
            if choice == "1":
                ConsoleManager.set_auto_clear(True)
                ConsoleManager.clear_and_show_header("🖥 НАСТРОЙКА КОНСОЛИ")
                print(Colors.success("\n✅ Автоочистка консоли ВКЛЮЧЕНА!"))
                print(Colors.info("   Теперь при каждом переходе между меню консоль будет очищаться."))
                input("\nНажмите Enter для продолжения...")
            
            elif choice == "2":
                ConsoleManager.set_auto_clear(False)
                ConsoleManager.clear_and_show_header("🖥 НАСТРОЙКА КОНСОЛИ")
                print(Colors.warning("\n⚠ Автоочистка консоли ВЫКЛЮЧЕНА"))
                print(Colors.info("   История консоли будет сохраняться между меню."))
                input("\nНажмите Enter для продолжения...")
            
            elif choice == "3":
                ConsoleManager.clear()
                print("="*60)
                print(Colors.header("  🖥 НАСТРОЙКА КОНСОЛИ"))
                print("="*60)
                print(Colors.success("\n✅ Консоль очищена!"))
                input("\nНажмите Enter для продолжения...")
            
            elif choice == "4":
                break
            
            else:
                print(Colors.error("❌ Неверный выбор"))
                time.sleep(1)
    
    def output_mode_menu(self):
        """Меню выбора режима вывода"""
        while True:
            ConsoleManager.clear_and_show_header("🔇 НАСТРОЙКА ВЫВОДА")
            
            print(f"\n  Текущий режим: ", end="")
            if OutputMode.current_mode == OutputMode.SILENT:
                print(Colors.info("🔇 ТИХИЙ (только прогресс)"))
            elif OutputMode.current_mode == OutputMode.NORMAL:
                print(Colors.info("📝 НОРМАЛЬНЫЙ (показывать детали)"))
            else:
                print(Colors.info("🐛 DEBUG (полный вывод)"))
            
            print("\n" + "-"*60)
            print("1. 🔇 Тихий режим - только прогресс-бар и статистика")
            print("2. 📝 Нормальный режим - показывать детали скачивания")
            print("3. 🐛 Debug режим - полный вывод SteamCMD")
            print("4. ↩️ Назад")
            print("="*60)
            
            choice = input("\nВыберите режим (1-4): ").strip()
            
            if choice == "1":
                OutputMode.set_mode(OutputMode.SILENT)
                self.save_output_mode()
                ConsoleManager.clear_and_show_header("🔇 НАСТРОЙКА ВЫВОДА")
                print(Colors.success("\n✅ Установлен ТИХИЙ режим (только прогресс)"))
                self.logger.info("Режим вывода изменен на SILENT")
                input("\nНажмите Enter для продолжения...")
            elif choice == "2":
                OutputMode.set_mode(OutputMode.NORMAL)
                self.save_output_mode()
                ConsoleManager.clear_and_show_header("🔇 НАСТРОЙКА ВЫВОДА")
                print(Colors.success("\n✅ Установлен НОРМАЛЬНЫЙ режим"))
                self.logger.info("Режим вывода изменен на NORMAL")
                input("\nНажмите Enter для продолжения...")
            elif choice == "3":
                OutputMode.set_mode(OutputMode.DEBUG)
                self.save_output_mode()
                ConsoleManager.clear_and_show_header("🔇 НАСТРОЙКА ВЫВОДА")
                print(Colors.success("\n✅ Установлен DEBUG режим"))
                self.logger.info("Режим вывода изменен на DEBUG")
                input("\nНажмите Enter для продолжения...")
            elif choice == "4":
                break
            else:
                print(Colors.error("❌ Неверный выбор"))
                time.sleep(1)
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        settings_file = Path.cwd() / "downloader_settings.txt"
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("STEAMCMD_PATH="):
                            path = line.strip().split("=", 1)[1]
                            if path and Path(path).exists():
                                self.steamcmd_path = path
                        elif line.startswith("GAME_MODS_PATH="):
                            path = line.strip().split("=", 1)[1]
                            if path and Path(path).exists():
                                self.game_mods_path = path
                        elif line.startswith("GAME_ID="):
                            self.game_id = line.strip().split("=", 1)[1]
                        elif line.startswith("GAME_NAME="):
                            self.game_name = line.strip().split("=", 1)[1]
            except:
                pass
    
    def save_settings(self):
        """Сохраняет настройки"""
        settings_file = Path.cwd() / "downloader_settings.txt"
        with open(settings_file, 'w', encoding='utf-8') as f:
            if self.steamcmd_path:
                f.write(f"STEAMCMD_PATH={self.steamcmd_path}\n")
            if self.game_mods_path:
                f.write(f"GAME_MODS_PATH={self.game_mods_path}\n")
            f.write(f"GAME_ID={self.game_id}\n")
            f.write(f"GAME_NAME={self.game_name}\n")
    
    def select_game(self):
        """Меню выбора игры"""
        ConsoleManager.clear_and_show_header("🎮 ВЫБОР ИГРЫ")

        print("\n1. 🎮 RimWorld (по умолчанию)")
        print("2. 🎲 Своя игра (указать App ID вручную)")
        print("3. 🔍 Поиск игры по названию (обновляемая база, ~180 МБ)")
        print("="*60)

        choice = input("\nВыберите игру (1-3): ").strip()

        if choice == "1":
            self.game_name = "RimWorld"
            self.game_id = "294100"
            ConsoleManager.clear_and_show_header("🎮 ВЫБОР ИГРЫ")
            print(Colors.success(f"\n✅ Выбрана игра: {self.game_name} (App ID: {self.game_id})"))
            self.save_settings()
            self.logger.info(f"Выбрана игра: {self.game_name} (ID: {self.game_id})")
            input("\nНажмите Enter для продолжения...")
            return True

        elif choice == "2":
            print("\n📝 Введите данные для своей игры:")
            self.game_name = input("   Название игры: ").strip()
            if not self.game_name:
                self.game_name = "Custom Game"

            print(Colors.info("\n💡 Где найти App ID?"))
            print("   1. Откройте страницу игры в Steam (можно через VPN)")
            print("   2. Или найдите на сайте steamdb.info")
            print("   3. Или спросите в поисковике 'App ID [название игры]'")

            self.game_id = input("\n   App ID игры: ").strip()
            if not self.game_id:
                print(Colors.error("❌ App ID обязателен"))
                input("\nНажмите Enter для продолжения...")
                return False

            if not self.game_id.isdigit():
                print(Colors.warning("⚠ App ID должен состоять только из цифр"))
                confirm = input("Продолжить? (y/n): ").lower()
                if confirm != 'y':
                    return False

            ConsoleManager.clear_and_show_header("🎮 ВЫБОР ИГРЫ")
            print(Colors.success(f"\n✅ Выбрана игра: {self.game_name} (App ID: {self.game_id})"))
            self.save_settings()
            self.logger.info(f"Выбрана игра: {self.game_name} (ID: {self.game_id})")
            input("\nНажмите Enter для продолжения...")
            return True

        elif choice == "3":
            query = input("\n🔍 Введите название игры (на английском): ").strip()
            if not query:
                print(Colors.error("❌ Название не введено"))
                time.sleep(1)
                return False

            if len(query) < 2:
                print(Colors.error("❌ Введите хотя бы 2 символа"))
                time.sleep(1)
                return False

            results = self.search_game_by_name(query)

            if not results:
                input("\nНажмите Enter для продолжения...")
                return False

            print("\n📋 Результаты поиска:")
            print("-" * 60)

            for i, (name, app_id) in enumerate(results[:20], 1):
                display_name = name if len(name) <= 55 else name[:52] + "..."
                print(f"  {i:2}. {Colors.colorize(display_name)}")
                print(f"      🆔 App ID: {Colors.info(app_id)}")
                print()

            print("-" * 60)
            max_choice = min(20, len(results))
            pick = input(f"\nВыберите номер (1-{max_choice}) или Enter для отмены: ").strip()

            if pick.isdigit() and 1 <= int(pick) <= max_choice:
                self.game_name, self.game_id = results[int(pick)-1]
                ConsoleManager.clear_and_show_header("🎮 ВЫБОР ИГРЫ")
                print(Colors.success(f"\n✅ Выбрана игра: {self.game_name}"))
                print(Colors.info(f"   App ID: {self.game_id}"))
                self.save_settings()
                self.logger.info(f"Выбрана игра: {self.game_name} (ID: {self.game_id})")
            else:
                print(Colors.warning("❌ Выбор отменен"))

            input("\nНажмите Enter для продолжения...")
            return True

        else:
            print(Colors.error("❌ Неверный выбор"))
            time.sleep(1)
            return False
    
    def check_steamcmd(self) -> bool:
        """Проверяет наличие SteamCMD"""
        if self.steamcmd_path and Path(self.steamcmd_path).exists():
            return True
        return False
    
    def find_steamcmd_in_folder(self, folder_path: Path) -> Path:
        """Ищет steamcmd.exe в указанной папке и подпапках"""
        steamcmd_exe = folder_path / "steamcmd.exe"
        if steamcmd_exe.exists():
            return steamcmd_exe
        
        for root, dirs, files in os.walk(folder_path):
            depth = Path(root).relative_to(folder_path).parts
            if len(depth) > 3:
                continue
            if "steamcmd.exe" in files:
                return Path(root) / "steamcmd.exe"
        
        return None
    
    def steamcmd_menu(self):
        """Меню управления SteamCMD"""
        while True:
            ConsoleManager.clear_and_show_header("🔧 УПРАВЛЕНИЕ STEAMCMD")
            
            if self.check_steamcmd():
                print(Colors.success(f"\n✅ Текущий путь: {self.steamcmd_path}"))
                print(f"📁 Размер: {self.get_folder_size(Path(self.steamcmd_path).parent)}")
            else:
                print(Colors.error("\n❌ SteamCMD не установлен"))
            
            print("\n" + "-"*60)
            print("1. 📥 Установить SteamCMD (автоматически)")
            print("2. 📂 Указать папку с SteamCMD (поиск steamcmd.exe)")
            print("3. 🔄 Обновить SteamCMD")
            print("4. 🗑 Удалить SteamCMD")
            print("5. ℹ️ Проверить версию")
            print("6. ↩️ Назад в главное меню")
            print("="*60)
            
            choice = input("\nВыберите действие (1-6): ").strip()
            
            if choice == "1":
                self.install_steamcmd()
            elif choice == "2":
                self.set_steamcmd_folder()
            elif choice == "3":
                self.update_steamcmd()
            elif choice == "4":
                self.uninstall_steamcmd()
            elif choice == "5":
                self.check_steamcmd_version()
            elif choice == "6":
                break
            else:
                print(Colors.error("❌ Неверный выбор"))
                time.sleep(1)
    
    def set_steamcmd_folder(self):
        """Указывает папку с SteamCMD (автоматически ищет steamcmd.exe)"""
        ConsoleManager.clear_and_show_header("📂 УКАЗАНИЕ ПАПКИ STEAMCMD")
        
        print("\n📂 Укажите папку, где находится SteamCMD")
        print("   (программа автоматически найдет steamcmd.exe в этой папке)")
        print("   Примеры:")
        print("   - C:\\steamcmd")
        print("   - D:\\Programs\\SteamCMD")
        print("   - C:\\Users\\user\\Desktop\\SteamCmd")
        print("\n   Введите путь к папке: ", end="")
        folder_path = input().strip()
        
        if not folder_path:
            print(Colors.error("❌ Путь не указан"))
            input("\nНажмите Enter для продолжения...")
            return
        
        folder = Path(folder_path)
        if not folder.exists():
            print(Colors.error(f"❌ Папка не найдена: {folder_path}"))
            input("\nНажмите Enter для продолжения...")
            return
        
        steamcmd_exe = self.find_steamcmd_in_folder(folder)
        
        if steamcmd_exe:
            self.steamcmd_path = str(steamcmd_exe)
            self.save_settings()
            print(Colors.success(f"\n✅ Найден SteamCMD: {steamcmd_exe}"))
            print(f"📁 Размер папки: {self.get_folder_size(folder)}")
            self.logger.info(f"SteamCMD найден: {steamcmd_exe}")
        else:
            print(Colors.error(f"\n❌ Не найден steamcmd.exe в папке: {folder_path}"))
            print(Colors.info("💡 Убедитесь, что:"))
            print("   - В папке есть файл steamcmd.exe")
            print("   - Указана правильная папка")
            print("   - Или установите SteamCMD через пункт 1")
        
        input("\nНажмите Enter для продолжения...")
    
    def install_steamcmd(self, install_path: str = None) -> bool:
        """Скачивает и устанавливает SteamCMD"""
        ConsoleManager.clear_and_show_header("📥 УСТАНОВКА STEAMCMD")
        
        if not install_path:
            print("\n📁 Введите путь для установки SteamCMD")
            print("   (Enter для C:\\steamcmd): ", end="")
            install_path = input().strip()
            if not install_path:
                install_path = "C:\\steamcmd"
        
        install_path = Path(install_path)
        
        if (install_path / "steamcmd.exe").exists():
            print(Colors.warning(f"\n⚠ SteamCMD уже установлен в {install_path}"))
            overwrite = input("Переустановить? (y/n): ").lower()
            if overwrite != 'y':
                return False
        
        install_path.mkdir(parents=True, exist_ok=True)
        zip_path = install_path / "steamcmd.zip"
        
        print(Colors.info(f"\n📥 Скачивание SteamCMD..."))
        self.logger.info(f"Установка SteamCMD в {install_path}")
        
        try:
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 / total_size)
                    print(f"  Прогресс: {percent:.1f}%", end='\r')
            
            urllib.request.urlretrieve(STEAMCMD_URL, zip_path, report_progress)
            print(f"\n  Загрузка завершена!")
            
            print(Colors.info(f"\n📦 Распаковка..."))
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(install_path)
            
            zip_path.unlink()
            
            steamcmd_exe = install_path / "steamcmd.exe"
            if steamcmd_exe.exists():
                self.steamcmd_path = str(steamcmd_exe)
                self.save_settings()
                print(Colors.success(f"\n✅ SteamCMD успешно установлен в: {steamcmd_exe}"))
                
                print(Colors.info("\n🔄 Выполняю первичную настройку..."))
                subprocess.run([str(steamcmd_exe), "+quit"], 
                             capture_output=True, 
                             timeout=60)
                print(Colors.success("✅ Первичная настройка завершена!"))
                self.logger.success(f"SteamCMD установлен: {steamcmd_exe}")
                input("\nНажмите Enter для продолжения...")
                return True
            else:
                print(Colors.error(f"❌ Не найден steamcmd.exe после установки"))
                self.logger.error("SteamCMD не найден после установки")
                input("\nНажмите Enter для продолжения...")
                return False
                
        except Exception as e:
            print(Colors.error(f"❌ Ошибка при установке SteamCMD: {e}"))
            self.logger.error(f"Ошибка установки SteamCMD: {e}")
            input("\nНажмите Enter для продолжения...")
            return False
    
    def update_steamcmd(self):
        """Обновляет SteamCMD"""
        if not self.check_steamcmd():
            print(Colors.error("❌ SteamCMD не установлен. Сначала установите его."))
            input("\nНажмите Enter для продолжения...")
            return
        
        ConsoleManager.clear_and_show_header("🔄 ОБНОВЛЕНИЕ STEAMCMD")
        
        print(Colors.info("\n🔄 Обновление SteamCMD..."))
        self.logger.info("Обновление SteamCMD")
        
        try:
            result = subprocess.run(
                [self.steamcmd_path, "+quit"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print(Colors.success("✅ SteamCMD успешно обновлен!"))
                self.logger.success("SteamCMD обновлен")
            else:
                print(Colors.warning("⚠ Обновление завершилось с предупреждениями"))
                self.logger.warning("Обновление SteamCMD с предупреждениями")
        except Exception as e:
            print(Colors.error(f"❌ Ошибка при обновлении: {e}"))
            self.logger.error(f"Ошибка обновления SteamCMD: {e}")
        
        input("\nНажмите Enter для продолжения...")
    
    def uninstall_steamcmd(self):
        """Удаляет SteamCMD"""
        if not self.steamcmd_path:
            print(Colors.error("❌ Путь к SteamCMD не указан"))
            input("\nНажмите Enter для продолжения...")
            return
        
        ConsoleManager.clear_and_show_header("🗑 УДАЛЕНИЕ STEAMCMD")
        
        steamcmd_folder = Path(self.steamcmd_path).parent
        print(Colors.warning(f"\n⚠ ВНИМАНИЕ! Вы собираетесь удалить SteamCMD из папки:"))
        print(f"   {steamcmd_folder}")
        
        confirm = input("\nУдалить SteamCMD? (y/n): ").lower()
        if confirm != 'y':
            print(Colors.error("❌ Отменено"))
            input("\nНажмите Enter для продолжения...")
            return
        
        try:
            shutil.rmtree(steamcmd_folder)
            self.steamcmd_path = None
            self.save_settings()
            print(Colors.success(f"✅ SteamCMD удален из {steamcmd_folder}"))
            self.logger.info(f"SteamCMD удален из {steamcmd_folder}")
        except Exception as e:
            print(Colors.error(f"❌ Ошибка при удалении: {e}"))
            self.logger.error(f"Ошибка удаления SteamCMD: {e}")
        
        input("\nНажмите Enter для продолжения...")
    
    def check_steamcmd_version(self):
        """Проверяет версию SteamCMD"""
        if not self.check_steamcmd():
            print(Colors.error("❌ SteamCMD не установлен"))
            input("\nНажмите Enter для продолжения...")
            return
        
        ConsoleManager.clear_and_show_header("ℹ️ ВЕРСИЯ STEAMCMD")
        
        print(Colors.info("\n🔍 Проверка версии SteamCMD..."))
        try:
            result = subprocess.run(
                [self.steamcmd_path, "+version", "+quit"],
                capture_output=True,
                text=True,
                timeout=30
            )
            print(result.stdout)
            self.logger.info(f"Версия SteamCMD: {result.stdout[:200]}")
        except Exception as e:
            print(Colors.error(f"❌ Ошибка: {e}"))
        
        input("\nНажмите Enter для продолжения...")
    
    def get_folder_size(self, folder_path: Path) -> str:
        """Возвращает размер папки в человекочитаемом формате"""
        try:
            total_size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            elif total_size < 1024 * 1024 * 1024:
                return f"{total_size / (1024 * 1024):.1f} MB"
            else:
                return f"{total_size / (1024 * 1024 * 1024):.2f} GB"
        except:
            return "Неизвестно"
    
    def get_mod_ids_from_collection(self, collection_url: str) -> List[str]:
        """Получает список ID модов из коллекции Steam Workshop"""
        if OutputMode.should_show_detail():
            print(Colors.info(f"\n🔍 Анализ коллекции: {collection_url}"))
        self.logger.info(f"Анализ коллекции: {collection_url}")
        
        if "id=" in collection_url:
            collection_id = collection_url.split("id=")[1].split("&")[0]
        else:
            collection_id = collection_url.strip("/").split("/")[-1]
        
        if OutputMode.should_show_detail():
            print(f"📚 ID коллекции: {collection_id}")
        
        try:
            import requests
            from bs4 import BeautifulSoup
            import re
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
            }
            
            response = requests.get(collection_url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            mod_links = soup.find_all('a', href=re.compile(r'/sharedfiles/filedetails/\?id=\d+'))
            
            mod_ids = []
            for link in mod_links:
                match = re.search(r'id=(\d+)', link.get('href', ''))
                if match:
                    mod_id = match.group(1)
                    if mod_id not in mod_ids and mod_id != collection_id:
                        mod_ids.append(mod_id)
            
            mod_ids = list(dict.fromkeys(mod_ids))
            
            if not mod_ids:
                print(Colors.warning("⚠ Не удалось найти моды в коллекции"))
                self.logger.warning("Моды в коллекции не найдены")
                return []
            
            if OutputMode.should_show_detail():
                print(Colors.success(f"✅ Найдено модов: {len(mod_ids)}"))
            self.logger.info(f"Найдено модов в коллекции: {len(mod_ids)}")
            return mod_ids
            
        except Exception as e:
            print(Colors.error(f"❌ Ошибка: {e}"))
            self.logger.error(f"Ошибка парсинга коллекции: {e}")
            return []
    
    def download_single_mod(self, mod_id: str):
        """Скачивает один мод по ID"""
        if not self.check_steamcmd():
            print(Colors.error("\n❌ SteamCMD не установлен. Установите его в пункте 3 меню."))
            input("\nНажмите Enter для продолжения...")
            return
        
        ConsoleManager.clear_and_show_header(f"📥 СКАЧИВАНИЕ МОДА {mod_id}")
        
        self.download_dir = Path.cwd() / f"{self.game_name.lower().replace(' ', '_')}_mods"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.workshop_dir = self.download_dir / f"steamapps/workshop/content/{self.game_id}"
        
        if OutputMode.should_show_detail():
            print(Colors.info(f"\n📥 Скачивание мода {mod_id}..."))
        self.logger.info(f"Начало скачивания мода {mod_id}")
        
        script_path = self.download_dir / "download_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("@ShutdownOnFailedCommand 1\n")
            f.write("@NoPromptForPassword 1\n")
            f.write(f'force_install_dir "{self.download_dir}"\n')
            f.write("login anonymous\n")
            f.write(f"workshop_download_item {self.game_id} {mod_id}\n")
            f.write("quit\n")
        
        if OutputMode.should_show_detail():
            print(Colors.info(f"\n🚀 Запуск SteamCMD..."))
        
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                [self.steamcmd_path, "+runscript", str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            if OutputMode.should_show_steam_output():
                for line in process.stdout:
                    print(f"  {line.strip()}")
            else:
                # В тихом режиме просто ждем
                for _ in process.stdout:
                    pass
            
            process.wait()
            
            elapsed = time.time() - start_time
            
            if process.returncode == 0:
                if OutputMode.should_show_detail():
                    print(Colors.success(f"\n✅ Мод {mod_id} скачан за {elapsed:.1f} сек!"))
                else:
                    print(Colors.success(f"✅ Мод {mod_id} скачан за {elapsed:.1f} сек"))
                print(f"📁 Мод скачан в: {self.workshop_dir}")
                self.logger.success(f"Мод {mod_id} скачан за {elapsed:.1f} сек")
                
                install = input("\n💿 Установить мод в игру сейчас? (y/n): ").lower()
                if install == 'y':
                    self.install_mods_to_game()
            else:
                print(Colors.error(f"\n❌ Ошибка скачивания мода {mod_id} (код: {process.returncode})"))
                self.logger.error(f"Ошибка скачивания мода {mod_id}: код {process.returncode}")
                input("\nНажмите Enter для продолжения...")
                
        except Exception as e:
            print(Colors.error(f"❌ Ошибка: {e}"))
            self.logger.error(f"Ошибка скачивания мода {mod_id}: {e}")
            input("\nНажмите Enter для продолжения...")
    
    def download_collection(self, collection_url: str):
        """Скачивает коллекцию модов с прогресс-баром и статистикой"""
        if not self.check_steamcmd():
            print(Colors.error("\n❌ SteamCMD не установлен. Установите его в пункте 3 меню."))
            input("\nНажмите Enter для продолжения...")
            return
        
        ConsoleManager.clear_and_show_header("📥 СКАЧИВАНИЕ КОЛЛЕКЦИИ")
        
        self.download_start_time = time.time()
        self.logger.info(f"=== НАЧАЛО СКАЧИВАНИЯ КОЛЛЕКЦИИ ===")
        self.logger.info(f"URL: {collection_url}")
        
        self.download_dir = Path.cwd() / f"{self.game_name.lower().replace(' ', '_')}_mods"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.workshop_dir = self.download_dir / f"steamapps/workshop/content/{self.game_id}"
        
        print(Colors.info(f"\n🔍 Анализ коллекции: {collection_url}"))
        mod_ids = self.get_mod_ids_from_collection(collection_url)
        
        
        if not mod_ids:
            print(Colors.warning("\n⚠ Не удалось получить список модов"))
            input("\nНажмите Enter для продолжения...")
            return
        
        total_mods = len(mod_ids)
        
        print(f"\n📋 Найдено модов: {total_mods}")
        if OutputMode.should_show_detail() and total_mods <= 20:
            for i, mod_id in enumerate(mod_ids[:20], 1):
                print(f"  {i}. {mod_id}")
        elif total_mods > 20:
            print(f"  ... и еще {total_mods - 20} модов")
        
        response = input(f"\n💾 Скачать {total_mods} модов? (y/n): ").lower()
        if response != 'y':
            print(Colors.error("❌ Отменено"))
            self.logger.info("Скачивание отменено пользователем")
            input("\nНажмите Enter для продолжения...")
            return
        
        # Создаем скрипт
        script_path = self.download_dir / "download_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("@ShutdownOnFailedCommand 1\n")
            f.write("@NoPromptForPassword 1\n")
            f.write(f'force_install_dir "{self.download_dir}"\n')
            f.write("login anonymous\n")
            for mod_id in mod_ids:
                f.write(f"workshop_download_item {self.game_id} {mod_id}\n")
            f.write("quit\n")
        
        print(Colors.info(f"\n🚀 Запуск SteamCMD..."))
        print(Colors.info(f"📊 Режим вывода: ", end=""))
        if OutputMode.current_mode == OutputMode.SILENT:
            print(Colors.info("ТИХИЙ (только статистика)"))
        elif OutputMode.current_mode == OutputMode.NORMAL:
            print(Colors.info("НОРМАЛЬНЫЙ"))
        else:
            print(Colors.info("DEBUG"))
        
        print("="*60)
        
        # Прогресс-бар
        progress = ProgressBar(total_mods, prefix="📥 Скачивание", suffix="модов")
        progress.start()
        
        # Счетчик успешных/неудачных загрузок
        successful = 0
        failed = 0
        failed_mods = []
        
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                [self.steamcmd_path, "+runscript", str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            # Мониторинг прогресса
            current_mod_index = 0
            
            for line in process.stdout:
                line_stripped = line.strip()
                
                # Парсим прогресс
                if "Downloading item" in line_stripped:
                    current_mod_index += 1
                    progress.update(current=current_mod_index)
                
                # Отслеживаем успешные/неудачные загрузки
                if "Success. Downloaded item" in line_stripped:
                    successful += 1
                    self.logger.info(f"Мод успешно скачан: {line_stripped[:100]}")
                elif "ERROR!" in line_stripped and "Download item" in line_stripped:
                    failed += 1
                    # Извлекаем ID мода
                    match = re.search(r'item (\d+)', line_stripped)
                    if match:
                        failed_mods.append(match.group(1))
                    self.logger.warning(f"Ошибка скачивания: {line_stripped[:100]}")
                
                # Вывод в режиме DEBUG
                if OutputMode.should_show_steam_output() and line_stripped:
                    if not any(keyword in line_stripped for keyword in ["Downloading item", "Success.", "ERROR!"]):
                        print(f"  {line_stripped}")
            
            process.wait()
            
            elapsed = time.time() - start_time
            
            # Завершаем прогресс-бар
            progress.finish()
            
            # Выводим итоговую статистику
            print("\n" + "="*60)
            print(Colors.header("  📊 СТАТИСТИКА СКАЧИВАНИЯ"))
            print("="*60)
            print(f"✅ Успешно скачано: {Colors.success(str(successful))} модов")
            print(f"❌ Ошибок: {Colors.error(str(failed))} модов")
            print(f"📁 Всего модов в коллекции: {total_mods}")
            
            # Время выполнения
            if elapsed < 60:
                time_str = f"{elapsed:.1f} сек"
            elif elapsed < 3600:
                time_str = f"{elapsed/60:.1f} мин"
            else:
                time_str = f"{elapsed/3600:.1f} ч"
            print(f"⏱ Время выполнения: {time_str}")
            
            # Средняя скорость
            if elapsed > 0:
                avg_speed = total_mods / elapsed
                print(f"📈 Средняя скорость: {avg_speed:.2f} модов/сек")
            
            if failed_mods:
                print(f"\n{Colors.warning('⚠ Неудачные моды:')}")
                for mod_id in failed_mods[:10]:
                    print(f"  - {mod_id}")
                if len(failed_mods) > 10:
                    print(f"  ... и еще {len(failed_mods)-10}")
            
            print("="*60)
            
            self.logger.info(f"Скачивание завершено. Успешно: {successful}, Ошибок: {failed}")
            self.logger.info(f"Общее время: {time_str}")
            
            if process.returncode == 0 or successful > 0:
                print(Colors.success("\n✅ Процесс скачивания завершен!"))
                print(f"📁 Моды скачаны в: {self.workshop_dir}")
                
                downloaded = list(self.workshop_dir.iterdir()) if self.workshop_dir.exists() else []
                print(f"📊 Скачано папок: {len(downloaded)} из {total_mods}")
                
                install = input("\n💿 Установить скачанные моды в игру сейчас? (y/n): ").lower()
                if install == 'y':
                    self.install_mods_to_game()
            else:
                print(Colors.error(f"\n❌ SteamCMD завершился с ошибкой (код: {process.returncode})"))
                self.logger.error(f"SteamCMD завершился с ошибкой: {process.returncode}")
                input("\nНажмите Enter для продолжения...")
                
        except Exception as e:
            print(Colors.error(f"❌ Ошибка: {e}"))
            self.logger.error(f"Ошибка скачивания: {e}")
            input("\nНажмите Enter для продолжения...")
    
    def download_menu(self):
        """Меню выбора типа скачивания"""
        while True:
            ConsoleManager.clear_and_show_header("📥 ВЫБОР ТИПА СКАЧИВАНИЯ")
            
            print("\n1. 📦 Скачать коллекцию модов (несколько модов по URL)")
            print("2. 🔧 Скачать один мод (по ID)")
            print("3. 📚 Пакетная загрузка (несколько коллекций/ID из файла)")
            print("4. ↩️ Назад в главное меню")
            print("="*60)
            
            choice = input("\nВыберите действие (1-4): ").strip()
            
            if choice == "1":
                ConsoleManager.clear_and_show_header("📥 СКАЧИВАНИЕ КОЛЛЕКЦИИ")
                collection_url = input("\n🔗 Введите URL коллекции Steam Workshop: ").strip()
                if collection_url:
                    self.download_collection(collection_url)
                else:
                    print(Colors.error("❌ URL не указан"))
                    time.sleep(1)
            
            elif choice == "2":
                ConsoleManager.clear_and_show_header("🔧 СКАЧИВАНИЕ ОДНОГО МОДА")
                mod_id = input("\n🔢 Введите ID мода: ").strip()
                if mod_id and mod_id.isdigit():
                    self.download_single_mod(mod_id)
                else:
                    print(Colors.error("❌ Введите корректный ID мода (только цифры)"))
                    time.sleep(1)

            elif choice == "3":
                self.batch_download()        
            
            elif choice == "4":
                break
            
            else:
                print(Colors.error("❌ Неверный выбор"))
                time.sleep(1)
    
    def install_mods_to_game(self):
        """Устанавливает скачанные моды в игру"""
        if not self.workshop_dir or not self.workshop_dir.exists():
            print(Colors.error("❌ Нет скачанных модов. Сначала скачайте коллекцию."))
            input("\nНажмите Enter для продолжения...")
            return
        
        ConsoleManager.clear_and_show_header("📁 УСТАНОВКА МОДОВ В ИГРУ")
        
        if self.game_mods_path:
            print(f"\nСохраненный путь: {self.game_mods_path}")
            use_saved = input("Использовать сохраненный путь? (y/n): ").lower()
            if use_saved == 'y':
                game_mods_path = Path(self.game_mods_path)
            else:
                game_mods_path = None
        else:
            game_mods_path = None
        
        if not game_mods_path:
            print(f"\n📂 Введите полный путь к папке Mods игры {self.game_name}")
            print("   Примеры:")
            print("   - C:\\Program Files (x86)\\Steam\\steamapps\\common\\Игра\\Mods")
            print("   - D:\\Games\\Игра\\Mods")
            print("\n   Введите путь: ", end="")
            path = input().strip()
            
            if not path:
                print(Colors.error("❌ Путь не указан"))
                input("\nНажмите Enter для продолжения...")
                return
            
            game_mods_path = Path(path)
        
        if not game_mods_path.exists():
            print(Colors.warning(f"❌ Папка не найдена: {game_mods_path}"))
            create = input("Создать папку? (y/n): ").lower()
            if create == 'y':
                game_mods_path.mkdir(parents=True, exist_ok=True)
                print(Colors.success(f"✅ Папка создана: {game_mods_path}"))
            else:
                input("\nНажмите Enter для продолжения...")
                return
        
        self.game_mods_path = str(game_mods_path)
        self.save_settings()
        
        downloaded_mods = list(self.workshop_dir.iterdir())
        if not downloaded_mods:
            print(Colors.error("❌ Нет скачанных модов"))
            input("\nНажмите Enter для продолжения...")
            return
        
        print(f"\n📦 Найдено модов для установки: {len(downloaded_mods)}")
        
        start_time = time.time()
        copied = 0
        skipped = 0
        
        # Прогресс-бар для установки
        progress = ProgressBar(len(downloaded_mods), prefix="📦 Установка", suffix="модов")
        progress.start()
        
        for i, mod_path in enumerate(downloaded_mods):
            dest_path = game_mods_path / mod_path.name
            
            if dest_path.exists():
                skipped += 1
                progress.update(current=i+1)
                continue
            
            try:
                shutil.copytree(mod_path, dest_path)
                copied += 1
                self.logger.info(f"Установлен мод: {mod_path.name}")
            except Exception as e:
                print(Colors.error(f"\n  ❌ Ошибка: {e}"))
                self.logger.error(f"Ошибка установки {mod_path.name}: {e}")
            
            progress.update(current=i+1)
        
        progress.finish()
        
        elapsed = time.time() - start_time
        if elapsed < 60:
            time_str = f"{elapsed:.1f} сек"
        elif elapsed < 3600:
            time_str = f"{elapsed/60:.1f} мин"
        else:
            time_str = f"{elapsed/3600:.1f} ч"
        
        print("\n" + "="*60)
        print(Colors.success(f"✅ Установка завершена!"))
        print(f"📊 Скопировано новых модов: {copied}")
        print(f"⏭ Пропущено (уже были): {skipped}")
        print(f"⏱ Время установки: {time_str}")
        print("="*60)
        
        self.logger.info(f"Установка завершена. Скопировано: {copied}, Пропущено: {skipped}, Время: {time_str}")
        
        input("\nНажмите Enter для продолжения...")


def color_settings_menu():
    """Меню выбора цвета"""
    ConsoleManager.clear_and_show_header("🎨 ВЫБОР ЦВЕТА ИНТЕРФЕЙСА")
    
    print("\nДоступные цвета:")
    print("1. 🔴 Красный")
    print("2. 🟢 Зеленый")
    print("3. 🟡 Желтый")
    print("4. 🔵 Синий")
    print("5. 🟣 Фиолетовый")
    print("6. 🔷 Голубой (по умолчанию)")
    print("7. ⚪ Белый")
    print("="*60)
    
    choice = input("\nВыберите цвет (1-7): ").strip()
    
    color_map = {
        "1": "красный",
        "2": "зеленый",
        "3": "желтый",
        "4": "синий",
        "5": "фиолетовый",
        "6": "голубой",
        "7": "белый"
    }
    
    if choice in color_map:
        Colors.set_color(color_map[choice])
        ConsoleManager.clear_and_show_header("🎨 ВЫБОР ЦВЕТА ИНТЕРФЕЙСА")
        print(Colors.success(f"\n✅ Цвет изменен на {color_map[choice]}"))
        input("\nНажмите Enter для продолжения...")
        return True
    else:
        print(Colors.error("❌ Неверный выбор"))
        time.sleep(1)
        return False


def install_libraries():
    """Установка необходимых библиотек"""
    ConsoleManager.clear_and_show_header("📦 УСТАНОВКА БИБЛИОТЕК")
    
    libraries = ["requests", "beautifulsoup4"]
    
    print(Colors.info("\nБудут установлены следующие библиотеки:"))
    for lib in libraries:
        print(f"  - {lib}")
    
    print("\n" + Colors.warning("⚠ ВНИМАНИЕ!"))
    print("Установка библиотек требует подключения к интернету")
    print("Возможно потребуется запуск от имени администратора")
    
    confirm = input("\nПродолжить установку? (y/n): ").lower()
    if confirm != 'y':
        print(Colors.error("❌ Установка отменена"))
        input("\nНажмите Enter для продолжения...")
        return False
    
    print(Colors.info("\n📥 Начинаю установку библиотек..."))
    
    for lib in libraries:
        print(f"\n🔄 Установка {lib}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", lib],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print(Colors.success(f"✅ {lib} успешно установлен!"))
            else:
                print(Colors.error(f"❌ Ошибка при установке {lib}"))
                print(result.stderr)
                input("\nНажмите Enter для продолжения...")
                return False
        except Exception as e:
            print(Colors.error(f"❌ Ошибка: {e}"))
            input("\nНажмите Enter для продолжения...")
            return False
    
    ConsoleManager.clear_and_show_header("📦 УСТАНОВКА БИБЛИОТЕК")
    print(Colors.success("\n✅ ВСЕ БИБЛИОТЕКИ УСПЕШНО УСТАНОВЛЕНЫ!"))
    print(Colors.info("\n💡 Теперь можно использовать все функции программы"))
    input("\nНажмите Enter для продолжения...")
    return True


def check_libraries():
    """Проверяет установлены ли библиотеки"""
    try:
        import requests
        import bs4
        return True
    except ImportError:
        return False


def main():
    """Главное меню программы"""
    # Загружаем сохраненный цвет
    color_file = Path.cwd() / "color_settings.txt"
    if color_file.exists():
        try:
            with open(color_file, 'r', encoding='utf-8') as f:
                color = f.read().strip()
                Colors.set_color(color)
        except:
            pass
    
    # Загружаем настройки консоли
    ConsoleManager.load_settings()
    
    downloader = SteamWorkshopDownloader()
    
    while True:
        # Очищаем консоль перед показом главного меню (если включено)
        if ConsoleManager.auto_clear_enabled:
            ConsoleManager.clear()
        
        libs_installed = check_libraries()
        
        print("="*60)
        print(Colors.header("  UNIVERSAL STEAM WORKSHOP DOWNLOADER v1.3"))
        print(Colors.colorize("  Скачивание коллекций модов через SteamCMD"))
        print(Colors.colorize(f"  {Colors.BRIGHT_MAGENTA}by KtoIa{Colors.RESET}"))
        print("="*60)
        print(Colors.header("\n  ГЛАВНОЕ МЕНЮ"))
        print("="*60)
        print("1. 📥 Скачать моды (коллекция или один мод)")
        print("2. 🎲 Выбрать игру")
        print("3. 🔧 Управление SteamCMD")
        print("4. 📁 Указать путь к папке Mods игры")
        print("5. 🎨 Настройка цвета интерфейса")
        print("6. 🔇 Настройка режима вывода (тихий/лог)")
        print("7. 🖥 Настройка консоли (очистка истории)")
        print("8. 📦 Установить библиотеки (requests, beautifulsoup4)")
        print("9. 📤 Экспорт/импорт списка модов")
        print("0. 🚪 Выход")
        print("="*60)
        
        # Статусы
        if libs_installed:
            print(Colors.success(f"\n📚 Библиотеки: ✅ установлены"))
        else:
            print(Colors.error(f"📚 Библиотеки: ❌ не установлены"))
        
        print(f"🔇 Режим вывода: ", end="")
        if OutputMode.current_mode == OutputMode.SILENT:
            print(Colors.info("🔇 ТИХИЙ"))
        elif OutputMode.current_mode == OutputMode.NORMAL:
            print(Colors.info("📝 НОРМАЛЬНЫЙ"))
        else:
            print(Colors.info("🐛 DEBUG"))
        
        print(f"🖥 Автоочистка консоли: ", end="")
        if ConsoleManager.auto_clear_enabled:
            print(Colors.success("✅ ВКЛ"))
        else:
            print(Colors.warning("❌ ВЫКЛ"))
        
        print(f"\n🎮 Текущая игра: {Colors.colorize(downloader.game_name)} (App ID: {downloader.game_id})")
        
        if downloader.game_mods_path:
            print(f"📂 Папка Mods: {Colors.colorize(downloader.game_mods_path)}")
        else:
            print(f"📂 Папка Mods: {Colors.warning('не указана')}")
        
        if downloader.check_steamcmd():
            print(f"🔧 SteamCMD: {Colors.success('✅ установлен')}")
        else:
            print(f"🔧 SteamCMD: {Colors.error('❌ не установлен')}")
        
        choice = input("\nВыберите действие (0-9, 0 для выхода): ").strip()
        
        if choice == "1":
            if not downloader.check_steamcmd():
                print(Colors.warning("\n⚠ SteamCMD не установлен!"))
                print("Сначала установите SteamCMD в пункте 3 меню.")
                time.sleep(2)
                continue
            
            if not libs_installed:
                print(Colors.warning("\n⚠ Для скачивания коллекций необходимы библиотеки!"))
                print("Выберите пункт 8 для установки библиотек")
                time.sleep(2)
                continue
            
            downloader.download_menu()
        
        elif choice == "2":
            downloader.select_game()
        
        elif choice == "3":
            downloader.steamcmd_menu()
        
        elif choice == "4":
            ConsoleManager.clear_and_show_header("📁 УКАЗАНИЕ ПУТИ К ПАПКЕ MODS")
            
            if downloader.game_mods_path:
                print(f"\nТекущий путь: {downloader.game_mods_path}")
                change = input("Изменить путь? (y/n): ").lower()
                if change != 'y':
                    continue
            
            print(f"\n📂 Введите полный путь к папке Mods игры {downloader.game_name}")
            print("   Примеры:")
            print("   - C:\\Program Files (x86)\\Steam\\steamapps\\common\\Игра\\Mods")
            print("   - D:\\Games\\Игра\\Mods")
            print("\n   Введите путь: ", end="")
            path = input().strip()
            
            if path:
                path_obj = Path(path)
                if path_obj.exists() or path_obj.parent.exists():
                    downloader.game_mods_path = str(path_obj)
                    downloader.save_settings()
                    print(Colors.success(f"✅ Путь сохранен: {path_obj}"))
                else:
                    print(Colors.warning(f"⚠ Путь не существует, но сохранен. Создайте папку позже."))
                    downloader.game_mods_path = str(path_obj)
                    downloader.save_settings()
            else:
                print(Colors.error("❌ Путь не указан"))
            
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "5":
            if color_settings_menu():
                with open(color_file, 'w', encoding='utf-8') as f:
                    for name, code in [("красный", Colors.RED), ("зеленый", Colors.GREEN), 
                                       ("желтый", Colors.YELLOW), ("синий", Colors.BLUE),
                                       ("фиолетовый", Colors.MAGENTA), ("голубой", Colors.CYAN),
                                       ("белый", Colors.WHITE)]:
                        if Colors.current_color == code:
                            f.write(name)
                            break
        
        elif choice == "6":
            downloader.output_mode_menu()
        
        elif choice == "7":
            downloader.console_menu()
        
        elif choice == "8":
            install_libraries()
        
        elif choice == "9":
            ConsoleManager.clear_and_show_header("📤 ЭКСПОРТ/ИМПОРТ")
            print("\n1. 📤 Экспортировать текущий список модов")
            print("2. 📥 Импортировать список и скачать")
            print("3. ↩️ Назад")
            print("="*60)
            sub = input("\nВыберите действие (1-3): ").strip()
            if sub == "1":
                if hasattr(downloader, 'current_mod_ids') and downloader.current_mod_ids:
                    downloader.export_mods_list(downloader.current_mod_ids)
                else:
                    print(Colors.warning("⚠ Нет загруженного списка модов"))
                input("\nНажмите Enter для продолжения...")
            elif sub == "2":
                mods = downloader.import_mods_list()
                if mods:
                    downloader.current_mod_ids = mods
                    downloader.download_mods_list(mods)
            elif sub == "3":
                continue
            else:
                print(Colors.error("❌ Неверный выбор"))
                time.sleep(1)

        elif choice == "0":
            ConsoleManager.clear()
            print("\n👋 До свидания!")
            break
        
        else:
            print(Colors.error("❌ Неверный выбор"))
            time.sleep(1)


if __name__ == "__main__":
    main()