from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QGroupBox, QGridLayout)


class PerformanceWidget(QWidget):

    def __init__(self, performance_monitor, parent=None):
        super().__init__(parent)
        self.performance_monitor = performance_monitor
        self.update_interval = 1000  # мс
        self.initUI()
        self.start_monitoring()

    def initUI(self):
        layout = QVBoxLayout()

        # Группа производительности
        perf_group = QGroupBox("Оценка производительности")
        perf_layout = QGridLayout()

        # Время обработки
        perf_layout.addWidget(QLabel("Время обработки:"), 0, 0)
        self.processing_time_label = QLabel("0.00 сек")
        self.processing_time_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        perf_layout.addWidget(self.processing_time_label, 0, 1)

        # Использование памяти
        perf_layout.addWidget(QLabel("Использование памяти:"), 1, 0)
        self.memory_label = QLabel("0.0 MB")
        self.memory_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        perf_layout.addWidget(self.memory_label, 1, 1)

        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        layout.addStretch()

        self.setLayout(layout)

    def start_monitoring(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(self.update_interval)

    def update_display(self):
        info = self.performance_monitor.get_system_info()

        # Использование памяти
        memory_mb = info['memory_mb']
        self.memory_label.setText(f"{memory_mb:.1f} MB")

        # Общее время обработки всех операций
        total_time = sum(
            sum(m['time'] for m in measurements)
            for measurements in self.performance_monitor.measurements.values()
        )
        self.processing_time_label.setText(f"{total_time:.2f} сек")
