from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=16, height=8, dpi=120):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class PlotControlWidget(QWidget):
    plot_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_plot_index = 0
        self.plot_titles = ["ИСХОДНЫЙ СИГНАЛ", "ОБРАБОТАННЫЙ СИГНАЛ", "АНАЛИЗ РИТМОВ"]
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.btn_prev = QPushButton("◀ Предыдущий")
        self.btn_prev.setStyleSheet(
            "QPushButton {font-size: 12px; padding: 8px; background-color: #34495e; color: white; border: none; border-radius: 4px;} QPushButton:hover {background-color: #2c3e50;} QPushButton:disabled {background-color: #95a5a6;}")
        self.btn_prev.clicked.connect(self.show_previous_plot)
        layout.addWidget(self.btn_prev)
        self.current_plot_label = QLabel("ИСХОДНЫЙ СИГНАЛ")
        self.current_plot_label.setStyleSheet(
            "QLabel {font-size: 16px; font-weight: bold; color: #2c3e50; padding: 8px; background-color: #ecf0f1; border-radius: 4px;}")
        self.current_plot_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_plot_label, 1)
        self.btn_next = QPushButton("Следующий ▶")
        self.btn_next.setStyleSheet(
            "QPushButton {font-size: 12px; padding: 8px; background-color: #34495e; color: white; border: none; border-radius: 4px;} QPushButton:hover {background-color: #2c3e50;} QPushButton:disabled {background-color: #95a5a6;}")
        self.btn_next.clicked.connect(self.show_next_plot)
        layout.addWidget(self.btn_next)
        self.setLayout(layout)
        self.update_buttons()

    def show_previous_plot(self):
        if self.current_plot_index > 0:
            self.current_plot_index -= 1
            self.update_display()

    def show_next_plot(self):
        if self.current_plot_index < len(self.plot_titles) - 1:
            self.current_plot_index += 1
            self.update_display()

    def update_display(self):
        self.current_plot_label.setText(self.plot_titles[self.current_plot_index])
        self.update_buttons()
        self.plot_changed.emit(self.current_plot_index)

    def update_buttons(self):
        self.btn_prev.setEnabled(self.current_plot_index > 0)
        self.btn_next.setEnabled(self.current_plot_index < len(self.plot_titles) - 1)

    def get_current_plot_index(self):
        return self.current_plot_index

    def set_current_plot_index(self, index):
        if 0 <= index < len(self.plot_titles):
            self.current_plot_index = index
            self.update_display()


class ScrollablePlotWidget(QWidget):
    def __init__(self, title, canvas, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(canvas)
        scroll_area.setMinimumSize(400, 500)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
