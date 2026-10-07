"""Пользовательские меню: консоль, режим вывода, выбор игры, скачивание."""

import time

from uswd.colors import Colors
from uswd.console import ConsoleManager
from uswd.output_mode import OutputMode


class MenuMixin:
    """Миксин с интерактивными меню."""

    def console_menu(self):
        """Меню настройки консоли (очистка истории)."""
        while True:
            ConsoleManager.clear_and_show_header("🖥 НАСТРОЙКА КОНСОЛИ")

            print("\n  Текущий режим автоочистки: ", end="")
            if ConsoleManager.auto_clear_enabled:
                print(Colors.success("✅ ВКЛЮЧЕНА"))
                print(Colors.info("     (консоль очищается при каждом переходе между меню)"))
            else:
                print(Colors.warning("❌ ВЫКЛЮЧЕНА"))
                print(Colors.info("     (история консоли сохраняется между меню)"))

            print("\n" + "-" * 60)
            print("1. 🧹 Включить автоочистку консоли (рекомендуется)")
            print("2. 📜 Выключить автоочистку (сохранять историю)")
            print("3. 🔄 Очистить консоль сейчас")
            print("4. ↩️ Назад")
            print("=" * 60)

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
                print("=" * 60)
                print(Colors.header("  🖥 НАСТРОЙКА КОНСОЛИ"))
                print("=" * 60)
                print(Colors.success("\n✅ Консоль очищена!"))
                input("\nНажмите Enter для продолжения...")

            elif choice == "4":
                break

            else:
                print(Colors.error("❌ Неверный выбор"))
                time.sleep(1)

    def output_mode_menu(self):
        """Меню выбора режима вывода."""
        while True:
            ConsoleManager.clear_and_show_header("🔇 НАСТРОЙКА ВЫВОДА")

            print("\n  Текущий режим: ", end="")
            if OutputMode.current_mode == OutputMode.SILENT:
                print(Colors.info("🔇 ТИХИЙ (только прогресс)"))
            elif OutputMode.current_mode == OutputMode.NORMAL:
                print(Colors.info("📝 НОРМАЛЬНЫЙ (показывать детали)"))
            else:
                print(Colors.info("🐛 DEBUG (полный вывод)"))

            print("\n" + "-" * 60)
            print("1. 🔇 Тихий режим - только прогресс-бар и статистика")
            print("2. 📝 Нормальный режим - показывать детали скачивания")
            print("3. 🐛 Debug режим - полный вывод SteamCMD")
            print("4. ↩️ Назад")
            print("=" * 60)

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

    def select_game(self):
        """Меню выбора игры."""
        ConsoleManager.clear_and_show_header("🎮 ВЫБОР ИГРЫ")

        print("\n1. 🎮 RimWorld (по умолчанию)")
        print("2. 🎲 Своя игра (указать App ID вручную)")
        print("3. 🔍 Поиск игры по названию (обновляемая база, ~16 МБ)")
        print("=" * 60)

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
                self.game_name, self.game_id = results[int(pick) - 1]
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

    def download_menu(self):
        """Меню выбора типа скачивания."""
        while True:
            ConsoleManager.clear_and_show_header("📥 ВЫБОР ТИПА СКАЧИВАНИЯ")

            print("\n1. 📦 Скачать коллекцию модов (несколько модов по URL)")
            print("2. 🔧 Скачать один мод (по ID)")
            print("3. 📚 Пакетная загрузка (несколько коллекций/ID из файла)")
            print("4. ↩️ Назад в главное меню")
            print("=" * 60)

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
