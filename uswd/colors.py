"""Цвета для терминала."""

from pathlib import Path
from typing import Optional


class Colors:
    """Управление цветами в консоли."""

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

    # Соответствие имени цвета и ANSI-кода (используется в меню и сохранении)
    COLOR_CODES = {
        'красный': RED,
        'зеленый': GREEN,
        'желтый': YELLOW,
        'синий': BLUE,
        'фиолетовый': MAGENTA,
        'голубой': CYAN,
        'белый': WHITE,
    }

    @classmethod
    def set_color(cls, color_name: str) -> bool:
        colors = cls.COLOR_CODES
        if color_name and color_name.lower() in colors:
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

    @classmethod
    def load(cls, file_path=None) -> bool:
        """Загружает выбранный цвет из файла настроек."""
        path = Path(file_path) if file_path else Path.cwd() / "color_settings.txt"
        if not path.exists():
            return False
        try:
            name = path.read_text(encoding='utf-8').strip()
            return cls.set_color(name)
        except Exception:
            return False

    @classmethod
    def save(cls, file_path=None) -> bool:
        """Сохраняет текущий цвет в файл настроек."""
        path = Path(file_path) if file_path else Path.cwd() / "color_settings.txt"
        try:
            for name, code in cls.COLOR_CODES.items():
                if cls.current_color == code:
                    path.write_text(name, encoding='utf-8')
                    return True
        except Exception:
            return False
        return False
