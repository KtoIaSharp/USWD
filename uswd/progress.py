"""Визуальный прогресс-бар."""

import threading
import time

from uswd.colors import Colors


class ProgressBar:
    """Визуальный прогресс-бар с оценкой времени."""

    def __init__(self, total: int, prefix: str = "", suffix: str = "", length: int = 50):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.current = 0
        self.start_time = None
        self.last_update_time = None
        self.last_current = 0
        self.lock = threading.Lock()

    def start(self):
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_current = 0

    def update(self, current: int = None, increment: int = None):
        with self.lock:
            if current is not None:
                self.current = min(current, self.total)
            elif increment is not None:
                self.current = min(self.current + increment, self.total)

            self._draw()

    def _draw(self):
        percent = self.current / self.total if self.total else 0
        filled = int(self.length * percent)
        bar = '█' * filled + '░' * (self.length - filled)

        elapsed = time.time() - self.start_time if self.start_time else 0

        # Оценка оставшегося времени
        eta_str = ""
        if self.current > 0 and elapsed > 0:
            speed = self.current / elapsed
            remaining_items = self.total - self.current
            eta_seconds = remaining_items / speed if speed > 0 else 0

            if eta_seconds < 60:
                eta_str = f" ~{eta_seconds:.0f} сек"
            elif eta_seconds < 3600:
                eta_str = f" ~{eta_seconds/60:.0f} мин"
            else:
                eta_str = f" ~{eta_seconds/3600:.1f} ч"

        # Время выполнения
        if elapsed < 60:
            time_str = f"{elapsed:.0f} сек"
        elif elapsed < 3600:
            time_str = f"{elapsed/60:.1f} мин"
        else:
            time_str = f"{elapsed/3600:.1f} ч"

        print(
            f'\r{self.prefix} |{Colors.colorize(bar)}| {percent*100:.1f}% '
            f'{self.suffix} [{self.current}/{self.total}] ⏱ {time_str}{eta_str}',
            end='', flush=True
        )

    def finish(self):
        print()
        elapsed = time.time() - self.start_time if self.start_time else 0
        if elapsed < 60:
            print(Colors.success(f"✅ Завершено за {elapsed:.1f} сек"))
        elif elapsed < 3600:
            print(Colors.success(f"✅ Завершено за {elapsed/60:.1f} мин"))
        else:
            print(Colors.success(f"✅ Завершено за {elapsed/3600:.1f} ч"))
