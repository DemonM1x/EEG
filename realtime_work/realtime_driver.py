import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import serial
from serial.tools import list_ports


@dataclass
class EEGSample:
    timestamp: float  # время в секундах с начала сессии
    amplitudes: list[float]  # амплитуды по каналам


@dataclass
class EEGSampleBatch:
    samples: list[EEGSample]


class EEGAcquisitionDriver(ABC):

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def iter_samples(self) -> Iterable[EEGSample]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class SerialEEGDriver(EEGAcquisitionDriver):

    def __init__(
            self,
            port: str,
            baudrate: int = 115200,
            timeout: float = 1.0,
            sample_rate_hz: float = 250.0
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.fs = sample_rate_hz
        self.dt = 1.0 / self.fs if sample_rate_hz > 0 else 0
        self._running = False
        self.ser: Optional[serial.Serial] = None
        self._start_time = None

    def open(self) -> None:
        try:
            print("Доступные порты:", [(port.device, port.description) for port in list_ports.comports()])

            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )

            # Время для установления соединения
            time.sleep(2)

            # Сброс буфера устройства
            if self.ser.is_open:
                self.ser.reset_input_buffer()

            self._running = True
            self._start_time = time.time()
            print(f"Подключено к {self.port} на скорости {self.baudrate} baud")

        except serial.SerialException as e:
            raise RuntimeError(f"Не удалось открыть serial порт {self.port}: {e}")

    def iter_samples(self) -> Iterable[EEGSample]:
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial порт не открыт. Вызовите open() сначала.")

        buffer = b""

        while self._running:
            try:
                # Чтение доступных данных
                data = self.ser.read(self.ser.in_waiting or 1)
                if data:
                    buffer += data

                    # Парсинг полных строк (CSV формат)
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        sample = self._parse_line(line.strip())
                        if sample:
                            yield sample

                # Контроль скорости чтения для приближения к sample rate
                if self.dt > 0:
                    time.sleep(self.dt)

            except serial.SerialException as e:
                print(f"Ошибка чтения serial: {e}")
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                break

    def _parse_line(self, line: bytes) -> Optional[EEGSample]:
        if not line:
            return None

        try:
            # Декодирование и очистка строки
            decoded = line.decode('utf-8', errors='ignore').strip()

            # Пропуск пустых строк или не-данных
            if not decoded:
                return None

            # Пропуск комментариев (строки начинающиеся с #)
            if decoded.startswith('#'):
                return None

            # Разделение CSV формата
            parts = decoded.split(',')

            # Поддержка форматов для одного канала:
            # 1. "value" - только значение (используем локальное время)
            # 2. "timestamp,value" - время и значение

            if len(parts) == 1:
                # Формат: только значение
                try:
                    raw_value = float(parts[0])
                    timestamp = time.time() - (self._start_time or time.time())
                    return EEGSample(timestamp=timestamp, amplitudes=[raw_value])
                except ValueError:
                    return None

            elif len(parts) >= 2:
                # Формат: timestamp,value (берем только первое значение)
                try:
                    timestamp_str, value_str = parts[0], parts[1]
                    timestamp = float(timestamp_str)
                    raw_value = float(value_str)
                    return EEGSample(timestamp=timestamp, amplitudes=[raw_value])
                except ValueError:
                    return None

        except Exception as e:
            print(f"Ошибка парсинга строки '{line}': {e}")

        return None

    def close(self) -> None:
        self._running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("Serial соединение закрыто")

    @staticmethod
    def list_available_ports():
        return [(port.device, port.description) for port in list_ports.comports()]


class SyntheticEEGDriver(EEGAcquisitionDriver):

    def __init__(self, sample_rate_hz: float = 250.0):
        self.fs = sample_rate_hz
        self.dt = 1.0 / self.fs
        self._running = False
        self._start_time = None

    def open(self) -> None:
        self._running = True
        self._start_time = time.time()
        print("Синтетический драйвер запущен (один канал)")

    def iter_samples(self) -> Iterable[EEGSample]:
        sample_count = 0

        while self._running:
            timestamp = sample_count / self.fs

            # Генерация синтетического ЭЭГ сигнала для одного канала
            # Альфа ритм (8-13 Гц)
            alpha_signal = 50 * np.sin(2 * np.pi * 10.0 * timestamp)

            # Бета ритм (13-30 Гц)
            beta_signal = 20 * np.sin(2 * np.pi * 20.0 * timestamp)

            # Шум
            noise = 5 * np.random.normal()

            # Случайные артефакты
            artifact = 0
            if np.random.random() < 0.001:  # 0.1% вероятность артефакта
                artifact = 100 * np.random.normal()

            total_signal = alpha_signal + beta_signal + noise + artifact

            yield EEGSample(timestamp=timestamp, amplitudes=[total_signal])

            sample_count += 1
            time.sleep(self.dt)

    def close(self) -> None:
        self._running = False
        print("Синтетический драйвер остановлен")
