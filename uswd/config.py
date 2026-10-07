"""
Константы и настройки путей USWD.

Все изменяемые значения (URL-источники, имена файлов настроек, версия)
собраны здесь, чтобы их было удобно менять в одном месте.
"""

VERSION = "1.3"
APP_NAME = "USWD"

# --- SteamCMD ---
STEAMCMD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"

# --- Список App ID игр (по приоритету) ---
APPID_SOURCES = [
    {
        "name": "jsnli/steamappidlist (ежедневно)",
        "urls": [
            "https://raw.githubusercontent.com/jsnli/steamappidlist/master/data/games_appid.json",
            "https://raw.githubusercontent.com/jsnli/steamappidlist/main/data/games_appid.json",
        ],
        "max_size_mb": 50,
    },
    {
        "name": "dgibbs64/SteamCMD-AppID-List (архив 2023)",
        "urls": [
            "https://raw.githubusercontent.com/dgibbs64/SteamCMD-AppID-List/master/steamcmd_appid.json",
        ],
        "max_size_mb": 20,
    },
]

# Срок актуальности локального списка игр (в секундах)
APPID_CACHE_TTL = 7 * 24 * 3600  # 7 дней

# --- Имена цветов интерфейса (порядок как в меню) ---
COLOR_NAMES = [
    "красный",
    "зеленый",
    "желтый",
    "синий",
    "фиолетовый",
    "голубой",
    "белый",
]

# --- Файлы настроек (в рабочей директории) ---
SETTINGS_FILE = "downloader_settings.txt"
COLOR_FILE = "color_settings.txt"
OUTPUT_MODE_FILE = "output_mode.txt"
CONSOLE_FILE = "console_settings.txt"
APPID_CACHE_FILE = "steam_appid_list.json"
APPID_SOURCE_FILE = "steam_appid_source.txt"

# --- Библиотеки, которые ставит USWD при необходимости ---
REQUIRED_LIBRARIES = ["requests", "beautifulsoup4"]
