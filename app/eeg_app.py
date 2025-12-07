import serial.tools.list_ports

from app.processing import ProcessingMethods, RealtimeMethods
from app.visualization import VisualizationMethods
from core.analyzer import EEGAnalyzer
from core.data_loader import EEGDataLoader
from core.preprocessor import EEGPreprocessor
from core.realtime_visualizer import RealtimeEEGWidget
from core.validator import EEGValidator
from core.visualizer import EEGVisualizer
from gui.menu_bar import EEGMenuBar
from gui.panels import *
from gui.threads import *
from gui.widgets import *
from utils.performance import PerformanceMonitor


class EEGAnalyzerApp(QMainWindow, ProcessingMethods, RealtimeMethods, VisualizationMethods):
    def __init__(self):
        super().__init__()
        self.performance_monitor = PerformanceMonitor()
        self.init_core_modules()
        self.init_data_variables()
        self.init_realtime_components()
        self.init_processing_params()
        self.initUI()
        self.load_user_preferences()

    def init_core_modules(self):
        self.data_loader = EEGDataLoader()
        self.data_loader.performance_monitor = self.performance_monitor
        self.preprocessor = EEGPreprocessor()
        self.preprocessor.performance_monitor = self.performance_monitor
        self.analyzer = EEGAnalyzer()
        self.analyzer.performance_monitor = self.performance_monitor
        self.visualizer = EEGVisualizer()
        self.visualizer.performance_monitor = self.performance_monitor
        self.validator = EEGValidator()

    def init_data_variables(self):
        self.raw_data = None
        self.processed_data = None
        self.sampling_rate = 250
        self.channel_names = []
        self.current_analysis = None
        self.recorded_data = None
        self.recording_thread = None
        self.is_recording = False

    def init_realtime_components(self):
        self.realtime_controller = None
        self.realtime_buffer = None
        self.realtime_recorder = None
        self.realtime_driver = None

    def init_processing_params(self):
        self.processing_params = {
            'low_freq': 1.0, 'high_freq': 40.0, 'notch_freq': 50.0,
            'detrend': True, 'remove_dc': True, 'remove_artifacts': True, 'artifact_threshold': 3.0
        }

    def initUI(self):
        self.setWindowTitle("EEG Analyzer")
        self.setGeometry(50, 50, 1600, 900)
        self.menu_bar = EEGMenuBar(self)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.tabs = QTabWidget()
        self.data_tab = self.create_scrollable_tab(self.create_data_tab())
        self.recording_tab = self.create_scrollable_tab(self.create_recording_tab())
        self.tabs.addTab(self.data_tab, "ДАННЫЕ")
        self.tabs.addTab(self.recording_tab, "ЗАПИСЬ ДАННЫХ")
        main_layout.addWidget(self.tabs)
        self.statusBar().showMessage('Готов к работе')
        self.statusBar().addPermanentWidget(self.create_status_widgets())

    def create_scrollable_tab(self, content_widget):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content_widget.setMinimumSize(1400, 1200)
        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_data_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.top_panel = TopControlPanel(self)
        self.processing_panel = ProcessingPanel(self)
        self.analysis_panel = AnalysisPanel(self)
        self.connect_panel_signals()
        layout.addWidget(self.top_panel)
        layout.addWidget(self.processing_panel)
        layout.addWidget(self.analysis_panel)
        self.plot_control = PlotControlWidget()
        self.plot_control.plot_changed.connect(self.on_plot_changed)
        layout.addWidget(self.plot_control)
        self.plot_area = QWidget()
        plot_layout = QVBoxLayout(self.plot_area)
        self.raw_canvas = MplCanvas(self, width=14, height=7)
        self.processed_canvas = MplCanvas(self, width=14, height=7)
        self.analysis_canvas = MplCanvas(self, width=14, height=7)
        plot_layout.addWidget(self.raw_canvas)
        plot_layout.addWidget(self.processed_canvas)
        plot_layout.addWidget(self.analysis_canvas)
        self.show_plot_by_index(0)
        layout.addWidget(self.plot_area, 1)
        self.info_panel = InfoPanel(self.performance_monitor, self)
        layout.addWidget(self.info_panel)
        widget.setLayout(layout)
        return widget

    def create_recording_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.recording_settings_panel = RecordingSettingsPanel(self)
        layout.addWidget(self.recording_settings_panel)
        self.recording_control_panel = RecordingControlPanel(self)
        layout.addWidget(self.recording_control_panel)
        self.recording_status_panel = RecordingStatusPanel(self)
        layout.addWidget(self.recording_status_panel)
        self.realtime_plot_widget = RealtimeEEGWidget()
        layout.addWidget(self.realtime_plot_widget)
        self.connect_recording_signals()
        widget.setLayout(layout)
        return widget

    def connect_panel_signals(self):
        self.top_panel.btn_load.clicked.connect(self.load_data)
        self.top_panel.btn_test.clicked.connect(self.generate_test_data)
        self.top_panel.channel_combo.currentIndexChanged.connect(self.update_plots)
        self.top_panel.viz_combo.currentIndexChanged.connect(self.update_plots)
        self.processing_panel.low_freq_spin.valueChanged.connect(self.update_processing_params)
        self.processing_panel.high_freq_spin.valueChanged.connect(self.update_processing_params)
        self.processing_panel.notch_freq_spin.valueChanged.connect(self.update_processing_params)
        self.processing_panel.detrend_check.stateChanged.connect(self.update_processing_params)
        self.processing_panel.remove_dc_check.stateChanged.connect(self.update_processing_params)
        self.processing_panel.artifacts_check.stateChanged.connect(self.update_processing_params)
        self.processing_panel.threshold_spin.valueChanged.connect(self.update_processing_params)
        self.processing_panel.btn_process.clicked.connect(self.process_data)
        self.analysis_panel.analysis_channel_combo.currentIndexChanged.connect(self.on_analysis_channel_changed)
        self.analysis_panel.btn_analyze.clicked.connect(self.analyze_rhythms)
        self.analysis_panel.btn_analyze_single.clicked.connect(self.analyze_single_rhythm)
        self.analysis_panel.btn_save_report.clicked.connect(self.save_report)
        self.analysis_panel.btn_validate.clicked.connect(self.validate_with_mne)

    def connect_recording_signals(self):
        self.recording_settings_panel.data_source_combo.currentTextChanged.connect(self.on_data_source_changed)
        self.recording_settings_panel.btn_refresh_ports.clicked.connect(self.refresh_ports)
        self.recording_control_panel.btn_start_recording.clicked.connect(self.start_recording)
        self.recording_control_panel.btn_stop_recording.clicked.connect(self.stop_recording)
        self.recording_control_panel.btn_save_recorded.clicked.connect(self.save_recorded_data)
        self.recording_control_panel.btn_use_recorded.clicked.connect(self.use_recorded_data)
        self.refresh_ports()

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл ЭЭГ", "",
                                                   "Файлы ЭЭГ (*.edf *.csv *.txt *.set);;All Files (*.*)")
        if file_path:
            self.load_thread = DataLoadThread(file_path, self.data_loader)
            self.load_thread.result_signal.connect(self.on_data_loaded)
            self.load_thread.error_signal.connect(self.on_load_error)
            self.load_thread.info_signal.connect(self.on_load_info)
            self.load_thread.start()
            self.statusBar().showMessage(f"Загрузка: {file_path}")

    def on_data_loaded(self, result):
        data, sampling_rate, channel_names = result
        self.raw_data = data
        self.sampling_rate = sampling_rate
        self.channel_names = channel_names
        self.processed_data = None
        self.current_analysis = None
        self.update_channel_combo()
        self.update_analysis_channel_combo()
        self.update_data_info()
        self.update_plots()
        self.processing_panel.btn_process.setEnabled(True)
        self.analysis_panel.btn_analyze.setEnabled(False)
        self.performance_monitor.take_system_snapshot()
        self.update_performance_display()
        self.statusBar().showMessage("Данные успешно загружены!")

    def on_load_error(self, error_msg):
        QMessageBox.critical(self, "Ошибка загрузки", error_msg)
        self.statusBar().showMessage("Ошибка загрузки данных")

    def on_load_info(self, info_msg):
        self.info_panel.info_text.append(info_msg)

    def generate_test_data(self):
        try:
            self.raw_data, self.sampling_rate, self.channel_names = self.data_loader.generate_test_data()
            self.processed_data = None
            self.current_analysis = None
            self.update_channel_combo()
            self.update_analysis_channel_combo()
            self.update_data_info()
            self.update_plots()
            self.processing_panel.btn_process.setEnabled(True)
            self.analysis_panel.btn_analyze.setEnabled(False)
            self.statusBar().showMessage("Тестовые данные сгенерированы!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации: {e}")

    def update_channel_combo(self):
        self.top_panel.channel_combo.clear()
        if self.channel_names:
            self.top_panel.channel_combo.addItems(self.channel_names)
        else:
            self.top_panel.channel_combo.addItems(["Канал 0"])

    def update_analysis_channel_combo(self):
        self.analysis_panel.analysis_channel_combo.clear()
        if self.channel_names:
            self.analysis_panel.analysis_channel_combo.addItems(self.channel_names)
        else:
            self.analysis_panel.analysis_channel_combo.addItems(["Канал 0"])

    def update_processing_params(self):
        self.processing_params = {
            'low_freq': self.processing_panel.low_freq_spin.value(),
            'high_freq': self.processing_panel.high_freq_spin.value(),
            'notch_freq': self.processing_panel.notch_freq_spin.value(),
            'detrend': self.processing_panel.detrend_check.isChecked(),
            'remove_dc': self.processing_panel.remove_dc_check.isChecked(),
            'remove_artifacts': self.processing_panel.artifacts_check.isChecked(),
            'artifact_threshold': self.processing_panel.threshold_spin.value()
        }

    def refresh_ports(self):
        self.recording_settings_panel.com_port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.recording_settings_panel.com_port_combo.addItem(f"{port.device} - {port.description}")

    def on_data_source_changed(self):
        data_source = self.recording_settings_panel.data_source_combo.currentText()
        is_serial = "Serial" in data_source
        self.recording_settings_panel.com_port_combo.setEnabled(is_serial)
        self.recording_settings_panel.btn_refresh_ports.setEnabled(is_serial)
        self.recording_settings_panel.baudrate_combo.setEnabled(is_serial)
        if not is_serial:
            self.recording_status_panel.recording_info.append("Выбраны синтетические данные - COM порт не требуется")

    def load_user_preferences(self):
        try:
            geometry = [50, 50, 1600, 900]
            self.setGeometry(*geometry)
            self.processing_params.update({'low_freq': 1.0, 'high_freq': 40.0, 'notch_freq': 50.0})
            self.processing_panel.low_freq_spin.setValue(self.processing_params['low_freq'])
            self.processing_panel.high_freq_spin.setValue(self.processing_params['high_freq'])
            self.processing_panel.notch_freq_spin.setValue(self.processing_params['notch_freq'])
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    def create_status_widgets(self):
        status_widget = QWidget()
        layout = QHBoxLayout(status_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.memory_label = QLabel("Память: --")
        self.memory_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.memory_label)
        self.processing_progress = QProgressBar()
        self.processing_progress.setVisible(False)
        self.processing_progress.setMaximumWidth(100)
        self.processing_progress.setMaximumHeight(16)
        layout.addWidget(self.processing_progress)
        from PyQt5.QtCore import QTimer
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_status)
        self.memory_timer.start(5000)
        return status_widget

    def update_memory_status(self):
        try:
            import psutil
            memory = psutil.virtual_memory()
            color = "#666"
            if memory.percent > 85:
                color = "#d32f2f"
            elif memory.percent > 70:
                color = "#f57c00"
            self.memory_label.setText(f"Память: {memory.percent:.1f}%")
            self.memory_label.setStyleSheet(f"font-size: 10px; color: {color};")
        except Exception as e:
            print(f"Ошибка обновления статуса памяти: {e}")

    def show_processing_progress(self, show=True, value=0):
        self.processing_progress.setVisible(show)
        if show:
            self.processing_progress.setValue(value)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'realtime_controller') and self.realtime_controller:
                self.realtime_controller.stop()
            event.accept()
        except Exception as e:
            print(f"Ошибка при закрытии приложения: {e}")
            event.accept()
