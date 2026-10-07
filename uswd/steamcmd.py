"""Управление SteamCMD: установка, обновление, удаление, версия."""

import os
import shutil
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

from uswd.colors import Colors
from uswd.console import ConsoleManager
from uswd.config import STEAMCMD_URL


class SteamCMDMixin:
    """Миксин с методами управления SteamCMD."""

    # --- Проверка и поиск ---

    def check_steamcmd(self) -> bool:
        """Проверяет наличие SteamCMD."""
        if self.steamcmd_path and Path(self.steamcmd_path).exists():
            return True
        return False

    def find_steamcmd_in_folder(self, folder_path: Path):
        """Ищет steamcmd.exe в указанной папке и подпапках."""
        steamcmd_exe = folder_path / "steamcmd.exe"
        if steamcmd_exe.exists():
            return steamcmd_exe

        for root, _dirs, files in os.walk(folder_path):
            depth = Path(root).relative_to(folder_path).parts
            if len(depth) > 3:
                continue
            if "steamcmd.exe" in files:
                return Path(root) / "steamcmd.exe"

        return None

    def get_folder_size(self, folder_path: Path) -> str:
        """Возвращает размер папки в человекочитаемом формате."""
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
        except Exception:
            return "Неизвестно"

    # --- Меню ---

    def steamcmd_menu(self):
        """Меню управления SteamCMD."""
        while True:
            ConsoleManager.clear_and_show_header("🔧 УПРАВЛЕНИЕ STEAMCMD")

            if self.check_steamcmd():
                print(Colors.success(f"\n✅ Текущий путь: {self.steamcmd_path}"))
                print(f"📁 Размер: {self.get_folder_size(Path(self.steamcmd_path).parent)}")
            else:
                print(Colors.error("\n❌ SteamCMD не установлен"))

            print("\n" + "-" * 60)
            print("1. 📥 Установить SteamCMD (автоматически)")
            print("2. 📂 Указать папку с SteamCMD (поиск steamcmd.exe)")
            print("3. 🔄 Обновить SteamCMD")
            print("4. 🗑 Удалить SteamCMD")
            print("5. ℹ️ Проверить версию")
            print("6. ↩️ Назад в главное меню")
            print("=" * 60)

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

    # --- Действия ---

    def set_steamcmd_folder(self):
        """Указывает папку с SteamCMD (автоматически ищет steamcmd.exe)."""
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
        """Скачивает и устанавливает SteamCMD."""
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

        print(Colors.info("\n📥 Скачивание SteamCMD..."))
        self.logger.info(f"Установка SteamCMD в {install_path}")

        try:
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 / total_size)
                    print(f"  Прогресс: {percent:.1f}%", end='\r')

            urllib.request.urlretrieve(STEAMCMD_URL, zip_path, report_progress)
            print("\n  Загрузка завершена!")

            print(Colors.info("\n📦 Распаковка..."))
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
                print(Colors.error("❌ Не найден steamcmd.exe после установки"))
                self.logger.error("SteamCMD не найден после установки")
                input("\nНажмите Enter для продолжения...")
                return False

        except Exception as e:
            print(Colors.error(f"❌ Ошибка при установке SteamCMD: {e}"))
            self.logger.error(f"Ошибка установки SteamCMD: {e}")
            input("\nНажмите Enter для продолжения...")
            return False

    def update_steamcmd(self):
        """Обновляет SteamCMD."""
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
        """Удаляет SteamCMD."""
        if not self.steamcmd_path:
            print(Colors.error("❌ Путь к SteamCMD не указан"))
            input("\nНажмите Enter для продолжения...")
            return

        ConsoleManager.clear_and_show_header("🗑 УДАЛЕНИЕ STEAMCMD")

        steamcmd_folder = Path(self.steamcmd_path).parent
        print(Colors.warning("\n⚠ ВНИМАНИЕ! Вы собираетесь удалить SteamCMD из папки:"))
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
        """Проверяет версию SteamCMD."""
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
