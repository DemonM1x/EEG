#!/usr/bin/env python3
"""
Тестовый скрипт для проверки real-time функциональности ЭЭГ
"""

import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton

# Добавляем родительскую директорию в Python path для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт наших модулей
from core.realtime_driver import SyntheticEEGDriver
from core.realtime_controller import RealtimeEEGController, RealtimeDataBuffer
from realtime_work.realtime_visualizer import RealtimeEEGWidget


class TestRealtimeApp(QMainWindow):
    """Простое тестовое приложение для real-time функциональности"""

    def __init__(self):
        super().__init__()
        self.controller = None
        self.buffer = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Тест Real-time ЭЭГ")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Кнопки управления
        self.start_btn = QPushButton("Запустить тест")
        self.start_btn.clicked.connect(self.start_test)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Остановить тест")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        # Real-time виджет
        self.plot_widget = RealtimeEEGWidget()
        layout.addWidget(self.plot_widget)

        central_widget.setLayout(layout)

    def start_test(self):
        """Запуск теста"""
        try:
            print("Запуск теста real-time функциональности...")

            # Создаем синтетический драйвер (один канал)
            driver = SyntheticEEGDriver(sample_rate_hz=250.0)

            # Создаем контроллер и буфер
            self.controller = RealtimeEEGController(driver)
            self.buffer = RealtimeDataBuffer(max_duration_seconds=30.0)

            # Подключаем сигналы
            self.controller.data_received.connect(self.on_data_received)
            self.controller.status_changed.connect(self.on_status_changed)
            self.controller.error_occurred.connect(self.on_error)

            # Настраиваем виджет
            self.plot_widget.set_buffer(self.buffer)

            # Запускаем
            self.controller.start()

            # Обновляем интерфейс
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            print("Тест запущен успешно!")

        except Exception as e:
            print(f"Ошибка запуска теста: {e}")

    def stop_test(self):
        """Остановка теста"""
        try:
            if self.controller:
                self.controller.stop()
                self.controller = None

            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

            print("Тест остановлен")

        except Exception as e:
            print(f"Ошибка остановки теста: {e}")

    def on_data_received(self, batch):
        """Обработка новых данных"""
        try:
            if self.buffer:
                self.buffer.add_batch(batch)
                self.plot_widget.update_plot()

        except Exception as e:
            print(f"Ошибка обработки данных: {e}")

    def on_status_changed(self, status):
        """Обработка изменения статуса"""
        print(f"Статус: {status}")

    def on_error(self, error):
        """Обработка ошибок"""
        print(f"Ошибка: {error}")

    def closeEvent(self, event):
        """Обработка закрытия приложения"""
        self.stop_test()
        event.accept()


def main():
    """Главная функция"""
    app = QApplication(sys.argv)

    # Проверяем импорты
    try:
        print("Проверка импортов...")
        from core.realtime_driver import SyntheticEEGDriver, SerialEEGDriver
        from core.realtime_controller import RealtimeEEGController, RealtimeDataBuffer
        from realtime_work.realtime_visualizer import RealtimeEEGWidget
        from realtime_work.realtime_recorder import RealtimeEEGRecorder
        print("✓ Все модули импортированы успешно")

        # Тест создания объектов
        print("Тест создания объектов...")
        driver = SyntheticEEGDriver(sample_rate_hz=250.0)
        buffer = RealtimeDataBuffer(max_duration_seconds=10.0)
        print("✓ Объекты созданы успешно")

        # Запуск GUI
        print("Запуск тестового приложения...")
        window = TestRealtimeApp()
        window.show()

        sys.exit(app.exec_())

    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        return 1
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return 1


if __name__ == "__main__":
    main()
