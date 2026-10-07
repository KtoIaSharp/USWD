"""Режим вывода (тихий/нормальный/debug)."""


class OutputMode:
    """Управление режимом вывода (тихий/лог)."""

    SILENT = "silent"  # Показывать только прогресс
    NORMAL = "normal"  # Показывать всё
    DEBUG = "debug"    # Показывать всё + логи SteamCMD

    current_mode = NORMAL

    @classmethod
    def set_mode(cls, mode: str) -> bool:
        if mode in [cls.SILENT, cls.NORMAL, cls.DEBUG]:
            cls.current_mode = mode
            return True
        return False

    @classmethod
    def should_show_detail(cls) -> bool:
        return cls.current_mode in [cls.NORMAL, cls.DEBUG]

    @classmethod
    def should_show_steam_output(cls) -> bool:
        return cls.current_mode == cls.DEBUG
