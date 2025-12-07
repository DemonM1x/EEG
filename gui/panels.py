from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QComboBox, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QGroupBox, QTextEdit,
                             QTabWidget, QProgressBar)

from core.performance_widget import PerformanceWidget


class TopControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        self.btn_load = QPushButton("Загрузить данные ЭЭГ")
        self.btn_load.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.btn_load)

        self.btn_test = QPushButton("Тестовые данные")
        layout.addWidget(self.btn_test)

        layout.addWidget(QLabel("Канал:"))
        self.channel_combo = QComboBox()
        layout.addWidget(self.channel_combo)

        layout.addWidget(QLabel("График:"))
        self.viz_combo = QComboBox()
        self.viz_combo.addItems([
            "Временной ряд",
            "Спектр мощности",
            "Все каналы",
            "Спектрограмма"
        ])
        layout.addWidget(self.viz_combo)

        self.setLayout(layout)


class ProcessingPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Низкая частота:"))
        self.low_freq_spin = QDoubleSpinBox()
        self.low_freq_spin.setRange(0.1, 100)
        self.low_freq_spin.setValue(1.0)
        layout.addWidget(self.low_freq_spin)

        layout.addWidget(QLabel("Высокая частота:"))
        self.high_freq_spin = QDoubleSpinBox()
        self.high_freq_spin.setRange(0.1, 100)
        self.high_freq_spin.setValue(40.0)
        layout.addWidget(self.high_freq_spin)

        layout.addWidget(QLabel("Notch (Гц):"))
        self.notch_freq_spin = QSpinBox()
        self.notch_freq_spin.setRange(0, 60)
        self.notch_freq_spin.setValue(50)
        layout.addWidget(self.notch_freq_spin)

        self.detrend_check = QCheckBox("Детренд")
        self.detrend_check.setChecked(True)
        layout.addWidget(self.detrend_check)

        self.remove_dc_check = QCheckBox("Удалить DC")
        self.remove_dc_check.setChecked(True)
        layout.addWidget(self.remove_dc_check)

        self.artifacts_check = QCheckBox("Артефакты")
        self.artifacts_check.setChecked(True)
        layout.addWidget(self.artifacts_check)

        layout.addWidget(QLabel("Порог:"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(1, 10)
        self.threshold_spin.setValue(3.0)
        layout.addWidget(self.threshold_spin)

        self.btn_process = QPushButton("ОБРАБОТАТЬ СИГНАЛ")
        self.btn_process.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.btn_process.setEnabled(False)
        layout.addWidget(self.btn_process)

        self.setLayout(layout)


class AnalysisPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Анализ ритмов для канала:"))
        self.analysis_channel_combo = QComboBox()
        layout.addWidget(self.analysis_channel_combo)

        layout.addWidget(QLabel("Детальный анализ ритма:"))
        self.rhythm_combo = QComboBox()
        self.rhythm_combo.addItems(["Все ритмы", "дельта", "тета", "альфа", "бета", "гамма"])
        layout.addWidget(self.rhythm_combo)

        self.btn_analyze = QPushButton("АНАЛИЗИРОВАТЬ ВСЕ РИТМЫ")
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.btn_analyze.setEnabled(False)
        layout.addWidget(self.btn_analyze)

        self.btn_analyze_single = QPushButton("АНАЛИЗИРОВАТЬ ВЫБРАННЫЙ РИТМ")
        self.btn_analyze_single.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                padding: 8px;
                background-color: #673AB7;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5E35B1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.btn_analyze_single.setEnabled(False)
        layout.addWidget(self.btn_analyze_single)

        self.btn_save_report = QPushButton("СОХРАНИТЬ ОТЧЕТ")
        self.btn_save_report.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.btn_save_report.setEnabled(False)
        layout.addWidget(self.btn_save_report)

        self.btn_validate = QPushButton("ВАЛИДАЦИЯ С MNE-PYTHON")
        self.btn_validate.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #00BCD4;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0097A7;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.btn_validate.setEnabled(False)
        layout.addWidget(self.btn_validate)

        self.setLayout(layout)


class RecordingSettingsPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.initUI()

    def initUI(self):
        settings_group = QGroupBox("Настройки записи")
        settings_layout = QGridLayout()

        settings_layout.addWidget(QLabel("Источник данных:"), 0, 0)
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["Serial порт (Arduino/EEG)", "Синтетические данные (тест)"])
        settings_layout.addWidget(self.data_source_combo, 0, 1)

        settings_layout.addWidget(QLabel("COM порт:"), 1, 0)
        self.com_port_combo = QComboBox()
        settings_layout.addWidget(self.com_port_combo, 1, 1)

        self.btn_refresh_ports = QPushButton("Обновить")
        settings_layout.addWidget(self.btn_refresh_ports, 1, 2)

        settings_layout.addWidget(QLabel("Baudrate:"), 2, 0)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400"])
        self.baudrate_combo.setCurrentText("115200")
        settings_layout.addWidget(self.baudrate_combo, 2, 1)

        settings_layout.addWidget(QLabel("Частота (Гц):"), 3, 0)
        self.recording_sampling_spin = QSpinBox()
        self.recording_sampling_spin.setRange(1, 2000)
        self.recording_sampling_spin.setValue(250)
        settings_layout.addWidget(self.recording_sampling_spin, 3, 1)

        settings_group.setLayout(settings_layout)

        layout = QVBoxLayout()
        layout.addWidget(settings_group)
        self.setLayout(layout)


class RecordingControlPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.initUI()

    def initUI(self):
        control_group = QGroupBox("Управление записью")
        control_layout = QHBoxLayout()

        self.btn_start_recording = QPushButton("НАЧАТЬ ЗАПИСЬ")
        self.btn_start_recording.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        control_layout.addWidget(self.btn_start_recording)

        self.btn_stop_recording = QPushButton("ОСТАНОВИТЬ")
        self.btn_stop_recording.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_stop_recording.setEnabled(False)
        control_layout.addWidget(self.btn_stop_recording)

        self.btn_save_recorded = QPushButton("СОХРАНИТЬ")
        self.btn_save_recorded.setEnabled(False)
        control_layout.addWidget(self.btn_save_recorded)

        self.btn_use_recorded = QPushButton("АНАЛИЗИРОВАТЬ")
        self.btn_use_recorded.setEnabled(False)
        control_layout.addWidget(self.btn_use_recorded)

        control_group.setLayout(control_layout)

        layout = QVBoxLayout()
        layout.addWidget(control_group)
        self.setLayout(layout)


class InfoPanel(QWidget):

    def __init__(self, performance_monitor, parent=None):
        super().__init__(parent)
        self.performance_monitor = performance_monitor
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.info_tabs = QTabWidget()

        self.info_text = QTextEdit()
        self.info_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 13px;
                line-height: 1.6;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)

        self.recommendations_text = QTextEdit()
        self.recommendations_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 13px;
                line-height: 1.6;
                color: #2c3e50;
                background-color: #f0f8ff;
                border: 1px solid #bde0ff;
                border-radius: 8px;
                padding: 15px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)

        self.performance_text = QTextEdit()
        self.performance_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.performance_text.setReadOnly(True)

        self.performance_widget = PerformanceWidget(self.performance_monitor)

        self.info_tabs.addTab(self.info_text, "📋 Информация")
        self.info_tabs.addTab(self.recommendations_text, "💡 Рекомендации")
        self.info_tabs.addTab(self.performance_widget, "⚡ Мониторинг")
        self.info_tabs.addTab(self.performance_text, "📊 Отчет")

        layout.addWidget(self.info_tabs)
        self.setLayout(layout)


class RecordingStatusPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        status_group = QGroupBox("Статус записи")
        status_layout = QVBoxLayout()

        self.recording_status = QLabel("Готов к записи")
        self.recording_status.setStyleSheet("font-size: 12px; padding: 5px;")
        status_layout.addWidget(self.recording_status)

        self.recording_progress = QProgressBar()
        self.recording_progress.setVisible(False)
        status_layout.addWidget(self.recording_progress)

        status_group.setLayout(status_layout)

        info_group = QGroupBox("Информация о записи")
        info_layout = QVBoxLayout()

        self.recording_info = QTextEdit()
        self.recording_info.setMaximumHeight(120)
        self.recording_info.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 12px;
                line-height: 1.5;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        info_layout.addWidget(self.recording_info)

        info_group.setLayout(info_layout)

        layout = QVBoxLayout()
        layout.addWidget(status_group)
        layout.addWidget(info_group)
        self.setLayout(layout)
