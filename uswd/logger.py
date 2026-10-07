"""Логирование в файл."""

from datetime import datetime
from pathlib import Path


class Logger:
    """Логирование в файл logs/download_YYYYMMDD_HHMMSS.log."""

    def __init__(self):
        self.log_dir = Path.cwd() / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.start_new_session()

    def start_new_session(self):
        """Начинает новую сессию логирования."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = self.log_dir / f"download_{timestamp}.log"
        self.log(f"=== НОВАЯ СЕССИЯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    def log(self, message: str, level: str = "INFO"):
        """Записывает сообщение в лог."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        try:
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + "\n")
        except Exception:
            pass

    def info(self, message: str):
        self.log(message, "INFO")

    def error(self, message: str):
        self.log(message, "ERROR")

    def warning(self, message: str):
        self.log(message, "WARNING")

    def success(self, message: str):
        self.log(message, "SUCCESS")
