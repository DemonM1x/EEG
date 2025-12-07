import signal

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from utils.performance import PerformanceMonitor


class EEGVisualizer:

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        plt.style.use('seaborn-v0_8')

    def plot_raw_signal(self, data, sampling_rate, channel_names, fig=None):
        with self.performance_monitor.measure("Визуализация сигнала"):
            if fig is None:
                fig = plt.figure(figsize=(12, 8))

            n_channels = min(data.shape[0], 8)  # Ограничиваем количество каналов
            time = np.arange(data.shape[1]) / sampling_rate

            # Создание субплотов
            gs = GridSpec(n_channels, 1, figure=fig)
            fig.clf()

            for i in range(n_channels):
                ax = fig.add_subplot(gs[i, 0])
                ax.plot(time, data[i], 'b', linewidth=0.5)
                ax.set_ylabel(f'{channel_names[i]}\n(мкВ)', rotation=0, ha='right')
                ax.grid(True, alpha=0.3)

                if i < n_channels - 1:
                    ax.set_xticklabels([])
                else:
                    ax.set_xlabel('Время (с)')

            fig.suptitle('Сигналы ЭЭГ по каналам', fontsize=14)
            fig.tight_layout()

            return fig

    def plot_spectrum(self, data, sampling_rate, channel_names, fig=None):
        with self.performance_monitor.measure("Визуализация спектра"):
            if fig is None:
                fig = plt.figure(figsize=(12, 8))

            from scipy.fft import fft, fftfreq

            n_channels = min(data.shape[0], 6)
            fig.clf()

            for i in range(n_channels):
                ax = fig.add_subplot(2, 3, i + 1)

                # Расчет спектра
                n = len(data[i])
                fft_result = fft(data[i])
                frequencies = fftfreq(n, 1 / sampling_rate)

                positive_freq_idx = frequencies > 0
                freqs = frequencies[positive_freq_idx]
                power = np.abs(fft_result[positive_freq_idx]) ** 2 / n

                ax.semilogy(freqs, power, 'r', linewidth=1)
                ax.set_xlabel('Частота (Гц)')
                ax.set_ylabel('Мощность')
                ax.set_title(f'{channel_names[i]}')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 40)

            fig.suptitle('Спектры мощности по каналам', fontsize=14)
            fig.tight_layout()

            return fig

    def plot_topomap(self, data, channel_names, fig=None):
        with self.performance_monitor.measure("Топографическая карта"):
            if fig is None:
                fig = plt.figure(figsize=(10, 8))

            fig.clf()
            ax = fig.add_subplot(111)

            # Средняя мощность по каналам
            channel_power = np.mean(data ** 2, axis=1)

            im = ax.imshow([channel_power], cmap='RdBu_r', aspect='auto')
            ax.set_yticks([0])
            ax.set_yticklabels(['Мощность'])
            ax.set_xticks(range(len(channel_names)))
            ax.set_xticklabels(channel_names, rotation=45)
            plt.colorbar(im, ax=ax, label='Мощность (мкВ²)')

            ax.set_title('Топографическое распределение мощности')

            return fig

    def plot_spectrogram(self, data, sampling_rate, channel_idx=0, fig=None):
        with self.performance_monitor.measure("Спектрограмма"):
            if fig is None:
                fig = plt.figure(figsize=(12, 6))

            fig.clf()
            ax = fig.add_subplot(111)

            f, t, Sxx = signal.spectrogram(data[channel_idx], sampling_rate,
                                           nperseg=256, noverlap=128)

            im = ax.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')
            ax.set_ylabel('Частота [Гц]')
            ax.set_xlabel('Время [с]')
            ax.set_ylim(0, 40)
            plt.colorbar(im, ax=ax, label='Мощность [дБ]')

            ax.set_title('Спектрограмма ЭЭГ')

            return fig

    def plot_rhythm_analysis(self, analysis_results, fig=None):
        with self.performance_monitor.measure("Визуализация ритмов"):
            if fig is None:
                fig = plt.figure(figsize=(10, 8))

            fig.clf()

            # График относительной мощности
            ax1 = fig.add_subplot(211)
            rhythms = list(analysis_results['relative_power'].keys())
            powers = list(analysis_results['relative_power'].values())

            bars = ax1.bar(rhythms, powers, color=['blue', 'green', 'red', 'orange', 'purple'])
            ax1.set_ylabel('Относительная мощность')
            ax1.set_title('Распределение мощности по ритмам')

            # Добавление значений на столбцы
            for bar, power in zip(bars, powers):
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                         f'{power:.3f}', ha='center', va='bottom')

            # График абсолютной мощности
            ax2 = fig.add_subplot(212)
            abs_powers = list(analysis_results['rhythm_power'].values())

            bars = ax2.bar(rhythms, abs_powers, color=['blue', 'green', 'red', 'orange', 'purple'])
            ax2.set_ylabel('Абсолютная мощность')
            ax2.set_xlabel('Ритмы ЭЭГ')
            ax2.set_title('Абсолютная мощность ритмов')

            fig.tight_layout()

            return fig
