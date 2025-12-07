import gc
import os
import sys
import time
from typing import Any, Dict

import numpy as np
import psutil


class PerformanceMonitor:

    def __init__(self):
        self.measurements = {}
        self.memory_snapshots = {}
        self.tracked_objects = {}

    def measure(self, operation_name):
        return self.MeasurementContext(self, operation_name)

    class MeasurementContext:
        def __init__(self, monitor, name):
            self.monitor = monitor
            self.name = name

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            execution_time = time.time() - self.start_time

            if self.name not in self.monitor.measurements:
                self.monitor.measurements[self.name] = []

            self.monitor.measurements[self.name].append({
                'time': execution_time,
                'timestamp': time.time()
            })

    def get_system_info(self):
        process = psutil.Process(os.getpid())

        return {
            'memory_mb': process.memory_info().rss / 1024 / 1024
        }

    def get_summary(self):
        if not self.measurements:
            return "Измерения не проводились"

        total_time = sum(
            sum(m['time'] for m in measurements)
            for measurements in self.measurements.values()
        )

        current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        summary = f"Время обработки: {total_time:.2f} сек\n"
        summary += f"Использование памяти: {current_memory:.1f} MB"

        return summary

    def get_object_memory_size(self, obj: Any) -> float:
        return sys.getsizeof(obj) / 1024 / 1024

    def get_numpy_array_memory(self, array: np.ndarray) -> float:
        return array.nbytes / 1024 / 1024

    def track_eeg_data(self, data_name: str, data: Any) -> None:
        if isinstance(data, np.ndarray):
            memory_mb = self.get_numpy_array_memory(data)
            data_type = f"numpy array {data.shape} {data.dtype}"
        else:
            memory_mb = self.get_object_memory_size(data)
            data_type = type(data).__name__

        self.tracked_objects[data_name] = {
            'memory_mb': memory_mb,
            'type': data_type,
            'timestamp': time.time()
        }

    def measure_with_memory(self, operation_name: str):
        return self.MemoryMeasurementContext(self, operation_name)

    class MemoryMeasurementContext:
        def __init__(self, monitor, name):
            self.monitor = monitor
            self.name = name
            self.memory_before = 0
            self.memory_after = 0

        def __enter__(self):
            gc.collect()  # Принудительная сборка мусора для точности
            self.start_time = time.time()
            process = psutil.Process(os.getpid())
            self.memory_before = process.memory_info().rss / 1024 / 1024
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            execution_time = time.time() - self.start_time
            gc.collect()
            process = psutil.Process(os.getpid())
            self.memory_after = process.memory_info().rss / 1024 / 1024
            memory_delta = self.memory_after - self.memory_before

            if self.name not in self.monitor.measurements:
                self.monitor.measurements[self.name] = []

            self.monitor.measurements[self.name].append({
                'time': execution_time,
                'memory_before_mb': self.memory_before,
                'memory_after_mb': self.memory_after,
                'memory_delta_mb': memory_delta,
                'timestamp': time.time()
            })

    def get_eeg_memory_usage(self) -> Dict[str, float]:
        return {name: info['memory_mb'] for name, info in self.tracked_objects.items()}

    def get_detailed_summary(self) -> str:
        if not self.measurements and not self.tracked_objects:
            return "Измерения не проводились"

        summary = []

        # Время выполнения операций
        if self.measurements:
            summary.append("=== ВРЕМЯ ВЫПОЛНЕНИЯ ===")
            total_time = 0
            for op_name, measurements in self.measurements.items():
                op_time = sum(m['time'] for m in measurements)
                total_time += op_time
                avg_time = op_time / len(measurements)
                summary.append(f"{op_name}: {op_time:.3f}с (среднее: {avg_time:.3f}с, вызовов: {len(measurements)})")
            summary.append(f"Общее время: {total_time:.3f}с")
            summary.append("")

        # Использование памяти EEG объектами
        if self.tracked_objects:
            summary.append("=== ПАМЯТЬ EEG ОБЪЕКТОВ ===")
            total_eeg_memory = 0
            for name, info in self.tracked_objects.items():
                memory_mb = info['memory_mb']
                total_eeg_memory += memory_mb
                summary.append(f"{name}: {memory_mb:.2f} МБ ({info['type']})")
            summary.append(f"Общая память EEG данных: {total_eeg_memory:.2f} МБ")
            summary.append("")

        # Изменения памяти по операциям
        memory_ops = {name: measurements for name, measurements in self.measurements.items()
                      if any('memory_delta_mb' in m for m in measurements)}
        if memory_ops:
            summary.append("=== ИЗМЕНЕНИЯ ПАМЯТИ ПО ОПЕРАЦИЯМ ===")
            for op_name, measurements in memory_ops.items():
                memory_deltas = [m.get('memory_delta_mb', 0) for m in measurements]
                total_delta = sum(memory_deltas)
                avg_delta = total_delta / len(memory_deltas)
                summary.append(f"{op_name}: {total_delta:+.2f} МБ (среднее: {avg_delta:+.2f} МБ)")

        # Общая информация о системе
        current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        summary.append(f"Текущая память процесса: {current_memory:.1f} МБ")

        return "\n".join(summary)

    def clear_tracking(self):
        self.measurements.clear()
        self.tracked_objects.clear()
        self.memory_snapshots.clear()

    def take_system_snapshot(self, snapshot_name: str = None):
        if snapshot_name is None:
            snapshot_name = f"snapshot_{len(self.memory_snapshots)}"

        process = psutil.Process(os.getpid())
        self.memory_snapshots[snapshot_name] = {
            'timestamp': time.time(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'tracked_objects_count': len(self.tracked_objects),
            'total_eeg_memory': sum(info['memory_mb'] for info in self.tracked_objects.values())
        }

    def get_rhythm_analysis_report(self) -> str:
        rhythm_operations = [
            "Анализ ритмов",
            "Визуализация ритмов",
            "Анализ одного ритма",
            "Расчет спектральной мощности",
            "Анализ альфа-ритма",
            "Анализ бета-ритма",
            "Анализ гамма-ритма",
            "Анализ дельта-ритма",
            "Анализ тета-ритма"
        ]

        if not self.measurements:
            return "Анализ ритмов не проводился"

        summary = []
        summary.append("=== ОТЧЕТ ПО АНАЛИЗУ РИТМОВ ===")
        summary.append("")

        # Фильтруем только операции анализа ритмов
        rhythm_measurements = {}
        for op_name, measurements in self.measurements.items():
            if any(rhythm_op.lower() in op_name.lower() for rhythm_op in rhythm_operations):
                rhythm_measurements[op_name] = measurements

        if not rhythm_measurements:
            return "Операции анализа ритмов не найдены"

        # Время выполнения анализа ритмов
        summary.append("ВРЕМЯ ВЫПОЛНЕНИЯ:")
        total_rhythm_time = 0
        for op_name, measurements in rhythm_measurements.items():
            op_time = sum(m['time'] for m in measurements)
            total_rhythm_time += op_time
            avg_time = op_time / len(measurements)
            summary.append(f"• {op_name}: {op_time:.3f}с (среднее: {avg_time:.3f}с)")

        summary.append(f"• Общее время анализа ритмов: {total_rhythm_time:.3f}с")
        summary.append("")

        # Использование памяти при анализе ритмов
        memory_ops = {name: measurements for name, measurements in rhythm_measurements.items()
                      if any('memory_delta_mb' in m for m in measurements)}

        if memory_ops:
            summary.append("ИСПОЛЬЗОВАНИЕ ПАМЯТИ:")
            total_memory_delta = 0
            max_memory_usage = 0

            for op_name, measurements in memory_ops.items():
                memory_deltas = [m.get('memory_delta_mb', 0) for m in measurements]
                memory_peaks = [m.get('memory_after_mb', 0) for m in measurements]

                total_delta = sum(memory_deltas)
                avg_delta = total_delta / len(memory_deltas)
                max_peak = max(memory_peaks) if memory_peaks else 0

                total_memory_delta += total_delta
                max_memory_usage = max(max_memory_usage, max_peak)

                summary.append(f"• {op_name}: {total_delta:.2f} МБ (пик: {max_peak:.1f} МБ)")

            summary.append(f"• Общее изменение памяти: {total_memory_delta:.2f} МБ")
            summary.append(f"• Общее использование: {max_memory_usage:.1f} МБ")
        else:
            summary.append("ИСПОЛЬЗОВАНИЕ ПАМЯТИ:")
            summary.append("• Детальные данные о памяти недоступны")

            # Показываем общую информацию о памяти
            current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            summary.append(f"• Текущая память процесса: {current_memory:.1f} МБ")

        summary.append("")
        summary.append("СТАТИСТИКА:")
        summary.append(f"• Количество операций анализа: {len(rhythm_measurements)}")
        summary.append(f"• Общее количество вызовов: {sum(len(m) for m in rhythm_measurements.values())}")

        if total_rhythm_time > 0:
            summary.append(f"• Средняя скорость анализа: {1 / total_rhythm_time:.2f} операций/сек")

        return "\n".join(summary)
