from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import time

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox, QCheckBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .realtime_controller import RealtimeDataBuffer


class RealtimeEEGPlot(FigureCanvas):

    def __init__(self, parent=None, width=12, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        # Настройки отображения
        self.window_seconds = 10.0  # Окно отображения
        self.auto_scale = True
        self.show_grid = True

        # Данные для отображения
        self.buffer: RealtimeDataBuffer = None

        # Настройка темной темы
        self._setup_dark_theme()

        # Создание осей
        self.ax = self.fig.add_subplot(111)
        self._setup_axes()

        # Линия для единственного канала
        self.line = None
        self.line_color = '#00ff00'

        # Обновление каждые 50мс
        self.update_interval = 50
        self.last_update = time.time()

    def _setup_dark_theme(self):
        self.fig.patch.set_facecolor('#121212')

    def _setup_axes(self):
        self.ax.set_facecolor('#121212')

        # Цвета для темной темы
        text_color = '#e0e0e0'
        grid_color = '#2a2a2a'

        # Настройка границ и меток
        for spine in self.ax.spines.values():
            spine.set_color(text_color)

        self.ax.tick_params(colors=text_color)
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)

        # Сетка
        self.ax.grid(True, color=grid_color, linewidth=0.6, alpha=0.9)

        # Подписи осей
        self.ax.set_xlabel('Время (с)', color=text_color)
        self.ax.set_ylabel('Амплитуда (мкВ)', color=text_color)

        # Начальные пределы
        self.ax.set_xlim(0, self.window_seconds)
        self.ax.set_ylim(-100, 100)

    def set_buffer(self, buffer: RealtimeDataBuffer):
        self.buffer = buffer
        self._update_line()

    def _update_line(self):
        # Удаляем старую линию
        if self.line is not None:
            self.line.remove()

        # Создаем новую линию
        self.line, = self.ax.plot([], [], color=self.line_color, linewidth=1.0, label='ЭЭГ')

        # Добавляем легенду
        self.ax.legend(loc='upper right', fancybox=True, framealpha=0.8)

    def update_plot(self):
        if self.buffer is None or self.line is None:
            return

        # Ограничиваем частоту обновления
        current_time = time.time()
        if current_time - self.last_update < self.update_interval / 1000.0:
            return
        self.last_update = current_time

        # Получаем данные для отображения
        timestamps, channel_data = self.buffer.get_data_for_plotting(self.window_seconds)

        if not timestamps or not channel_data or not channel_data[0]:
            return

        # Обновляем данные единственной линии
        self.line.set_data(timestamps, channel_data[0])

        # Обновляем пределы по X (временное окно)
        if timestamps:
            x_max = timestamps[-1]
            x_min = x_max - self.window_seconds
            self.ax.set_xlim(x_min, x_max)

        # Автомасштабирование по Y
        if self.auto_scale:
            y_min, y_max = self.buffer.get_extrema()
            if y_min is not None and y_max is not None:
                # Добавляем небольшой отступ
                y_range = y_max - y_min
                if y_range > 0:
                    padding = y_range * 0.1
                    self.ax.set_ylim(y_min - padding, y_max + padding)
                else:
                    # Если данные константные
                    self.ax.set_ylim(y_min - 10, y_max + 10)

        # Обновляем canvas
        self.draw_idle()

    def set_window_seconds(self, seconds: float):
        self.window_seconds = seconds

    def set_auto_scale(self, enabled: bool):
        self.auto_scale = enabled

    def set_y_limits(self, y_min: float, y_max: float):
        self.auto_scale = False
        self.ax.set_ylim(y_min, y_max)
        self.draw_idle()

    def clear_plot(self):
        if self.line is not None:
            self.line.set_data([], [])
        self.ax.set_xlim(0, self.window_seconds)
        self.ax.set_ylim(-100, 100)
        self.draw_idle()


