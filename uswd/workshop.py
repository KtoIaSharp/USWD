"""Скачивание модов/коллекций и установка в игру."""

import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import List

from uswd.colors import Colors
from uswd.console import ConsoleManager
from uswd.output_mode import OutputMode
from uswd.progress import ProgressBar


class WorkshopMixin:
    """Миксин со скачиванием модов, коллекций и установкой в игру."""

    # --- Учёт текущего списка модов (для экспорта) ---

    def _remember_mod_ids(self, mod_ids: List[str], reset: bool = False):
        """Запоминает ID модов в self.current_mod_ids (для экспорта)."""
        if reset or self.current_mod_ids is None:
            self.current_mod_ids = []
        for mod_id in mod_ids:
            if mod_id not in self.current_mod_ids:
                self.current_mod_ids.append(mod_id)

    def export_mods_list(self, mod_ids: List[str], file_path: Path = None):
        """Экспортирует список ID модов в файл."""
        if not file_path:
            raw = input("💾 Имя файла для экспорта (например, my_mods.txt): ").strip()
            if not raw:
                print(Colors.error("❌ Имя файла не указано"))
                return
            file_path = Path(raw)
        file_path.write_text("\n".join(mod_ids), encoding='utf-8')
        print(Colors.success(f"✅ Экспортировано {len(mod_ids)} модов в {file_path}"))

    def import_mods_list(self, file_path: Path = None) -> List[str]:
        """Импортирует список ID модов из файла."""
        if not file_path:
            raw = input("📂 Файл для импорта: ").strip()
            if not raw:
                print(Colors.error("❌ Путь не указан"))
                return []
            file_path = Path(raw)
        if not file_path.exists():
            print(Colors.error("Файл не найден"))
            return []
        lines = file_path.read_text(encoding='utf-8').strip().splitlines()
        mod_ids = [l.strip() for l in lines if l.strip().isdigit()]
        print(Colors.success(f"✅ Импортировано {len(mod_ids)} модов"))
        return mod_ids

    def _ask_install(self):
        """Спрашивает и при согласии устанавливает моды в игру."""
        install = input("\n💿 Установить скачанные моды в игру сейчас? (y/n): ").lower()
        if install == 'y':
            self.install_mods_to_game()

    def download_mods_list(self, mod_ids: List[str]):
        """Скачивает список модов по ID."""
        self._remember_mod_ids(mod_ids, reset=True)
        for mod_id in mod_ids:
            self.download_single_mod(mod_id, ask_install=False)
        if mod_ids:
            self._ask_install()

    def batch_download(self, file_path: Path = None):
        """Загружает список URL или ID из текстового файла (построчно)."""
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

        self._remember_mod_ids([], reset=True)
        for url in collection_urls:
            self.download_collection(url, ask_install=False, reset_mod_list=False)

        for mod_id in mod_ids:
            self.download_single_mod(mod_id, ask_install=False)

        if collection_urls or mod_ids:
            self._ask_install()

        print(Colors.success("\n✅ Пакетная загрузка завершена"))
        input("Нажмите Enter...")

    # --- Коллекции ---

    def get_mod_ids_from_collection(self, collection_url: str) -> List[str]:
        """Получает список ID модов из коллекции Steam Workshop."""
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

    # --- Скачивание ---

    def download_single_mod(self, mod_id: str, ask_install: bool = True):
        """Скачивает один мод по ID."""
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
        else:
            print(Colors.info(f"📥 Скачивание мода {mod_id}... (тихий режим)"))
        self.logger.info(f"Начало скачивания мода {mod_id}")

        self._remember_mod_ids([mod_id])

        script_path = self.download_dir / "download_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("@ShutdownOnFailedCommand 1\n")
            f.write("@NoPromptForPassword 1\n")
            f.write(f'force_install_dir "{self.download_dir}"\n')
            f.write("login anonymous\n")
            f.write(f"workshop_download_item {self.game_id} {mod_id}\n")
            f.write("quit\n")

        if OutputMode.should_show_detail():
            print(Colors.info("\n🚀 Запуск SteamCMD..."))

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

            for line in process.stdout:
                if OutputMode.should_show_steam_output():
                    print(f"  {line.strip()}")

            process.wait()

            elapsed = time.time() - start_time

            if process.returncode == 0:
                if OutputMode.should_show_detail():
                    print(Colors.success(f"\n✅ Мод {mod_id} скачан за {elapsed:.1f} сек!"))
                else:
                    print(Colors.success(f"✅ Мод {mod_id} скачан за {elapsed:.1f} сек"))
                print(f"📁 Мод скачан в: {self.workshop_dir}")
                self.logger.success(f"Мод {mod_id} скачан за {elapsed:.1f} сек")

                if ask_install:
                    self._ask_install()
            else:
                print(Colors.error(f"\n❌ Ошибка скачивания мода {mod_id} (код: {process.returncode})"))
                self.logger.error(f"Ошибка скачивания мода {mod_id}: код {process.returncode}")
                input("\nНажмите Enter для продолжения...")

        except Exception as e:
            print(Colors.error(f"❌ Ошибка: {e}"))
            self.logger.error(f"Ошибка скачивания мода {mod_id}: {e}")
            input("\nНажмите Enter для продолжения...")

    def download_collection(self, collection_url: str, ask_install: bool = True, reset_mod_list: bool = True):
        """Скачивает коллекцию модов с прогресс-баром и статистикой."""
        if not self.check_steamcmd():
            print(Colors.error("\n❌ SteamCMD не установлен. Установите его в пункте 3 меню."))
            input("\nНажмите Enter для продолжения...")
            return

        ConsoleManager.clear_and_show_header("📥 СКАЧИВАНИЕ КОЛЛЕКЦИИ")

        self.download_start_time = time.time()
        self.logger.info("=== НАЧАЛО СКАЧИВАНИЯ КОЛЛЕКЦИИ ===")
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

        self._remember_mod_ids(mod_ids, reset=reset_mod_list)

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

        print(Colors.info("\n🚀 Запуск SteamCMD..."))
        print(Colors.info("📊 Режим вывода: "), end="")
        if OutputMode.current_mode == OutputMode.SILENT:
            print(Colors.info("ТИХИЙ (только статистика)"))
        elif OutputMode.current_mode == OutputMode.NORMAL:
            print(Colors.info("НОРМАЛЬНЫЙ"))
        else:
            print(Colors.info("DEBUG"))

        print("=" * 60)

        progress = ProgressBar(total_mods, prefix="📥 Скачивание", suffix="модов")
        progress.start()

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
                    match = re.search(r'item (\d+)', line_stripped)
                    if match:
                        failed_mods.append(match.group(1))
                    self.logger.warning(f"Ошибка скачивания: {line_stripped[:100]}")

                # Вывод в режиме DEBUG
                if OutputMode.should_show_steam_output() and line_stripped:
                    if not any(k in line_stripped for k in ["Downloading item", "Success.", "ERROR!"]):
                        print(f"  {line_stripped}")

            process.wait()

            elapsed = time.time() - start_time

            progress.finish()

            # Итоговая статистика
            print("\n" + "=" * 60)
            print(Colors.header("  📊 СТАТИСТИКА СКАЧИВАНИЯ"))
            print("=" * 60)
            print(f"✅ Успешно скачано: {Colors.success(str(successful))} модов")
            print(f"❌ Ошибок: {Colors.error(str(failed))} модов")
            print(f"📁 Всего модов в коллекции: {total_mods}")

            if elapsed < 60:
                time_str = f"{elapsed:.1f} сек"
            elif elapsed < 3600:
                time_str = f"{elapsed/60:.1f} мин"
            else:
                time_str = f"{elapsed/3600:.1f} ч"
            print(f"⏱ Время выполнения: {time_str}")

            if elapsed > 0:
                avg_speed = total_mods / elapsed
                print(f"📈 Средняя скорость: {avg_speed:.2f} модов/сек")

            if failed_mods:
                print(f"\n{Colors.warning('⚠ Неудачные моды:')}")
                for mod_id in failed_mods[:10]:
                    print(f"  - {mod_id}")
                if len(failed_mods) > 10:
                    print(f"  ... и еще {len(failed_mods)-10}")

            print("=" * 60)

            self.logger.info(f"Скачивание завершено. Успешно: {successful}, Ошибок: {failed}")
            self.logger.info(f"Общее время: {time_str}")

            if process.returncode == 0 or successful > 0:
                print(Colors.success("\n✅ Процесс скачивания завершен!"))
                print(f"📁 Моды скачаны в: {self.workshop_dir}")

                downloaded = list(self.workshop_dir.iterdir()) if self.workshop_dir.exists() else []
                print(f"📊 Скачано папок: {len(downloaded)} из {total_mods}")

                if ask_install:
                    self._ask_install()
            else:
                print(Colors.error(f"\n❌ SteamCMD завершился с ошибкой (код: {process.returncode})"))
                self.logger.error(f"SteamCMD завершился с ошибкой: {process.returncode}")
                input("\nНажмите Enter для продолжения...")

        except Exception as e:
            print(Colors.error(f"❌ Ошибка: {e}"))
            self.logger.error(f"Ошибка скачивания: {e}")
            input("\nНажмите Enter для продолжения...")

    # --- Установка в игру ---

    def install_mods_to_game(self):
        """Устанавливает скачанные моды в игру."""
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

        progress = ProgressBar(len(downloaded_mods), prefix="📦 Установка", suffix="модов")
        progress.start()

        for i, mod_path in enumerate(downloaded_mods):
            dest_path = game_mods_path / mod_path.name

            if dest_path.exists():
                skipped += 1
                progress.update(current=i + 1)
                continue

            try:
                shutil.copytree(mod_path, dest_path)
                copied += 1
                self.logger.info(f"Установлен мод: {mod_path.name}")
            except Exception as e:
                print(Colors.error(f"\n  ❌ Ошибка: {e}"))
                self.logger.error(f"Ошибка установки {mod_path.name}: {e}")

            progress.update(current=i + 1)

        progress.finish()

        elapsed = time.time() - start_time
        if elapsed < 60:
            time_str = f"{elapsed:.1f} сек"
        elif elapsed < 3600:
            time_str = f"{elapsed/60:.1f} мин"
        else:
            time_str = f"{elapsed/3600:.1f} ч"

        print("\n" + "=" * 60)
        print(Colors.success("✅ Установка завершена!"))
        print(f"📊 Скопировано новых модов: {copied}")
        print(f"⏭ Пропущено (уже были): {skipped}")
        print(f"⏱ Время установки: {time_str}")
        print("=" * 60)

        self.logger.info(f"Установка завершена. Скопировано: {copied}, Пропущено: {skipped}, Время: {time_str}")

        input("\nНажмите Enter для продолжения...")
