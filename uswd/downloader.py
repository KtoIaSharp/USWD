"""Сборка приложения из миксинов."""

from uswd.settings import SettingsMixin
from uswd.catalog import CatalogMixin
from uswd.steamcmd import SteamCMDMixin
from uswd.workshop import WorkshopMixin
from uswd.menus import MenuMixin
from uswd.logger import Logger
from uswd.console import ConsoleManager


class SteamWorkshopDownloader(
    SettingsMixin,
    CatalogMixin,
    SteamCMDMixin,
    WorkshopMixin,
    MenuMixin,
):
    """Основной класс приложения: скачивание модов Steam Workshop через SteamCMD."""

    def __init__(self):
        self.steamcmd_path = None
        self.game_name = "RimWorld"
        self.game_id = "294100"
        self.download_dir = None
        self.workshop_dir = None
        self.game_mods_path = None
        self.current_mod_ids = []
        self.logger = Logger()
        self.download_start_time = None

        # Загружаем сохраненные настройки
        self.load_settings()
        self.load_output_mode()
        ConsoleManager.load_settings()