class RealtimeEEGWidget(QWidget):
    # Сигналы
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

        # Буфер данных
        self.buffer = None

    def setup_ui(self):
        layout = QVBoxLayout()

        # Панель управления
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)

        # График
        self.plot_widget = RealtimeEEGPlot(self)
        layout.addWidget(self.plot_widget)

        # Панель статистики
        stats_panel = self._create_stats_panel()
        layout.addWidget(stats_panel)

        self.setLayout(layout)

    def _create_control_panel(self):
        widget = QWidget()
        layout = QHBoxLayout()

        # Временное окно
        layout.addWidget(QLabel("Окно (сек):"))
        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(1.0, 60.0)
        self.window_spin.setValue(10.0)
        self.window_spin.setSingleStep(1.0)
        self.window_spin.valueChanged.connect(self._on_window_changed)
        layout.addWidget(self.window_spin)

        # Автомасштабирование
        self.auto_scale_check = QCheckBox("Автомасштаб")
        self.auto_scale_check.setChecked(True)
        self.auto_scale_check.stateChanged.connect(self._on_auto_scale_changed)
        layout.addWidget(self.auto_scale_check)

        # Ручные пределы Y
        layout.addWidget(QLabel("Y мин:"))
        self.y_min_spin = QDoubleSpinBox()
        self.y_min_spin.setRange(-10000, 10000)
        self.y_min_spin.setValue(-100)
        self.y_min_spin.setEnabled(False)
        self.y_min_spin.valueChanged.connect(self._on_y_limits_changed)
        layout.addWidget(self.y_min_spin)

        layout.addWidget(QLabel("Y макс:"))
        self.y_max_spin = QDoubleSpinBox()
        self.y_max_spin.setRange(-10000, 10000)
        self.y_max_spin.setValue(100)
        self.y_max_spin.setEnabled(False)
        self.y_max_spin.valueChanged.connect(self._on_y_limits_changed)
        layout.addWidget(self.y_max_spin)

        # Кнопка очистки
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_plot)
        layout.addWidget(clear_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_stats_panel(self):
        widget = QWidget()
        layout = QHBoxLayout()

        self.stats_label = QLabel("Статистика: готов к работе")
        self.stats_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.stats_label)

        widget.setLayout(layout)
        return widget

    def _on_window_changed(self):
        window_seconds = self.window_spin.value()
        self.plot_widget.set_window_seconds(window_seconds)
        self.settings_changed.emit()

    def _on_auto_scale_changed(self):
        auto_scale = self.auto_scale_check.isChecked()
        self.plot_widget.set_auto_scale(auto_scale)

        # Включаем/выключаем ручные элементы управления
        self.y_min_spin.setEnabled(not auto_scale)
        self.y_max_spin.setEnabled(not auto_scale)

        self.settings_changed.emit()

    def _on_y_limits_changed(self):
        if not self.auto_scale_check.isChecked():
            y_min = self.y_min_spin.value()
            y_max = self.y_max_spin.value()
            self.plot_widget.set_y_limits(y_min, y_max)

    def set_buffer(self, buffer: RealtimeDataBuffer):
        self.buffer = buffer
        self.plot_widget.set_buffer(buffer)

    def update_plot(self):
        self.plot_widget.update_plot()
        self._update_statistics()

    def _update_statistics(self):
        if self.buffer is None:
            return

        stats = self.buffer.get_statistics()
        latest_values = self.buffer.get_latest_values()

        # Форматирование статистики
        stats_text = (
            f"Образцы: {stats['total_samples']} | "
            f"Время: {stats['duration_seconds']:.1f}с | "
            f"Каналы: {stats['channels']} | "
            f"Память: {stats['memory_usage_mb']:.1f}МБ"
        )

        if latest_values:
            values_text = " | Последние: " + ", ".join([f"{v:.1f}" for v in latest_values[:3]])
            if len(latest_values) > 3:
                values_text += "..."
            stats_text += values_text

        self.stats_label.setText(stats_text)

    def clear_plot(self):
        if self.buffer:
            self.buffer.clear()
        self.plot_widget.clear_plot()
        self.stats_label.setText("Статистика: очищено")
