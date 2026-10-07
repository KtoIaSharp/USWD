"""Загрузка и сохранение настроек приложения."""

from pathlib import Path

from uswd.config import SETTINGS_FILE, OUTPUT_MODE_FILE
from uswd.output_mode import OutputMode


class SettingsMixin:
    """Миксин с методами load/save настроек и режима вывода."""

    def load_output_mode(self):
        """Загружает сохраненный режим вывода."""
        mode_file = Path.cwd() / OUTPUT_MODE_FILE
        if mode_file.exists():
            try:
                mode = mode_file.read_text(encoding='utf-8').strip()
                OutputMode.set_mode(mode)
            except Exception:
                pass

    def save_output_mode(self):
        """Сохраняет режим вывода."""
        mode_file = Path.cwd() / OUTPUT_MODE_FILE
        with open(mode_file, 'w', encoding='utf-8') as f:
            f.write(OutputMode.current_mode)

    def load_settings(self):
        """Загружает сохраненные настройки."""
        settings_file = Path.cwd() / SETTINGS_FILE
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
            except Exception:
                pass

    def save_settings(self):
        """Сохраняет настройки."""
        settings_file = Path.cwd() / SETTINGS_FILE
        with open(settings_file, 'w', encoding='utf-8') as f:
            if self.steamcmd_path:
                f.write(f"STEAMCMD_PATH={self.steamcmd_path}\n")
            if self.game_mods_path:
                f.write(f"GAME_MODS_PATH={self.game_mods_path}\n")
            f.write(f"GAME_ID={self.game_id}\n")
            f.write(f"GAME_NAME={self.game_name}\n")
