import os
import sys
import unittest

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.analyzer import EEGAnalyzer
from preprocessor.preprocessor import EEGPreprocessor
from data_loader.data_loader import EEGDataLoader


class TestEEGAnalyzer(unittest.TestCase):

    def setUp(self):
        """Настройка тестовых данных"""
        self.analyzer = EEGAnalyzer()
        self.preprocessor = EEGPreprocessor()
        self.data_loader = EEGDataLoader()

        # Генерация тестовых данных
        self.test_data, self.sampling_rate, _ = self.data_loader.generate_test_data(
            duration=5, sampling_rate=250, n_channels=4
        )

        # Предобработка данных
        self.processed_data = self.preprocessor.apply_filters(
            self.test_data, self.sampling_rate
        )

    def test_spectral_power_calculation(self):
        """Тест расчета спектральной мощности"""
        result = self.analyzer.calculate_spectral_power(
            self.processed_data, self.sampling_rate
        )

        # Проверка наличия ключевых результатов
        self.assertIn('frequencies', result)
        self.assertIn('power_spectrum', result)
        self.assertIn('rhythm_power', result)
        self.assertIn('relative_power', result)

        # Проверка размеров
        self.assertEqual(len(result['frequencies']), len(result['power_spectrum']))

        # Проверка корректности мощности ритмов
        total_relative_power = sum(result['relative_power'].values())
        self.assertAlmostEqual(total_relative_power, 1.0, places=2)

    def test_spike_detection(self):
        """Тест детекции спайков"""
        # Добавляем искусственные спайки
        test_signal = self.processed_data[0].copy()
        spike_positions = [100, 500, 900]
        test_signal[spike_positions] += 100  # Большие выбросы

        result = self.analyzer.detect_spikes(
            test_signal, self.sampling_rate, threshold=2.0
        )

        self.assertIn('spike_count', result)
        self.assertIn('spike_times', result)
        self.assertGreaterEqual(result['spike_count'], len(spike_positions))

    def test_rhythm_analysis(self):
        """Тест анализа ритмов"""
        result = self.analyzer.analyze_rhythms(
            self.processed_data, self.sampling_rate
        )

        self.assertIn('rhythm_analysis', result)
        self.assertIn('dominant_rhythm', result)
        self.assertIn('spectral_entropy', result)

        # Проверка наличия всех ритмов
        expected_rhythms = ['delta', 'theta', 'alpha', 'beta', 'gamma']
        for rhythm in expected_rhythms:
            self.assertIn(rhythm, result['rhythm_analysis'])

    def test_statistics_calculation(self):
        """Тест расчета статистики"""
        stats = self.analyzer.calculate_statistics(self.processed_data)

        expected_stats = ['mean', 'std', 'variance', 'kurtosis', 'skewness', 'rms']
        for stat in expected_stats:
            self.assertIn(stat, stats)

        # Проверка корректности значений
        self.assertIsInstance(stats['mean'], float)
        self.assertGreaterEqual(stats['std'], 0)

    def test_performance_monitoring(self):
        """Тест мониторинга производительности"""
        import time

        # Измеряем время выполнения
        start_time = time.time()
        result = self.analyzer.calculate_spectral_power(
            self.processed_data, self.sampling_rate
        )
        execution_time = time.time() - start_time

        # Проверяем что выполнение заняло разумное время
        self.assertLess(execution_time, 10.0)  # Не более 10 секунд

    def test_coherence_calculation(self):
        """Тест расчета когерентности"""
        result = self.analyzer.calculate_coherence(
            self.processed_data, 0, 1, self.sampling_rate
        )

        self.assertIn('frequencies', result)
        self.assertIn('coherence', result)
        self.assertIn('rhythm_coherence', result)

        # Проверка диапазона когерентности
        self.assertTrue(0 <= result['mean_coherence'] <= 1)


if __name__ == '__main__':
    # Запуск тестов
    unittest.main(verbosity=2)
