import os
from datetime import time

import mne
import numpy as np
import pandas as pd
import pyedflib
from scipy import signal

from utils.performance import PerformanceMonitor


class EEGDataLoader:

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()

    def load_data(self, file_path):
        with self.performance_monitor.measure("Загрузка данных"):
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension == '.edf':
                return self.load_edf(file_path)
            elif file_extension in ['.csv', '.txt']:
                return self.load_csv(file_path)
            elif file_extension == '.set':
                return self.load_eeglab(file_path)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")

    def load_edf(self, file_path):
        try:
            with pyedflib.EdfReader(file_path) as f:
                n_channels = f.signals_in_file
                channel_names = f.getSignalLabels()
                sampling_rate = f.getSampleFrequency(0)

                # Чтение данных
                data = np.zeros((n_channels, f.getNSamples()[0]))
                for i in range(n_channels):
                    data[i, :] = f.readSignal(i)

            # Автоматическая проверка и коррекция данных
            data = self.auto_correct_data(data)

            return data, sampling_rate, channel_names

        except Exception as e:
            raise Exception(f"Ошибка загрузки EDF: {e}")

    def load_csv(self, file_path):
        try:
            # Попробуем разные разделители
            separators = [',', ';', '\t', ' ']
            df = None

            for sep in separators:
                try:
                    df = pd.read_csv(file_path, sep=sep, engine='python')
                    if df.shape[1] > 1:  # Если есть несколько колонок
                        break
                except:
                    continue

            if df is None or df.empty:
                raise ValueError("Не удалось прочитать CSV файл")

            # Автоматическое определение структуры данных
            data, sampling_rate, channel_names = self.parse_csv_structure(df)

            # Автоматическая проверка и коррекция данных
            data = self.auto_correct_data(data)

            return data, sampling_rate, channel_names

        except Exception as e:
            raise Exception(f"Ошибка загрузки CSV: {e}")

    def load_eeglab(self, file_path):
        try:
            raw = mne.io.read_raw_eeglab(file_path, preload=True)
            data = raw.get_data()
            sampling_rate = raw.info['sfreq']
            channel_names = [ch_name for ch_name in raw.info['ch_names']]

            # Автоматическая проверка и коррекция данных
            data = self.auto_correct_data(data)

            return data, sampling_rate, channel_names

        except Exception as e:
            raise Exception(f"Ошибка загрузки EEGLAB: {e}")

    def parse_csv_structure(self, df):
        # Удаляем возможные пустые колонки
        df = df.dropna(axis=1, how='all')

        # Ищем колонку с временем
        time_columns = ['time', 'Time', 'TIME', 't', 'T', 'время', 'Время']
        time_col = None

        for col in time_columns:
            if col in df.columns:
                time_col = col
                break

        if time_col:
            # Если есть колонка времени
            data_columns = [col for col in df.columns if col != time_col]
            data = df[data_columns].values.T
            time_values = df[time_col].values

            # Вычисляем частоту дискретизации
            if len(time_values) > 1:
                time_diff = np.diff(time_values)
                sampling_rate = 1 / np.mean(time_diff)
            else:
                sampling_rate = 250  # По умолчанию
        else:
            # Если нет колонки времени, считаем что это просто данные
            data = df.values.T
            sampling_rate = 250  # Частота по умолчанию

        # Генерация имен каналов
        if data.shape[0] <= len(df.columns):
            channel_names = list(df.columns)[:data.shape[0]]
        else:
            channel_names = [f'Channel_{i:02d}' for i in range(data.shape[0])]

        return data, sampling_rate, channel_names

    def auto_correct_data(self, data):
        corrected_data = data.copy()

        # Удаление NaN и Inf значений
        corrected_data = np.nan_to_num(corrected_data, nan=0.0, posinf=0.0, neginf=0.0)

        # Проверка на постоянное смещение и тренд
        for i in range(corrected_data.shape[0]):
            channel_data = corrected_data[i]

            # Удаление линейного тренда
            if len(channel_data) > 1:
                corrected_data[i] = signal.detrend(channel_data)

            # Удаление постоянного смещения
            corrected_data[i] = corrected_data[i] - np.mean(corrected_data[i])

        return corrected_data

    def generate_test_data(self, duration=10, sampling_rate=250, n_channels=8):
        n_samples = int(duration * sampling_rate)
        time = np.linspace(0, duration, n_samples)

        data = np.zeros((n_channels, n_samples))
        channel_names = [f'EEG_{i:03d}' for i in range(n_channels)]

        # Генерация разных ритмов
        rhythms = [
            (2, 4, 50),  # Delta
            (4, 8, 40),  # Theta
            (8, 13, 60),  # Alpha
            (13, 30, 30),  # Beta
            (30, 100, 20),  # Gamma
            (2, 30, 35),  # Mixed
            (8, 12, 55),  # Alpha
            (15, 25, 25)  # Beta
        ]

        for i in range(n_channels):
            low_freq, high_freq, amplitude = rhythms[i % len(rhythms)]

            # Случайная центральная частота в диапазоне
            center_freq = np.random.uniform(low_freq, high_freq)

            # Основной ритм
            main_signal = amplitude * np.sin(2 * np.pi * center_freq * time)

            # Добавляем гармоники
            for harmonic in range(2, 4):
                if center_freq * harmonic <= high_freq:
                    harmonic_amp = amplitude / harmonic
                    main_signal += harmonic_amp * np.sin(2 * np.pi * center_freq * harmonic * time)

            # Шум
            noise = 5 * np.random.normal(0, 1, n_samples)

            # Случайные артефакты
            artifacts = np.zeros(n_samples)
            if i % 3 == 0:  # Добавляем артефакты в некоторые каналы
                n_artifacts = np.random.randint(2, 6)
                artifact_times = np.random.randint(0, n_samples, n_artifacts)
                artifacts[artifact_times] = 80 * np.random.randn(n_artifacts)

            data[i, :] = main_signal + noise + artifacts

        return data, sampling_rate, channel_names

    def get_file_info(self, file_path):
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size / (1024 * 1024)

        return {
            'file_name': os.path.basename(file_path),
            'file_size_mb': round(file_size, 2),
            'file_extension': os.path.splitext(file_path)[1].lower(),
            'modified_time': time.ctime(file_stats.st_mtime)
        }
