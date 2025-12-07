import numpy as np
import pywt
from scipy import signal
from scipy.signal import butter, filtfilt, iirnotch

from utils.filter_validation import FilterValidator
from utils.performance import PerformanceMonitor


class EEGPreprocessor:

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()

    def apply_filters(self, data, sampling_rate, low_freq=1.0, high_freq=40.0, notch_freq=50.0):
        with self.performance_monitor.measure("Фильтрация"):
            # Валидация и автокоррекция параметров фильтра
            validator = FilterValidator()

            # Проверка и коррекция параметров полосового фильтра
            corrected_low, corrected_high, bp_warnings = validator.validate_bandpass_params(
                low_freq, high_freq, sampling_rate
            )

            # Проверка и коррекция параметров notch фильтра
            corrected_notch, notch_warnings = validator.validate_notch_params(
                notch_freq, sampling_rate
            )

            # Вывод предупреждений если параметры были скорректированы
            all_warnings = bp_warnings + notch_warnings
            if all_warnings:
                print("⚠️  АВТОКОРРЕКЦИЯ ПАРАМЕТРОВ ФИЛЬТРА:")
                for warning in all_warnings:
                    print(f"   • {warning}")
                print()

            # Полосовой фильтр с скорректированными параметрами
            data = self.bandpass_filter(data, sampling_rate, corrected_low, corrected_high)

            # Notch фильтр для сети
            if corrected_notch > 0:
                data = self.notch_filter(data, sampling_rate, corrected_notch)

            return data

    def bandpass_filter(self, data, sampling_rate, low_freq, high_freq):
        nyquist = sampling_rate / 2

        # Проверка входных параметров
        if low_freq <= 0:
            raise ValueError(f"Нижняя частота должна быть больше 0, получено: {low_freq} Гц")

        if high_freq >= nyquist:
            raise ValueError(f"Верхняя частота ({high_freq} Гц) должна быть меньше частоты Найквиста ({nyquist} Гц)")

        if low_freq >= high_freq:
            raise ValueError(f"Нижняя частота ({low_freq} Гц) должна быть меньше верхней ({high_freq} Гц)")

        # Нормализация частот
        low = low_freq / nyquist
        high = high_freq / nyquist

        # Дополнительная проверка нормализованных частот
        if low <= 0 or low >= 1:
            raise ValueError(f"Нормализованная нижняя частота {low:.4f} вне допустимого диапазона (0, 1)")

        if high <= 0 or high >= 1:
            raise ValueError(f"Нормализованная верхняя частота {high:.4f} вне допустимого диапазона (0, 1)")

        # Убеждаемся, что частоты не слишком близки к границам
        if low < 0.001:
            low = 0.001
            print(f"Предупреждение: нижняя частота слишком мала, установлена в {low * nyquist:.2f} Гц")

        if high > 0.999:
            high = 0.999
            print(f"Предупреждение: верхняя частота слишком велика, установлена в {high * nyquist:.2f} Гц")

        try:
            b, a = butter(4, [low, high], btype='band')
        except Exception as e:
            raise ValueError(f"Ошибка создания фильтра: {e}. Частоты: low={low:.4f}, high={high:.4f}")

        # Применяем фильтр к каждому каналу
        filtered_data = np.zeros_like(data)
        for i in range(data.shape[0]):
            try:
                filtered_data[i] = filtfilt(b, a, data[i])
            except Exception as e:
                raise ValueError(f"Ошибка применения фильтра к каналу {i}: {e}")

        return filtered_data

    def notch_filter(self, data, sampling_rate, notch_freq, quality=30):
        nyquist = sampling_rate / 2

        # Проверка входных параметров
        if notch_freq <= 0:
            raise ValueError(f"Частота notch фильтра должна быть больше 0, получено: {notch_freq} Гц")

        if notch_freq >= nyquist:
            raise ValueError(
                f"Частота notch фильтра ({notch_freq} Гц) должна быть меньше частоты Найквиста ({nyquist} Гц)")

        # Нормализация частоты
        freq = notch_freq / nyquist

        # Проверка нормализованной частоты
        if freq <= 0 or freq >= 1:
            raise ValueError(f"Нормализованная частота notch фильтра {freq:.4f} вне допустимого диапазона (0, 1)")

        # Убеждаемся, что частота не слишком близка к границам
        if freq < 0.001:
            freq = 0.001
            print(f"Предупреждение: частота notch фильтра слишком мала, установлена в {freq * nyquist:.2f} Гц")

        if freq > 0.999:
            freq = 0.999
            print(f"Предупреждение: частота notch фильтра слишком велика, установлена в {freq * nyquist:.2f} Гц")

        try:
            b, a = iirnotch(freq, quality)
        except Exception as e:
            raise ValueError(f"Ошибка создания notch фильтра: {e}. Частота: {freq:.4f}")

        filtered_data = np.zeros_like(data)
        for i in range(data.shape[0]):
            try:
                filtered_data[i] = filtfilt(b, a, data[i])
            except Exception as e:
                raise ValueError(f"Ошибка применения notch фильтра к каналу {i}: {e}")

        return filtered_data

    def detrend_signal(self, data):
        with self.performance_monitor.measure("Детрендирование"):
            detrended_data = np.zeros_like(data)
            for i in range(data.shape[0]):
                detrended_data[i] = signal.detrend(data[i])

            return detrended_data

    def remove_dc_offset(self, data):
        return data - np.mean(data, axis=1, keepdims=True)

    def remove_artifacts(self, data, threshold=3.0):
        with self.performance_monitor.measure("Удаление артефактов"):
            cleaned_data = data.copy()

            for i in range(data.shape[0]):
                channel_data = data[i]
                std = np.std(channel_data)
                mean = np.mean(channel_data)

                # Находим выбросы
                outliers = np.abs(channel_data - mean) > threshold * std

                # Заменяем выбросы интерполированными значениями
                if np.any(outliers):
                    indices = np.arange(len(channel_data))
                    cleaned_data[i] = np.interp(indices,
                                                indices[~outliers],
                                                channel_data[~outliers])

            return cleaned_data

    def wavelet_denoising(self, data, wavelet='db4', level=1):
        with self.performance_monitor.measure("Вейвлет-денизинг"):
            denoised_data = np.zeros_like(data)

            for i in range(data.shape[0]):
                # Вейвлет-разложение
                coeffs = pywt.wavedec(data[i], wavelet, level=level)

                # Пороговая обработка коэффициентов
                sigma = np.median(np.abs(coeffs[-level])) / 0.6745
                uthresh = sigma * np.sqrt(2 * np.log(len(data[i])))
                coeffs = [pywt.threshold(c, uthresh, 'soft') for c in coeffs]

                # Обратное вейвлет-преобразование
                denoised_data[i] = pywt.waverec(coeffs, wavelet)

            return denoised_data

    def ica_artifact_removal(self, data, n_components=None):
        try:
            from sklearn.decomposition import FastICA

            if n_components is None:
                n_components = min(data.shape[0], 10)

            ica = FastICA(n_components=n_components, random_state=42)
            components = ica.fit_transform(data.T)

            return data

        except ImportError:
            print("scikit-learn не установлен. Пропускаем ICA.")
            return data

    def normalize_data(self, data, method='zscore'):
        if method == 'zscore':
            return (data - np.mean(data, axis=1, keepdims=True)) / np.std(data, axis=1, keepdims=True)
        elif method == 'minmax':
            return (data - np.min(data, axis=1, keepdims=True)) / (
                    np.max(data, axis=1, keepdims=True) - np.min(data, axis=1, keepdims=True))
        else:
            return data
