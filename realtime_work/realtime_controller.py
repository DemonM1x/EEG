import queue
import threading
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from realtime_work.realtime_driver import EEGAcquisitionDriver, EEGSample, EEGSampleBatch


class RealtimeEEGController(QObject):
    # Сигналы для GUI
    data_received = pyqtSignal(object)  # EEGSampleBatch
    status_changed = pyqtSignal(str)  # Статус соединения
    error_occurred = pyqtSignal(str)  # Ошибки

    def __init__(self, driver: EEGAcquisitionDriver, batch_size: int = 64):
        super().__init__()
        self.driver = driver
        self.batch_size = batch_size
        self.queue: queue.Queue[EEGSampleBatch] = queue.Queue(maxsize=64)
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Таймер для обработки очереди в главном потоке
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_queue)
        self.timer_interval = 20  # мс

        # Статистика
        self.samples_received = 0
        self.batches_processed = 0

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        try:
            self._running.set()
            self._thread = threading.Thread(target=self._acquisition_loop, daemon=True)
            self._thread.start()

            # Запуск таймера обработки очереди
            self.timer.start(self.timer_interval)

            self.status_changed.emit("Запущено")
            print("Контроллер получения данных запущен")

        except Exception as e:
            self.error_occurred.emit(f"Ошибка запуска: {e}")

    def stop(self) -> None:
        if not self._running.is_set():
            return

        self._running.clear()
        self.timer.stop()

        if self._thread is not None:
            self._thread.join(timeout=2.0)

        self.status_changed.emit("Остановлено")
        print("Контроллер получения данных остановлен")

    def _acquisition_loop(self) -> None:
        try:
            self.driver.open()
            batch: list[EEGSample] = []

            for sample in self.driver.iter_samples():
                if not self._running.is_set():
                    break

                batch.append(sample)
                self.samples_received += 1

                # Отправка пакета когда он заполнен
                if len(batch) >= self.batch_size:
                    try:
                        self.queue.put_nowait(EEGSampleBatch(samples=batch.copy()))
                        batch.clear()
                        self.batches_processed += 1
                    except queue.Full:
                        # Если очередь переполнена, удаляем старые данные
                        try:
                            self.queue.get_nowait()
                            self.queue.put_nowait(EEGSampleBatch(samples=batch.copy()))
                            batch.clear()
                        except queue.Empty:
                            pass

        except Exception as e:
            self.error_occurred.emit(f"Ошибка получения данных: {e}")
        finally:
            try:
                self.driver.close()
            except:
                pass

    def _process_queue(self) -> None:
        processed_batches = 0
        max_batches_per_cycle = 5  # Ограничиваем количество пакетов за цикл

        while processed_batches < max_batches_per_cycle:
            try:
                batch = self.queue.get_nowait()
                self.data_received.emit(batch)
                processed_batches += 1
            except queue.Empty:
                break

    def get_statistics(self) -> dict:
        return {
            'samples_received': self.samples_received,
            'batches_processed': self.batches_processed,
            'queue_size': self.queue.qsize(),
            'is_running': self._running.is_set()
        }

    def clear_statistics(self) -> None:
        self.samples_received = 0
        self.batches_processed = 0


class RealtimeDataBuffer:

    def __init__(self, max_duration_seconds: float = 30.0, normalize_arduino_data: bool = True):
        self.max_duration = max_duration_seconds
        self.normalize_arduino_data = normalize_arduino_data

        # Буферы данных для одного канала
        self.timestamps = []
        self.data = []  # Данные одного канала

        # Глобальные экстремумы для масштабирования
        self.global_min = None
        self.global_max = None

    def add_batch(self, batch: EEGSampleBatch) -> None:
        if not batch.samples:
            return

        # Добавление новых данных
        for sample in batch.samples:
            self.timestamps.append(sample.timestamp)

            # Берем данные первого (единственного) канала
            if sample.amplitudes:
                raw_value = sample.amplitudes[0]

                # Применяем нормализацию Arduino данных если включена
                if self.normalize_arduino_data:
                    value = self._normalize_arduino_data(raw_value)
                else:
                    value = raw_value

                self.data.append(value)

                # Обновление глобальных экстремумов
                if self.global_min is None or value < self.global_min:
                    self.global_min = value
                if self.global_max is None or value > self.global_max:
                    self.global_max = value
            else:
                self.data.append(0.0)

        # Удаление старых данных
        self._cleanup_old_data()

    def _normalize_arduino_data(self, raw_value: float) -> float:
        # Arduino ADC: 10-битный (0-1023) соответствует 0-5В
        # Формула: voltage = (adc_value / 1023.0) * 5.0

        # Проверяем, что значение в ожидаемом диапазоне Arduino ADC
        if 0 <= raw_value <= 1023:
            # Нормализуем в диапазон 0-5В
            normalized = (raw_value / 1023.0) * 5.0
        else:
            # Если значение вне диапазона Arduino, возможно это уже нормализованные данные
            # или данные от другого источника - оставляем как есть
            normalized = raw_value

        return normalized

    def _cleanup_old_data(self) -> None:
        if not self.timestamps:
            return

        current_time = self.timestamps[-1]
        cutoff_time = current_time - self.max_duration

        # Находим индекс первого элемента, который нужно оставить
        keep_from_index = 0
        for i, timestamp in enumerate(self.timestamps):
            if timestamp >= cutoff_time:
                keep_from_index = i
                break

        # Удаляем старые данные
        if keep_from_index > 0:
            self.timestamps = self.timestamps[keep_from_index:]
            self.data = self.data[keep_from_index:]

    def get_data_for_plotting(self, window_seconds: float = 10.0) -> tuple:
        if not self.timestamps:
            return [], [[]]

        current_time = self.timestamps[-1]
        start_time = current_time - window_seconds

        # Находим данные в окне
        window_timestamps = []
        window_data = []

        for i, timestamp in enumerate(self.timestamps):
            if timestamp >= start_time:
                window_timestamps.append(timestamp)
                window_data.append(self.data[i])

        return window_timestamps, [window_data]

    def get_latest_values(self) -> list:
        if not self.data:
            return [0.0]

        return [self.data[-1]]

    def get_extrema(self) -> tuple:
        if self.global_min is None or self.global_max is None:
            return -100.0, 100.0
        return self.global_min, self.global_max

    def clear(self) -> None:
        self.timestamps.clear()
        self.data.clear()
        self.global_min = None
        self.global_max = None

    def get_statistics(self) -> dict:
        duration = 0.0
        if len(self.timestamps) > 1:
            duration = self.timestamps[-1] - self.timestamps[0]

        return {
            'total_samples': len(self.timestamps),
            'duration_seconds': duration,
            'channels': 1,
            'global_min': self.global_min,
            'global_max': self.global_max,
            'memory_usage_mb': self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> float:
        # Приблизительная оценка
        samples_count = len(self.timestamps)
        bytes_per_sample = 8 * 2  # float64 для timestamp + один канал
        return (samples_count * bytes_per_sample) / (1024 * 1024)
