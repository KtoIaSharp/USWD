"""Точка входа и главное меню."""

import subprocess
import sys
import time
from pathlib import Path

from uswd.colors import Colors
from uswd.console import ConsoleManager
from uswd.output_mode import OutputMode
from uswd.config import (
    VERSION,
    COLOR_FILE,
    REQUIRED_LIBRARIES,
)
from uswd.downloader import SteamWorkshopDownloader


def setup_console():
    """Настраивает консоль Windows: UTF-8 и поддержку ANSI-цветов.

    Без этого вывод эмодзи на консоли с кодовой страницей cp866/cp1251
    вызывает UnicodeEncodeError, а ANSI-коды печатаются как мусор.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
            # Включаем виртуальную обработку ANSI (VT) для окна консоли
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def color_settings_menu():
    """Меню выбора цвета."""
    ConsoleManager.clear_and_show_header("🎨 ВЫБОР ЦВЕТА ИНТЕРФЕЙСА")

    print("\nДоступные цвета:")
    print("1. 🔴 Красный")
    print("2. 🟢 Зеленый")
    print("3. 🟡 Желтый")
    print("4. 🔵 Синий")
    print("5. 🟣 Фиолетовый")
    print("6. 🔷 Голубой (по умолчанию)")
    print("7. ⚪ Белый")
    print("=" * 60)

    choice = input("\nВыберите цвет (1-7): ").strip()

    color_map = {
        "1": "красный",
        "2": "зеленый",
        "3": "желтый",
        "4": "синий",
        "5": "фиолетовый",
        "6": "голубой",
        "7": "белый",
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
    """Установка необходимых библиотек."""
    ConsoleManager.clear_and_show_header("📦 УСТАНОВКА БИБЛИОТЕК")

    libraries = REQUIRED_LIBRARIES

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
    """Проверяет установлены ли библиотеки."""
    try:
        import requests  # noqa: F401
        import bs4  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    """Главное меню программы."""
    setup_console()

    # Загружаем сохраненный цвет
    Colors.load(Path.cwd() / COLOR_FILE)

    # Загружаем настройки консоли
    ConsoleManager.load_settings()

    downloader = SteamWorkshopDownloader()

    while True:
        # Очищаем консоль перед показом главного меню (если включено)
        if ConsoleManager.auto_clear_enabled:
            ConsoleManager.clear()

        libs_installed = check_libraries()

        print("=" * 60)
        print(Colors.header(f"  UNIVERSAL STEAM WORKSHOP DOWNLOADER v{VERSION}"))
        print(Colors.colorize("  Скачивание коллекций модов через SteamCMD"))
        print(Colors.colorize(f"  {Colors.BRIGHT_MAGENTA}by KtoIa{Colors.RESET}"))
        print("=" * 60)
        print(Colors.header("\n  ГЛАВНОЕ МЕНЮ"))
        print("=" * 60)
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
        print("=" * 60)

        # Статусы
        if libs_installed:
            print(Colors.success("\n📚 Библиотеки: ✅ установлены"))
        else:
            print(Colors.error("\n📚 Библиотеки: ❌ не установлены"))

        print("🔇 Режим вывода: ", end="")
        if OutputMode.current_mode == OutputMode.SILENT:
            print(Colors.info("🔇 ТИХИЙ"))
        elif OutputMode.current_mode == OutputMode.NORMAL:
            print(Colors.info("📝 НОРМАЛЬНЫЙ"))
        else:
            print(Colors.info("🐛 DEBUG"))

        print("🖥 Автоочистка консоли: ", end="")
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
                    print(Colors.warning("⚠ Путь не существует, но сохранен. Создайте папку позже."))
                    downloader.game_mods_path = str(path_obj)
                    downloader.save_settings()
            else:
                print(Colors.error("❌ Путь не указан"))

            input("\nНажмите Enter для продолжения...")

        elif choice == "5":
            if color_settings_menu():
                Colors.save(Path.cwd() / COLOR_FILE)

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
            print("=" * 60)
            sub = input("\nВыберите действие (1-3): ").strip()
            if sub == "1":
                if downloader.current_mod_ids:
                    downloader.export_mods_list(downloader.current_mod_ids)
                else:
                    print(Colors.warning("⚠ Нет загруженного списка модов"))
                input("\nНажмите Enter для продолжения...")
            elif sub == "2":
                mods = downloader.import_mods_list()
                if mods:
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
