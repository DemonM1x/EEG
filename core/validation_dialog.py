"""
Диалоговое окно для отображения результатов валидации
"""
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QTabWidget, QWidget, QTableWidget,
                             QTableWidgetItem, QLabel, QProgressBar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ValidationThread(QThread):
    """Поток для валидации с MNE"""
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, validator, data, sampling_rate, channel_names, our_filtered):
        super().__init__()
        self.validator = validator
        self.data = data
        self.sampling_rate = sampling_rate
        self.channel_names = channel_names
        self.our_filtered = our_filtered

    def run(self):
        try:
            self.progress_signal.emit(20)

            # Получаем результаты MNE
            mne_result = self.validator.compare_with_mne(
                self.data,
                self.sampling_rate,
                self.channel_names
            )

            if not mne_result['available']:
                self.error_signal.emit(mne_result['message'])
                return

            self.progress_signal.emit(50)

            # Сравниваем фильтрацию
            comparison = self.validator.compare_filtering(
                self.our_filtered,
                mne_result['mne_data']
            )

            self.progress_signal.emit(80)

            # Генерируем отчёт
            report = self.validator.generate_comparison_report(
                self.data,
                mne_result['mne_data'],
                self.our_filtered,
                mne_result['mne_data']
            )

            self.progress_signal.emit(100)

            result = {
                'comparison': comparison,
                'report': report,
                'mne_data': mne_result['mne_data'],
                'our_data': self.our_filtered
            }

            self.result_signal.emit(result)

        except Exception as e:
            self.error_signal.emit(f"Ошибка валидации: {str(e)}")


class ValidationDialog(QDialog):
    """Диалог для отображения результатов валидации"""

    def __init__(self, validator, data, sampling_rate, channel_names, our_filtered, parent=None):
        super().__init__(parent)
        self.validator = validator
        self.data = data
        self.sampling_rate = sampling_rate
        self.channel_names = channel_names
        self.our_filtered = our_filtered
        self.validation_result = None

        self.initUI()
        self.start_validation()

    def initUI(self):
        self.setWindowTitle("Валидация результатов с MNE-Python")
        self.setGeometry(100, 100, 1000, 700)

        layout = QVBoxLayout()

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Инициализация валидации...")
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        # Табы
        self.tabs = QTabWidget()

        # Таб с отчётом
        self.report_tab = QWidget()
        report_layout = QVBoxLayout()
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Courier New", 10))
        report_layout.addWidget(self.report_text)
        self.report_tab.setLayout(report_layout)

        # Таб с таблицей
        self.table_tab = QWidget()
        table_layout = QVBoxLayout()
        self.comparison_table = QTableWidget()
        table_layout.addWidget(self.comparison_table)
        self.table_tab.setLayout(table_layout)

        # Таб с графиками
        self.plot_tab = QWidget()
        plot_layout = QVBoxLayout()
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        plot_layout.addWidget(self.canvas)
        self.plot_tab.setLayout(plot_layout)

        self.tabs.addTab(self.report_tab, "📊 Отчёт")
        self.tabs.addTab(self.table_tab, "📋 Таблица")
        self.tabs.addTab(self.plot_tab, "📈 Графики")

        layout.addWidget(self.tabs)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Сохранить отчёт")
        self.btn_save.clicked.connect(self.save_report)
        self.btn_save.setEnabled(False)
        buttons_layout.addWidget(self.btn_save)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_close)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def start_validation(self):
        """Запуск валидации"""
        self.validation_thread = ValidationThread(
            self.validator,
            self.data,
            self.sampling_rate,
            self.channel_names,
            self.our_filtered
        )

        self.validation_thread.progress_signal.connect(self.update_progress)
        self.validation_thread.result_signal.connect(self.on_validation_complete)
        self.validation_thread.error_signal.connect(self.on_validation_error)

        self.validation_thread.start()

    def update_progress(self, value):
        """Обновление прогресса"""
        self.progress_bar.setValue(value)

        if value == 20:
            self.progress_label.setText("Обработка данных с MNE-Python...")
        elif value == 50:
            self.progress_label.setText("Сравнение результатов...")
        elif value == 80:
            self.progress_label.setText("Генерация отчёта...")
        elif value == 100:
            self.progress_label.setText("Валидация завершена!")

    def on_validation_complete(self, result):
        """Обработка результатов валидации"""
        self.validation_result = result

        # Отображаем отчёт
        self.report_text.setPlainText(result['report'])

        # Заполняем таблицу
        self.fill_comparison_table(result['comparison'])

        # Строим графики
        self.plot_comparison(result)

        # Активируем кнопку сохранения
        self.btn_save.setEnabled(True)

        # Скрываем прогресс бар
        self.progress_bar.hide()
        self.progress_label.hide()

    def on_validation_error(self, error_msg):
        """Обработка ошибки валидации"""
        self.progress_label.setText(f"Ошибка: {error_msg}")
        self.progress_bar.hide()
        self.report_text.setPlainText(f"ОШИБКА ВАЛИДАЦИИ:\n\n{error_msg}")

    def fill_comparison_table(self, comparison):
        """Заполнение таблицы сравнения"""
        channels = comparison['channels']

        self.comparison_table.setRowCount(len(channels))
        self.comparison_table.setColumnCount(6)
        self.comparison_table.setHorizontalHeaderLabels([
            'Канал', 'Корреляция', 'R²', 'RMSE', 'MAE', 'NRMSE (%)'
        ])

        for i, ch_data in enumerate(channels):
            self.comparison_table.setItem(i, 0, QTableWidgetItem(f"Канал {ch_data['channel']}"))
            self.comparison_table.setItem(i, 1, QTableWidgetItem(f"{ch_data['correlation']:.4f}"))
            self.comparison_table.setItem(i, 2, QTableWidgetItem(f"{ch_data['r_squared']:.4f}"))
            self.comparison_table.setItem(i, 3, QTableWidgetItem(f"{ch_data['rmse']:.6f}"))
            self.comparison_table.setItem(i, 4, QTableWidgetItem(f"{ch_data['mae']:.6f}"))
            self.comparison_table.setItem(i, 5, QTableWidgetItem(f"{ch_data['nrmse']:.2f}"))

        self.comparison_table.resizeColumnsToContents()

    def plot_comparison(self, result):
        """Построение графиков сравнения"""
        self.figure.clear()

        our_data = result['our_data']
        mne_data = result['mne_data']

        n_channels = min(4, our_data.shape[0])

        for i in range(n_channels):
            ax = self.figure.add_subplot(n_channels, 1, i + 1)

            time_axis = np.arange(our_data.shape[1]) / self.sampling_rate

            ax.plot(time_axis, our_data[i], label='Наш результат', alpha=0.7)
            ax.plot(time_axis, mne_data[i], label='MNE-Python', alpha=0.7, linestyle='--')

            ax.set_ylabel(f'Канал {i}')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)

            if i == 0:
                ax.set_title('Сравнение фильтрованных сигналов')
            if i == n_channels - 1:
                ax.set_xlabel('Время (сек)')

        self.figure.tight_layout()
        self.canvas.draw()

    def save_report(self):
        """Сохранение отчёта"""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт валидации",
            "validation_report.txt",
            "Text Files (*.txt)"
        )

        if file_path and self.validation_result:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.validation_result['report'])

            self.progress_label.setText(f"Отчёт сохранён: {file_path}")
            self.progress_label.show()
