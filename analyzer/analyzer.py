import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.stats import entropy, kurtosis, skew

from utils.filter_validation import FilterValidator
from utils.performance import PerformanceMonitor


class EEGAnalyzer:

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()

        # Определение ритмов ЭЭГ
        self.rhythm_bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 100)
        }

    def get_rhythm_recommendations(self, analysis_result):
        rhythm_analysis = analysis_result['rhythm_analysis']
        dominant_rhythm = analysis_result['dominant_rhythm']
        spectral_entropy = analysis_result['spectral_entropy']

        recommendations = {
            'general': {},
            'rhythm_details': {},
            'specific_recommendations': []
        }

        # Анализ каждого ритма
        for rhythm, analysis in rhythm_analysis.items():
            relative_power = analysis['relative_power']

            # Определение состояния ритма
            state, recommendation = self.analyze_rhythm_state(rhythm, relative_power)

            recommendations['rhythm_details'][rhythm] = {
                'state': state,
                'recommendation': recommendation,
                'relative_power': relative_power
            }

        # Общие рекомендации
        recommendations['general'] = self.get_general_recommendations(
            dominant_rhythm, spectral_entropy, rhythm_analysis
        )

        # Специфические рекомендации
        recommendations['specific_recommendations'] = self.get_specific_recommendations(
            rhythm_analysis
        )

        return recommendations

    def analyze_rhythm_state(self, rhythm, relative_power):
        # Нормальные диапазоны мощности для разных ритмов (условные)
        normal_ranges = {
            'delta': (0.05, 0.25),
            'theta': (0.05, 0.15),
            'alpha': (0.10, 0.30),
            'beta': (0.15, 0.25),
            'gamma': (0.05, 0.15)
        }

        low, high = normal_ranges.get(rhythm, (0.05, 0.25))

        if relative_power < low:
            state = "НИЗКАЯ"
            recommendation = self.get_low_power_recommendation(rhythm)
        elif relative_power > high:
            state = "ВЫСОКАЯ"
            recommendation = self.get_high_power_recommendation(rhythm)
        else:
            state = "НОРМАЛЬНАЯ"
            recommendation = self.get_normal_recommendation(rhythm)

        return state, recommendation

    def get_low_power_recommendation(self, rhythm):
        recommendations = {
            'delta': "Рекомендуется улучшить качество сна и отдыха",
            'theta': "Возможно снижение креативности, рекомендуется медитация",
            'alpha': "Возможен стресс, рекомендуется релаксация и отдых",
            'beta': "Возможна рассеянность, рекомендуется концентрация и фокус",
            'gamma': "Возможны проблемы с когнитивными функциями, рекомендуется умственная активность"
        }
        return recommendations.get(rhythm, "Низкая мощность ритма")

    def get_high_power_recommendation(self, rhythm):
        recommendations = {
            'delta': "Глубокий сон или возможная патология, рекомендуется консультация специалиста",
            'theta': "Медитативное состояние или сонливость, рекомендуется активность",
            'alpha': "Глубокое расслабление, хорошее состояние для отдыха",
            'beta': "Высокая активность, возможна тревожность, рекомендуется релаксация",
            'gamma': "Интенсивная умственная деятельность, возможен стресс"
        }
        return recommendations.get(rhythm, "Высокая мощность ритма")


    def get_normal_recommendation(self, rhythm):
        recommendations = {
            'delta': "Нормальный сон и восстановление",
            'theta': "Хорошее состояние для творчества и интуиции",
            'alpha': "Расслабленное и спокойное состояние",
            'beta': "Активное бодрствование и концентрация",
            'gamma': "Нормальная когнитивная активность"
        }
        return recommendations.get(rhythm, "Нормальная мощность ритма")

    def get_general_recommendations(self, dominant_rhythm, spectral_entropy, rhythm_analysis):
        # Анализ доминирующего ритма
        dominant_power = rhythm_analysis[dominant_rhythm]['relative_power']

        if dominant_rhythm == 'alpha' and dominant_power > 0.25:
            summary = "Состояние глубокого расслабления и медитации"
            relaxation_level = "ВЫСОКИЙ"
        elif dominant_rhythm == 'beta' and dominant_power > 0.25:
            summary = "Активное бодрствование, возможна тревожность"
            relaxation_level = "НИЗКИЙ"
        elif dominant_rhythm == 'theta' and dominant_power > 0.15:
            summary = "Медитативное состояние или сонливость"
            relaxation_level = "СРЕДНИЙ"
        elif dominant_rhythm == 'delta' and dominant_power > 0.20:
            summary = "Состояние глубокого сна или отдыха"
            relaxation_level = "ОЧЕНЬ ВЫСОКИЙ"
        else:
            summary = "Сбалансированное состояние"
            relaxation_level = "НОРМАЛЬНЫЙ"

        return {
            'summary': summary,
            'dominant_rhythm': dominant_rhythm,
            'relaxation_level': relaxation_level,
            'spectral_entropy': spectral_entropy
        }

    def get_specific_recommendations(self, rhythm_analysis):
        recommendations = []

        # Анализ соотношения ритмов
        alpha_power = rhythm_analysis['alpha']['relative_power']
        beta_power = rhythm_analysis['beta']['relative_power']
        theta_power = rhythm_analysis['theta']['relative_power']

        # Соотношение альфа/бета (индекс релаксации)
        if alpha_power > 0 and beta_power > 0:
            alpha_beta_ratio = alpha_power / beta_power
            if alpha_beta_ratio > 2.0:
                recommendations.append("Высокий уровень релаксации - хорошее состояние для медитации")
            elif alpha_beta_ratio < 0.5:
                recommendations.append("Низкий уровень релаксации - рекомендуется снизить стресс")

        # Анализ тета-ритма
        if theta_power > 0.20:
            recommendations.append("Повышенная тета-активность - возможно состояние сонливости")
        elif theta_power < 0.05:
            recommendations.append("Пониженная тета-активность - возможно снижение креативности")

        # Общие рекомендации по балансу
        total_power = sum([analysis['relative_power'] for analysis in rhythm_analysis.values()])
        if abs(total_power - 1.0) > 0.1:
            recommendations.append("Обнаружен дисбаланс в распределении мощности ритмов")

        return recommendations

    def calculate_spectral_power(self, data, sampling_rate, channel_idx=0):
        with self.performance_monitor.measure_with_memory("Спектральный анализ"):
            if data.ndim == 2:
                signal_data = data[channel_idx]
            else:
                signal_data = data

            # Отслеживаем память входных данных
            self.performance_monitor.track_eeg_data("input_signal", signal_data)

            # БПФ
            n = len(signal_data)
            fft_result = fft(signal_data)
            frequencies = fftfreq(n, 1 / sampling_rate)

            # Отслеживаем память FFT результатов
            self.performance_monitor.track_eeg_data("fft_result", fft_result)
            self.performance_monitor.track_eeg_data("frequencies", frequencies)

            # Только положительные частоты
            positive_freq_idx = frequencies > 0
            frequencies = frequencies[positive_freq_idx]
            power_spectrum = np.abs(fft_result[positive_freq_idx]) ** 2 / n


            # Расчет мощности в ритмах
            rhythm_power = {}
            for rhythm, (low, high) in self.rhythm_bands.items():
                band_mask = (frequencies >= low) & (frequencies <= high)
                rhythm_power[rhythm] = np.sum(power_spectrum[band_mask])

            # Общая мощность
            total_power = np.sum(power_spectrum)

            # Относительная мощность
            relative_power = {rhythm: power / total_power
                              for rhythm, power in rhythm_power.items()}

            return {
                'frequencies': frequencies,
                'power_spectrum': power_spectrum,
                'rhythm_power': rhythm_power,
                'relative_power': relative_power,
                'total_power': total_power,
                'plot_data': power_spectrum,
                'peak_frequency': frequencies[np.argmax(power_spectrum)]
            }

    def detect_spikes(self, data, sampling_rate, threshold=3.0, channel_idx=0):
        with self.performance_monitor.measure("Детекция спайков"):
            if data.ndim == 2:
                signal_data = data[channel_idx]
            else:
                signal_data = data

            # Стандартное отклонение для определения порога
            std = np.std(signal_data)
            mean = np.mean(signal_data)

            # Поиск пиков
            peaks, properties = signal.find_peaks(
                np.abs(signal_data - mean),
                height=threshold * std,
                distance=sampling_rate * 0.1  # Минимальное расстояние 100 мс
            )

            # Характеристики спайков
            spike_times = peaks / sampling_rate
            spike_amplitudes = signal_data[peaks]

            return {
                'spike_times': spike_times,
                'spike_amplitudes': spike_amplitudes,
                'spike_count': len(peaks),
                'mean_amplitude': np.mean(spike_amplitudes),
                'spike_rate': len(peaks) / (len(signal_data) / sampling_rate)
            }

    def analyze_rhythms(self, data, sampling_rate, channel_idx=0):
        with self.performance_monitor.measure_with_memory("Анализ ритмов"):
            spectral_result = self.calculate_spectral_power(data, sampling_rate, channel_idx)

            if data.ndim == 2:
                signal_data = data[channel_idx]
            else:
                signal_data = data

            # Отслеживаем память исходного сигнала
            self.performance_monitor.track_eeg_data("rhythm_analysis_signal", signal_data)

            # Анализ для каждого ритма
            rhythm_analysis = {}
            for rhythm, (low_freq, high_freq) in self.rhythm_bands.items():
                # Фильтрация ритма
                filtered_signal = self.bandpass_filter_signal(
                    signal_data, sampling_rate, low_freq, high_freq
                )

                # Отслеживаем память отфильтрованного сигнала
                self.performance_monitor.track_eeg_data(f"filtered_{rhythm}", filtered_signal)

                # Характеристики ритма
                rhythm_analysis[rhythm] = {
                    'power': spectral_result['rhythm_power'][rhythm],
                    'relative_power': spectral_result['relative_power'][rhythm],
                    'mean_amplitude': np.mean(np.abs(filtered_signal)),
                    'dominant_frequency': self.find_dominant_frequency(
                        filtered_signal, sampling_rate, low_freq, high_freq
                    )
                }


            return {
                'rhythm_analysis': rhythm_analysis,
                'dominant_rhythm': max(spectral_result['relative_power'].items(),
                                       key=lambda x: x[1])[0],
                'spectral_entropy': self.calculate_spectral_entropy(
                    spectral_result['power_spectrum']
                ),
                # Include spectral data for visualization
                'frequencies': spectral_result['frequencies'],
                'power_spectrum': spectral_result['power_spectrum'],
                'rhythm_power': spectral_result['rhythm_power'],
                'relative_power': spectral_result['relative_power'],
                'total_power': spectral_result['total_power']
            }

    def bandpass_filter_signal(self, signal_data, sampling_rate, low_freq, high_freq):
        # Используем валидатор для проверки и коррекции параметров
        validator = FilterValidator()
        corrected_low, corrected_high, warnings = validator.validate_bandpass_params(
            low_freq, high_freq, sampling_rate
        )

        if warnings:
            print(f"Коррекция параметров фильтра для ритма {low_freq}-{high_freq} Гц:")
            for warning in warnings:
                print(f"   • {warning}")

        nyquist = sampling_rate / 2
        low = corrected_low / nyquist
        high = corrected_high / nyquist

        try:
            b, a = signal.butter(4, [low, high], btype='band')
            return signal.filtfilt(b, a, signal_data)
        except Exception as e:
            raise ValueError(f"Ошибка фильтрации сигнала: {e}. Частоты: low={low:.4f}, high={high:.4f}")

    def find_dominant_frequency(self, signal_data, sampling_rate, low_freq, high_freq):
        n = len(signal_data)
        fft_result = fft(signal_data)
        frequencies = fftfreq(n, 1 / sampling_rate)

        # Только положительные частоты в диапазоне
        freq_mask = (frequencies >= low_freq) & (frequencies <= high_freq) & (frequencies > 0)
        valid_freq = frequencies[freq_mask]
        valid_power = np.abs(fft_result[freq_mask]) ** 2

        if len(valid_freq) == 0:
            return 0

        return valid_freq[np.argmax(valid_power)]

    def calculate_spectral_entropy(self, power_spectrum):
        # Нормализация спектра мощности
        normalized_spectrum = power_spectrum / np.sum(power_spectrum)

        # Расчет энтропии
        return entropy(normalized_spectrum)

    def calculate_coherence(self, data, channel1, channel2, sampling_rate):
        with self.performance_monitor.measure("Когерентность"):
            if data.ndim != 2:
                raise ValueError("Для когерентности нужны многоканальные данные")

            f, Cxy = signal.coherence(data[channel1], data[channel2],
                                      fs=sampling_rate, nperseg=1024)

            # Средняя когерентность в основных ритмах
            rhythm_coherence = {}
            for rhythm, (low, high) in self.rhythm_bands.items():
                band_mask = (f >= low) & (f <= high)
                rhythm_coherence[rhythm] = np.mean(Cxy[band_mask])

            return {
                'frequencies': f,
                'coherence': Cxy,
                'rhythm_coherence': rhythm_coherence,
                'mean_coherence': np.mean(Cxy)
            }

    def calculate_statistics(self, data):
        with self.performance_monitor.measure("Статистика"):
            if data.ndim == 2:
                # Для многоканальных данных - усредняем по каналам
                flat_data = data.flatten()
            else:
                flat_data = data

            return {
                'mean': np.mean(flat_data),
                'std': np.std(flat_data),
                'variance': np.var(flat_data),
                'kurtosis': kurtosis(flat_data),
                'skewness': skew(flat_data),
                'rms': np.sqrt(np.mean(flat_data ** 2)),
                'max_amplitude': np.max(np.abs(flat_data)),
                'dynamic_range': np.max(flat_data) - np.min(flat_data)
            }


    def get_eeg_performance_report(self):
        return self.performance_monitor.get_detailed_summary()

    def get_eeg_memory_usage(self):
        return self.performance_monitor.get_eeg_memory_usage()

    def clear_performance_data(self):
        self.performance_monitor.clear_tracking()
