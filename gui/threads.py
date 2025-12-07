import time

import numpy as np
import serial
from PyQt5.QtCore import QThread, pyqtSignal
from scipy import signal as sp_signal


class DataLoadThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(tuple)
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)

    def __init__(self, file_path, data_loader):
        super().__init__()
        self.file_path = file_path
        self.data_loader = data_loader

    def run(self):
        try:
            self.info_signal.emit("Начало загрузки данных...")
            data, sampling_rate, channel_names = self.data_loader.load_data(self.file_path)
            self.info_signal.emit("Данные успешно загружены!")
            self.result_signal.emit((data, sampling_rate, channel_names))
        except Exception as e:
            self.error_signal.emit(str(e))


class ProcessingThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)

    def __init__(self, preprocessor, data, sampling_rate, processing_params):
        super().__init__()
        self.preprocessor = preprocessor
        self.data = data
        self.sampling_rate = sampling_rate
        self.processing_params = processing_params

    def run(self):
        try:
            self.info_signal.emit("Начало обработки сигнала...")
            processed_data = self.preprocessor.apply_filters(self.data, self.sampling_rate,
                                                             self.processing_params['low_freq'],
                                                             self.processing_params['high_freq'],
                                                             self.processing_params['notch_freq'])
            if self.processing_params['detrend']:
                self.info_signal.emit("Удаление тренда...")
                processed_data = self.preprocessor.detrend_signal(processed_data)
            if self.processing_params['remove_dc']:
                self.info_signal.emit("Удаление постоянной составляющей...")
                processed_data = self.preprocessor.remove_dc_offset(processed_data)
            if self.processing_params['remove_artifacts']:
                self.info_signal.emit("Удаление артефактов...")
                processed_data = self.preprocessor.remove_artifacts(processed_data,
                                                                    self.processing_params['artifact_threshold'])
            self.info_signal.emit("Обработка завершена!")
            self.result_signal.emit(processed_data)
        except Exception as e:
            self.error_signal.emit(str(e))


class AnalysisThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)

    def __init__(self, analyzer, data, sampling_rate, channel_idx):
        super().__init__()
        self.analyzer = analyzer
        self.data = data
        self.sampling_rate = sampling_rate
        self.channel_idx = channel_idx

    def run(self):
        try:
            self.info_signal.emit("Анализ ритмов ЭЭГ...")
            analysis_result = self.analyzer.analyze_rhythms(self.data, self.sampling_rate, self.channel_idx)
            recommendations = self.analyzer.get_rhythm_recommendations(analysis_result)
            result = {'analysis': analysis_result, 'recommendations': recommendations, 'channel_idx': self.channel_idx}
            self.info_signal.emit("Анализ завершен!")
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class SingleRhythmAnalysisThread(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)

    def __init__(self, analyzer, data, sampling_rate, channel_idx, rhythm_name):
        super().__init__()
        self.analyzer = analyzer
        self.data = data
        self.sampling_rate = sampling_rate
        self.channel_idx = channel_idx
        self.rhythm_name = rhythm_name

    def run(self):
        try:
            self.info_signal.emit(f"Анализ ритма {self.rhythm_name}...")
            rhythm_bands = {'дельта': (0.5, 4), 'тета': (4, 8), 'альфа': (8, 13), 'бета': (13, 30), 'гамма': (30, 50)}
            if self.rhythm_name not in rhythm_bands:
                raise ValueError(f"Неизвестный ритм: {self.rhythm_name}")
            low_freq, high_freq = rhythm_bands[self.rhythm_name]
            channel_data = self.data[self.channel_idx]
            freqs, psd = sp_signal.welch(channel_data, fs=self.sampling_rate, nperseg=min(256, len(channel_data)))
            freq_mask = (freqs >= low_freq) & (freqs <= high_freq)
            rhythm_freqs = freqs[freq_mask]
            rhythm_psd = psd[freq_mask]
            rhythm_power = np.trapz(rhythm_psd, rhythm_freqs)
            total_power = np.trapz(psd, freqs)
            relative_power = rhythm_power / total_power if total_power > 0 else 0
            peak_idx = np.argmax(rhythm_psd)
            peak_freq = rhythm_freqs[peak_idx]
            # Добавляем информацию для визуализации
            result = {
                'rhythm_name': self.rhythm_name,
                'channel_idx': self.channel_idx,
                'freqs': rhythm_freqs,
                'psd': rhythm_psd,
                'power': rhythm_power,
                'relative_power': relative_power,
                'peak_freq': peak_freq,
                'freq_range': (low_freq, high_freq),
                # Добавляем полный спектр для визуализации
                'frequencies': freqs,
                'power_spectrum': psd,
                # Добавляем информацию о ритмах для графика
                'rhythm_powers': {self.rhythm_name: rhythm_power},
                'rhythm_analysis': {
                    self.rhythm_name: {
                        'power': rhythm_power,
                        'relative_power': relative_power,
                        'dominant_frequency': peak_freq,
                        'frequency_range': (low_freq, high_freq)
                    }
                }
            }
            self.info_signal.emit(f"Анализ ритма {self.rhythm_name} завершен!")
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class SerialRecordingThread(QThread):
    data_signal = pyqtSignal(np.ndarray)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, port, baudrate, recording_time, sampling_rate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.recording_time = recording_time
        self.sampling_rate = sampling_rate
        self.is_recording = False
        self.serial_conn = None

    def run(self):
        try:
            self.status_signal.emit(f"Подключение к {self.port}...")
            self.serial_conn = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
            if not self.serial_conn.is_open:
                self.error_signal.emit(f"Не удалось открыть порт {self.port}")
                return
            self.status_signal.emit("Подключение установлено. Начало записи...")
            self.is_recording = True
            data_buffer = []
            start_time = time.time()
            while self.is_recording and (time.time() - start_time) < self.recording_time:
                if self.serial_conn.in_waiting > 0:
                    try:
                        line = self.serial_conn.readline().decode('utf-8').strip()
                        if line:
                            values = self.parse_serial_data(line)
                            if values is not None:
                                data_buffer.append(values)
                    except Exception as e:
                        self.error_signal.emit(f"Ошибка чтения данных: {e}")
                        break
                elapsed = time.time() - start_time
                progress = min(100, int((elapsed / self.recording_time) * 100))
                self.status_signal.emit(f"Запись... {progress}% ({elapsed:.1f}с / {self.recording_time}с)")
                time.sleep(0.01)
            if data_buffer:
                data_array = np.array(data_buffer).T
                self.data_signal.emit(data_array)
                self.status_signal.emit(f"Запись завершена. Получено {len(data_buffer)} samples")
            else:
                self.error_signal.emit("Не получено данных за время записи")
        except Exception as e:
            self.error_signal.emit(f"Ошибка записи: {e}")
        finally:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            self.is_recording = False

    def parse_serial_data(self, line):
        try:
            if ',' in line:
                values = []
                parts = line.split(',')
                for part in parts:
                    if ':' in part:
                        value_str = part.split(':')[1]
                        values.append(float(value_str))
                return values if values else None
            else:
                return [float(line)]
        except:
            return None

    def stop_recording(self):
        self.is_recording = False
