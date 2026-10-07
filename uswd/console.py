"""Управление консолью: очистка и заголовки."""

import os
import sys
from pathlib import Path

from uswd.colors import Colors
from uswd.config import CONSOLE_FILE


class ConsoleManager:
    """Управление консолью (очистка, история)."""

    # Режим автоочистки (по умолчанию ВКЛЮЧЕН)
    auto_clear_enabled = True

    @classmethod
    def clear(cls):
        """Очищает консоль."""
        if cls.auto_clear_enabled:
            if sys.platform == "win32":
                os.system('cls')
            else:
                os.system('clear')

    @classmethod
    def set_auto_clear(cls, enabled: bool):
        """Включает/выключает автоочистку консоли."""
        cls.auto_clear_enabled = enabled
        settings_file = Path.cwd() / CONSOLE_FILE
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(f"AUTO_CLEAR={enabled}")

    @classmethod
    def load_settings(cls):
        """Загружает настройки автоочистки."""
        settings_file = Path.cwd() / CONSOLE_FILE
        if settings_file.exists():
            try:
                content = settings_file.read_text(encoding='utf-8').strip()
                if "AUTO_CLEAR=True" in content:
                    cls.auto_clear_enabled = True
                elif "AUTO_CLEAR=False" in content:
                    cls.auto_clear_enabled = False
            except Exception:
                pass

    @classmethod
    def clear_and_show_header(cls, title: str, subtitle: str = None):
        """Очищает консоль и показывает заголовок."""
        cls.clear()
        print("=" * 60)
        print(Colors.header(f"  {title}"))
        if subtitle:
            print(Colors.colorize(f"  {subtitle}"))
        print("=" * 60)
