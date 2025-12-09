#!/usr/bin/env python3
"""
Интеграционные тесты для проверки совместимости с основным приложением
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Добавляем родительскую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""

    def setUp(self):
        """Настройка перед каждым тестом"""
        # Мокаем все внешние зависимости
        self.setup_mocks()

    def setup_mocks(self):
        """Настройка моков для всех внешних зависимостей"""
        # PyQt5 моки
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
        mock_pyqt5.QtWidgets = Mock()

        # Serial моки
        mock_serial = Mock()
        mock_serial.Serial = Mock()
        mock_serial.tools = Mock()
        mock_serial.tools.list_ports = Mock()
        mock_serial.tools.list_ports.comports = Mock(return_value=[])

        # Matplotlib моки - более полные
        mock_matplotlib = Mock()
        mock_matplotlib.pyplot = Mock()
        mock_matplotlib.backends = Mock()
        mock_matplotlib.backends.backend_qt5agg = Mock()
        mock_matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg = Mock()
        mock_matplotlib.figure = Mock()
        mock_matplotlib.figure.Figure = Mock()
        mock_matplotlib.animation = Mock()
        mock_matplotlib.gridspec = Mock()

        # Применяем моки
        modules_to_mock = {
            'PyQt5': mock_pyqt5,
            'PyQt5.QtCore': mock_pyqt5.QtCore,
            'PyQt5.QtWidgets': mock_pyqt5.QtWidgets,
            'serial': mock_serial,
            'serial.tools': mock_serial.tools,
            'serial.tools.list_ports': mock_serial.tools.list_ports,
            'matplotlib': mock_matplotlib,
            'matplotlib.pyplot': mock_matplotlib.pyplot,
            'matplotlib.backends': mock_matplotlib.backends,
            'matplotlib.backends.backend_qt5agg': mock_matplotlib.backends.backend_qt5agg,
            'matplotlib.figure': mock_matplotlib.figure,
            'matplotlib.animation': mock_matplotlib.animation,
            'matplotlib.gridspec': mock_matplotlib.gridspec,
        }

        for name, module in modules_to_mock.items():
            sys.modules[name] = module

    def test_realtime_modules_import(self):
        """Тест импорта всех real-time модулей"""
        try:
            from core.realtime_driver import SerialEEGDriver, SyntheticEEGDriver, EEGSample, EEGSampleBatch
            from core.realtime_controller import RealtimeEEGController, RealtimeDataBuffer
            from realtime_work.realtime_recorder import RealtimeEEGRecorder
            from realtime_work.realtime_visualizer import RealtimeEEGPlot, RealtimeEEGWidget

            self.assertTrue(True, "Все real-time модули импортированы успешно")
        except ImportError as e:
            self.fail(f"Ошибка импорта real-time модулей: {e}")

    def test_existing_modules_still_work(self):
        """Тест что существующие модули все еще работают"""
        try:
            from data_loader.data_loader import EEGDataLoader
            from preprocessor.preprocessor import EEGPreprocessor
            from analyzer.analyzer import EEGAnalyzer
            from core.visualizer import EEGVisualizer
            from utils.performance import PerformanceMonitor

            # Проверяем что можно создать объекты
            loader = EEGDataLoader()
            preprocessor = EEGPreprocessor()
            analyzer = EEGAnalyzer()
            visualizer = EEGVisualizer()
            monitor = PerformanceMonitor()

            self.assertIsNotNone(loader)
            self.assertIsNotNone(preprocessor)
            self.assertIsNotNone(analyzer)
            self.assertIsNotNone(visualizer)
            self.assertIsNotNone(monitor)

        except Exception as e:
            self.fail(f"Ошибка работы с существующими модулями: {e}")

    def test_realtime_workflow(self):
        """Тест полного workflow real-time функциональности"""
        from core.realtime_driver import SyntheticEEGDriver, EEGSampleBatch
        from core.realtime_controller import RealtimeDataBuffer
        from realtime_work.realtime_recorder import RealtimeEEGRecorder

        # 1. Создаем драйвер
        driver = SyntheticEEGDriver(sample_rate_hz=100.0)

        # 2. Создаем буфер
        buffer = RealtimeDataBuffer(max_duration_seconds=5.0)

        # 3. Создаем рекордер (без реального файла)
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            recorder = RealtimeEEGRecorder()

            # 4. Симулируем workflow
            driver.open()

            # Получаем данные
            samples = []
            for i, sample in enumerate(driver.iter_samples()):
                samples.append(sample)
                if i >= 4:  # 5 образцов
                    break

            # Создаем пакет и добавляем в буфер
            batch = EEGSampleBatch(samples=samples)
            buffer.add_batch(batch)

            # Проверяем что данные добавились
            stats = buffer.get_statistics()
            self.assertEqual(stats['total_samples'], 5)
            self.assertEqual(stats['channels'], 1)

            driver.close()

    def test_data_format_compatibility(self):
        """Тест совместимости форматов данных (один канал)"""
        import numpy as np
        from core.realtime_driver import EEGSample, EEGSampleBatch
        from core.realtime_controller import RealtimeDataBuffer

        # Создаем данные в формате, совместимом с существующими модулями (один канал)
        buffer = RealtimeDataBuffer(max_duration_seconds=10.0)

        # Добавляем тестовые данные (только один канал)
        samples = []
        for i in range(10):
            timestamp = i * 0.004  # 250 Гц
            # Только один канал - альфа ритм
            amplitude = 50.0 * np.sin(2 * np.pi * 10 * timestamp)  # 10 Гц альфа
            samples.append(EEGSample(timestamp=timestamp, amplitudes=[amplitude]))

        batch = EEGSampleBatch(samples=samples)
        buffer.add_batch(batch)

        # Получаем данные в формате для анализа
        timestamps, channel_data = buffer.get_data_for_plotting(window_seconds=1.0)

        # Проверяем формат данных (один канал)
        self.assertEqual(len(timestamps), 10)
        self.assertEqual(len(channel_data), 1)  # 1 канал
        self.assertEqual(len(channel_data[0]), 10)  # 10 образцов в канале

        # Конвертируем в numpy array (как ожидают существующие модули)
        data_array = np.array(channel_data)
        self.assertEqual(data_array.shape, (1, 10))  # (1 канал, время)

        # Проверяем что данные в разумных пределах
        self.assertTrue(np.all(np.abs(data_array) < 100))  # Амплитуды в разумных пределах

    def test_error_handling(self):
        """Тест обработки ошибок"""
        from core.realtime_driver import SyntheticEEGDriver
        from core.realtime_controller import RealtimeDataBuffer

        # Тест создания драйвера с корректными параметрами (должно работать)
        try:
            driver = SyntheticEEGDriver(sample_rate_hz=250.0)
            self.assertIsNotNone(driver)
        except Exception as e:
            self.fail(f"Не удалось создать драйвер с корректными параметрами: {e}")

        # Тест создания буфера с корректными параметрами (должно работать)
        try:
            buffer = RealtimeDataBuffer(max_duration_seconds=10.0)
            self.assertIsNotNone(buffer)
        except Exception as e:
            self.fail(f"Не удалось создать буфер с корректными параметрами: {e}")

        # Тест закрытия драйвера без открытия (не должно вызывать ошибку)
        driver = SyntheticEEGDriver(sample_rate_hz=250.0)
        try:
            driver.close()
        except Exception as e:
            self.fail(f"Закрытие неоткрытого драйвера вызвало ошибку: {e}")

    def test_memory_management(self):
        """Тест управления памятью"""
        from core.realtime_driver import EEGSample, EEGSampleBatch
        from core.realtime_controller import RealtimeDataBuffer

        # Создаем буфер с коротким временем хранения
        buffer = RealtimeDataBuffer(max_duration_seconds=0.1)

        # Добавляем много данных
        for batch_num in range(5):
            samples = []
            for i in range(10):
                timestamp = batch_num * 0.1 + i * 0.01
                samples.append(EEGSample(timestamp=timestamp, amplitudes=[float(i)]))

            batch = EEGSampleBatch(samples=samples)
            buffer.add_batch(batch)

        # Проверяем что старые данные удалились
        stats = buffer.get_statistics()
        self.assertLess(stats['total_samples'], 50)  # Должно быть меньше всех добавленных
        self.assertLess(stats['duration_seconds'], 0.2)  # Должно быть близко к max_duration


def run_integration_tests():
    """Запуск интеграционных тестов"""
    print("ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ REAL-TIME ФУНКЦИОНАЛЬНОСТИ")
    print("=" * 60)

    # Создаем test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegration)

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 ВСЕ ИНТЕГРАЦИОННЫЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print(f"⚠️  Провалено тестов: {len(result.failures + result.errors)}")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(f"  {failure[1]}")
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(f"  {error[1]}")
        return 1


if __name__ == "__main__":
    sys.exit(run_integration_tests())
