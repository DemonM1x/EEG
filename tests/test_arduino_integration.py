#!/usr/bin/env python3
"""
Тест интеграции с Arduino и real-time обработкой
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Добавляем родительскую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestArduinoIntegration(unittest.TestCase):
    """Тесты интеграции с Arduino"""

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Мокаем serial модуль
        self.mock_serial = Mock()
        sys.modules['serial'] = self.mock_serial
        sys.modules['serial.tools'] = Mock()
        sys.modules['serial.tools.list_ports'] = Mock()

        # Мокаем PyQt5
        mock_pyqt5 = Mock()
        mock_pyqt5.QtCore = Mock()
        mock_pyqt5.QtCore.QObject = object

        # Создаем правильный мок для pyqtSignal
        class MockSignal:
            def __init__(self, *args):
                pass

            def emit(self, *args):
                pass

            def connect(self, *args):
                pass

        mock_pyqt5.QtCore.pyqtSignal = MockSignal
        mock_pyqt5.QtCore.QTimer = Mock()

        sys.modules['PyQt5'] = mock_pyqt5
        sys.modules['PyQt5.QtCore'] = mock_pyqt5.QtCore

    def test_serial_driver_creation(self):
        """Тест создания Serial драйвера (один канал)"""
        from core.realtime_driver import SerialEEGDriver

        driver = SerialEEGDriver(
            port="COM3",
            baudrate=115200,
            sample_rate_hz=250.0
        )

        self.assertEqual(driver.port, "COM3")
        self.assertEqual(driver.baudrate, 115200)
        self.assertEqual(driver.fs, 250.0)

    def test_serial_data_parsing(self):
        """Тест парсинга данных от Arduino (один канал)"""
        from core.realtime_driver import SerialEEGDriver

        driver = SerialEEGDriver("COM3", 115200, 250.0)

        # Тест различных форматов данных для одного канала
        test_cases = [
            # (входная строка, ожидаемый результат)
            (b"1.234,567.89", (1.234, [567.89])),
            (b"2.345,123.45", (2.345, [123.45])),  # Берем только первый канал
            (b"456.78", (None, [456.78])),  # Только значение
            (b"", None),  # Пустая строка
            (b"invalid", None),  # Некорректные данные
        ]

        for input_data, expected in test_cases:
            result = driver._parse_line(input_data)

            if expected is None:
                self.assertIsNone(result)
            else:
                self.assertIsNotNone(result)
                if expected[0] is not None:
                    self.assertEqual(result.timestamp, expected[0])
                self.assertEqual(result.amplitudes, expected[1])

    def test_arduino_data_format_compatibility(self):
        """Тест совместимости с форматом данных Arduino (один канал)"""
        from core.realtime_driver import SerialEEGDriver, EEGSampleBatch
        from core.realtime_controller import RealtimeDataBuffer

        # Симулируем данные от Arduino скетча (берем только первый канал)
        arduino_data = [
            "0.000000,45.67",
            "0.004000,46.12",
            "0.008000,44.23",
            "0.012000,47.56",
            "0.016000,43.89"
        ]

        driver = SerialEEGDriver("COM3", 115200, 250.0)
        buffer = RealtimeDataBuffer(max_duration_seconds=1.0)

        # Парсим данные
        samples = []
        for line in arduino_data:
            sample = driver._parse_line(line.encode())
            if sample:
                samples.append(sample)

        # Проверяем результаты
        self.assertEqual(len(samples), 5)

        # Проверяем временные метки
        for i, sample in enumerate(samples):
            expected_time = i * 0.004
            self.assertAlmostEqual(sample.timestamp, expected_time, places=6)

        # Проверяем количество каналов (должен быть один)
        for sample in samples:
            self.assertEqual(len(sample.amplitudes), 1)

        # Добавляем в буфер
        batch = EEGSampleBatch(samples=samples)
        buffer.add_batch(batch)

        # Проверяем буфер
        stats = buffer.get_statistics()
        self.assertEqual(stats['total_samples'], 5)
        self.assertEqual(stats['channels'], 1)

    def test_real_time_processing_pipeline(self):
        """Тест полного pipeline обработки real-time данных"""
        from core.realtime_driver import EEGSample, EEGSampleBatch
        from core.realtime_controller import RealtimeDataBuffer

        # Создаем компоненты (один канал)
        buffer = RealtimeDataBuffer(max_duration_seconds=2.0)

        # Симулируем поток данных от Arduino
        import numpy as np

        # Генерируем синтетический ЭЭГ сигнал (альфа ритм 10 Гц)
        sample_rate = 250.0
        duration = 1.0  # 1 секунда
        n_samples = int(sample_rate * duration)

        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            # Альфа ритм с шумом
            alpha_signal = 50.0 * np.sin(2 * np.pi * 10.0 * t)
            noise = 5.0 * np.random.normal()
            amplitude = alpha_signal + noise

            sample = EEGSample(timestamp=t, amplitudes=[amplitude])
            samples.append(sample)

        # Обрабатываем данные пакетами (как в реальном времени)
        batch_size = 10
        for i in range(0, len(samples), batch_size):
            batch_samples = samples[i:i + batch_size]
            batch = EEGSampleBatch(samples=batch_samples)
            buffer.add_batch(batch)

        # Проверяем результаты
        stats = buffer.get_statistics()
        self.assertEqual(stats['total_samples'], n_samples)
        self.assertAlmostEqual(stats['duration_seconds'], duration, places=1)

        # Получаем данные для анализа
        timestamps, channel_data = buffer.get_data_for_plotting(window_seconds=2.0)

        self.assertEqual(len(timestamps), n_samples)
        self.assertEqual(len(channel_data), 1)
        self.assertEqual(len(channel_data[0]), n_samples)

        # Проверяем что данные в разумных пределах (альфа ритм ±шум)
        data_array = np.array(channel_data[0])
        self.assertTrue(np.all(np.abs(data_array) < 100))  # Разумные амплитуды

    def test_com_port_detection(self):
        """Тест определения COM портов"""
        from core.realtime_driver import SerialEEGDriver

        # Мокаем список портов
        mock_port1 = Mock()
        mock_port1.device = "COM3"
        mock_port1.description = "Arduino Uno"

        mock_port2 = Mock()
        mock_port2.device = "COM4"
        mock_port2.description = "USB Serial Port"

        with patch('core.realtime_driver.list_ports.comports', return_value=[mock_port1, mock_port2]):
            ports = SerialEEGDriver.list_available_ports()

            self.assertEqual(len(ports), 2)
            self.assertEqual(ports[0], ("COM3", "Arduino Uno"))
            self.assertEqual(ports[1], ("COM4", "USB Serial Port"))

    def test_error_handling_serial(self):
        """Тест обработки ошибок Serial соединения"""
        from core.realtime_driver import SerialEEGDriver

        # Тест с несуществующим портом (один канал)
        driver = SerialEEGDriver("COM999", 115200, 250.0)

        # Создаем настоящее исключение, наследующее от Exception
        class MockSerialException(Exception):
            pass

        # Мокаем serial модуль и его исключения
        with patch('core.realtime_driver.serial') as mock_serial_module:
            mock_serial_module.SerialException = MockSerialException
            mock_serial_module.Serial.side_effect = MockSerialException("Port not found")
            mock_serial_module.PARITY_NONE = 'N'
            mock_serial_module.STOPBITS_ONE = 1
            mock_serial_module.EIGHTBITS = 8

            with patch('core.realtime_driver.list_ports.comports', return_value=[]):
                with self.assertRaises(RuntimeError):
                    driver.open()

    def test_data_recording_integration(self):
        """Тест интеграции записи данных (один канал)"""
        from core.realtime_driver import EEGSample, EEGSampleBatch
        from realtime_work.realtime_recorder import RealtimeEEGRecorder
        import tempfile
        import os

        # Создаем временную директорию и файл
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test_recording.csv')

        try:
            # Создаем рекордер (один канал)
            recorder = RealtimeEEGRecorder()

            # Проверяем начальное состояние
            self.assertFalse(recorder.is_recording_active(), "Запись не должна быть активна изначально")

            # Начинаем запись
            start_result = recorder.start_recording(temp_file)

            # Если start_recording вернул False, выводим детали для отладки
            if not start_result:
                print(f"Ошибка старта записи. Файл: {temp_file}")
                print(f"Директория существует: {os.path.exists(temp_dir)}")
                print(f"Статус записи: {recorder.is_recording_active()}")

            self.assertTrue(start_result, f"Не удалось начать запись в файл: {temp_file}")

            # Проверяем что запись активна после старта
            self.assertTrue(recorder.is_recording_active(), "Запись не активна после старта")

            # Создаем тестовые данные (симуляция Arduino, один канал)
            samples = []
            for i in range(5):  # Уменьшаем количество для упрощения отладки
                timestamp = i * 0.004  # 250 Гц
                # Симулируем одноканальные данные от Arduino
                ch1 = 50.0 * np.sin(2 * np.pi * 10.0 * timestamp)  # 10 Гц
                samples.append(EEGSample(timestamp=timestamp, amplitudes=[ch1]))

            batch = EEGSampleBatch(samples=samples)

            # Записываем данные
            write_result = recorder.write_batch(batch)
            self.assertTrue(write_result, "Не удалось записать данные")

            # Проверяем что запись все еще активна
            self.assertTrue(recorder.is_recording_active(),
                            f"Запись не активна после записи данных. Записано образцов: {recorder.samples_written}")

            # Останавливаем запись
            stop_result = recorder.stop_recording()
            self.assertTrue(stop_result, "Не удалось остановить запись")

            # Проверяем файл
            self.assertTrue(os.path.exists(temp_file), f"Файл не существует: {temp_file}")

            # Проверяем содержимое файла
            with open(temp_file, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')

                # Должен быть заголовок + данные + метаданные
                self.assertGreater(len(lines), 5, f"Недостаточно строк в файле. Содержимое:\n{content}")

                # Проверяем что есть данные в правильном формате (один канал)
                data_lines = [line for line in lines if
                              not line.startswith('#') and ',' in line and 'timestamp' not in line]
                self.assertEqual(len(data_lines), 5, f"Неправильное количество строк данных. Найдено: {data_lines}")

        except Exception as e:
            print(f"Исключение в тесте: {e}")
            print(
                f"Статус записи: {recorder.is_recording_active() if 'recorder' in locals() else 'recorder не создан'}")
            raise
        finally:
            # Удаляем временные файлы
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass


def run_arduino_tests():
    """Запуск тестов Arduino интеграции"""
    print("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ С ARDUINO")
    print("=" * 50)

    # Создаем test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestArduinoIntegration)

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 ВСЕ ТЕСТЫ ARDUINO ИНТЕГРАЦИИ ПРОЙДЕНЫ!")
        return 0
    else:
        print(f"⚠️  Провалено тестов: {len(result.failures + result.errors)}")
        return 1


if __name__ == "__main__":
    # Импортируем numpy для тестов
    try:
        import numpy as np
    except ImportError:
        print("❌ Для тестов требуется numpy")
        print("   Установите: pip install numpy")
        sys.exit(1)

    sys.exit(run_arduino_tests())
