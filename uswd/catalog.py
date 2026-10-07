"""Поиск игр: загрузка списка App ID и поиск по названию."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from uswd.colors import Colors
from uswd.config import (
    APPID_SOURCES,
    APPID_CACHE_TTL,
    APPID_CACHE_FILE,
    APPID_SOURCE_FILE,
)


class CatalogMixin:
    """Миксин с методами работы со списком игр Steam."""

    def _valid_appid_cache(self, cache_file: Path) -> bool:
        """Проверяет, что локальный список игр — валидный непустой JSON."""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return isinstance(data, (list, dict)) and bool(data)
        except Exception:
            return False

    def download_appid_list(self) -> Path:
        """Скачивает файл со списком App ID игр (основной + резервный источник)."""
        import requests

        sources = APPID_SOURCES
        cache_file = Path.cwd() / APPID_CACHE_FILE
        info_file = Path.cwd() / APPID_SOURCE_FILE

        # Проверяем, нужно ли обновлять (файл старше APPID_CACHE_TTL или повреждён)
        need_update = True
        if cache_file.exists():
            if self._valid_appid_cache(cache_file):
                file_age = time.time() - cache_file.stat().st_mtime
                if file_age < APPID_CACHE_TTL:
                    need_update = False
                    source_info = "неизвестно"
                    if info_file.exists():
                        try:
                            source_info = info_file.read_text(encoding='utf-8').strip()
                        except Exception:
                            pass
                    date_str = datetime.fromtimestamp(cache_file.stat().st_mtime).strftime('%d.%m.%Y')
                    print(Colors.success(
                        f"✅ Использую локальный список игр (от {date_str}, источник: {source_info})"
                    ))
            else:
                print(Colors.warning("⚠ Локальный список игр повреждён, обновляю..."))

        if need_update:
            for source in sources:
                # Пробуем каждый URL из списка
                for url in source['urls']:
                    print(Colors.info(f"📡 Попытка: скачиваю список из {source['name']}..."))
                    try:
                        response = requests.get(url, timeout=120)
                        response.raise_for_status()

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
                        print(Colors.warning("⚠ Таймаут подключения"))
                        continue
                    except requests.exceptions.RequestException as e:
                        print(Colors.warning(f"⚠ Ошибка сети: {e}"))
                        continue
                    except Exception as e:
                        print(Colors.warning(f"⚠ Не удалось скачать: {e}"))
                        continue

            # Если все источники не сработали
            if cache_file.exists() and self._valid_appid_cache(cache_file):
                print(Colors.warning("⚠ Не удалось скачать свежий список"))
                print(Colors.info("💡 Использую сохраненную копию"))
                return cache_file
            else:
                print(Colors.error("❌ Нет локальной копии. Поиск будет недоступен."))
                return None

        return cache_file

    def search_game_by_name(self, query: str) -> List[Tuple[str, str]]:
        """Ищет игру по названию в локальном JSON-файле (без API)."""
        if not query or len(query.strip()) < 2:
            print(Colors.error("❌ Введите хотя бы 2 символа для поиска"))
            return []

        query_lower = query.lower().strip()
        print(Colors.info(f"🔍 Поиск игры: '{query}'"))

        cache_file = self.download_appid_list()
        if not cache_file or not cache_file.exists():
            print(Colors.error("❌ Нет списка игр для поиска"))
            return []

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Формат 1: {"appid": "name"} (dgibbs64)
            # Формат 2: [{"appid": 123, "name": "Game Name"}] (список словарей)
            # Формат 3: {"apps": [{"appid": 123, "name": "Game Name"}]} (Steam API)
            results = []

            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    app_id = str(item.get("appid", ""))
                    name = str(item.get("name", ""))
                    if not name or not app_id:
                        continue
                    self._match_game(results, name, app_id, query_lower)

            elif isinstance(data, dict):
                if "apps" in data:
                    apps_list = data["apps"]
                    if isinstance(apps_list, list):
                        for app in apps_list:
                            if not isinstance(app, dict):
                                continue
                            app_id = str(app.get("appid", app.get("appId", "")))
                            name = app.get("name", "")
                            if not name or not app_id:
                                continue
                            self._match_game(results, name, app_id, query_lower)
                else:
                    for app_id, name in data.items():
                        if not isinstance(name, str):
                            continue
                        self._match_game(results, name, str(app_id), query_lower)

            # Убираем дубликаты
            seen = set()
            unique_results = []
            for name, app_id in results:
                if app_id not in seen:
                    seen.add(app_id)
                    unique_results.append((name, app_id))

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
            unique_results = unique_results[:100]

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
                        print(Colors.info("🔍 Определяю название игры..."))
                        try:
                            import requests
                            resp = requests.get(
                                f"https://store.steampowered.com/api/appdetails?appids={app_id}",
                                timeout=10
                            )
                            data = resp.json()
                            if app_id in data and data[app_id].get("success"):
                                game_name = data[app_id]["data"].get("name", f"App {app_id}")
                                print(Colors.success(f"✅ Найдена игра: {game_name}"))
                                return [(game_name, app_id)]
                            else:
                                print(Colors.warning("⚠ Не удалось определить название, использую App ID"))
                                return [(f"App {app_id}", app_id)]
                        except Exception:
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

    @staticmethod
    def _match_game(results: list, name: str, app_id: str, query_lower: str):
        """Добавляет совпадение в результаты с приоритетом точного/префиксного матча."""
        name_lower = name.lower()
        if name_lower == query_lower:
            results.insert(0, (name, app_id))
        elif name_lower.startswith(query_lower):
            results.append((name, app_id))
        elif query_lower in name_lower:
            results.append((name, app_id))
