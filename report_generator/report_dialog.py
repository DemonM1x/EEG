from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QPushButton, QLineEdit, QTextEdit, QLabel, 
                             QGroupBox, QCheckBox, QFileDialog, QMessageBox,
                             QDateEdit, QSpinBox, QComboBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import os
from datetime import datetime


class ReportConfigDialog(QDialog):
    """Диалог настройки PDF-отчета"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка PDF-отчета")
        self.setModal(True)
        self.resize(500, 600)
        
        # Данные для отчета
        self.patient_info = {}
        self.output_path = ""
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Генерация PDF-отчета по анализу ЭЭГ")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Информация о пациенте
        patient_group = QGroupBox("Информация о пациенте")
        patient_layout = QFormLayout()
        
        self.patient_name_edit = QLineEdit()
        patient_layout.addRow("ФИО пациента:", self.patient_name_edit)
        
        self.patient_age_spin = QSpinBox()
        self.patient_age_spin.setRange(0, 120)
        self.patient_age_spin.setValue(30)
        patient_layout.addRow("Возраст:", self.patient_age_spin)
        
        self.patient_gender_combo = QComboBox()
        self.patient_gender_combo.addItems(["Не указан", "Мужской", "Женский"])
        patient_layout.addRow("Пол:", self.patient_gender_combo)
        
        self.examination_date = QDateEdit()
        self.examination_date.setDate(QDate.currentDate())
        self.examination_date.setCalendarPopup(True)
        patient_layout.addRow("Дата обследования:", self.examination_date)
        
        self.doctor_name_edit = QLineEdit()
        self.doctor_name_edit.setPlaceholderText("Петров П.П.")
        patient_layout.addRow("Врач:", self.doctor_name_edit)
        
        patient_group.setLayout(patient_layout)
        layout.addWidget(patient_group)
        
        # Настройки отчета
        report_group = QGroupBox("Настройки отчета")
        report_layout = QVBoxLayout()
        
        # Чекбоксы для включения разделов
        sections_layout = QVBoxLayout()
        
        self.include_raw_signals = QCheckBox("Включить исходные сигналы")
        self.include_raw_signals.setChecked(True)
        sections_layout.addWidget(self.include_raw_signals)
        
        self.include_processed_signals = QCheckBox("Включить обработанные сигналы")
        self.include_processed_signals.setChecked(True)
        sections_layout.addWidget(self.include_processed_signals)
        
        self.include_spectral_analysis = QCheckBox("Включить спектральный анализ")
        self.include_spectral_analysis.setChecked(True)
        sections_layout.addWidget(self.include_spectral_analysis)
        
        self.include_rhythm_analysis = QCheckBox("Включить анализ ритмов")
        self.include_rhythm_analysis.setChecked(True)
        sections_layout.addWidget(self.include_rhythm_analysis)
        
        self.include_recommendations = QCheckBox("Включить рекомендации и выводы")
        self.include_recommendations.setChecked(True)
        sections_layout.addWidget(self.include_recommendations)
        
        report_layout.addLayout(sections_layout)
        
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        # Выбор файла для сохранения
        file_group = QGroupBox("Сохранение отчета")
        file_layout = QVBoxLayout()
        
        file_selection_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Выберите путь для сохранения PDF-отчета...")
        self.file_path_edit.setReadOnly(True)
        file_selection_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("📁 Обзор...")
        self.browse_button.clicked.connect(self.browse_file)
        file_selection_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(file_selection_layout)
        
        # Автоматическое имя файла
        auto_name_layout = QHBoxLayout()
        self.auto_name_check = QCheckBox("Автоматическое имя файла")
        self.auto_name_check.setChecked(True)
        self.auto_name_check.stateChanged.connect(self.on_auto_name_changed)
        auto_name_layout.addWidget(self.auto_name_check)

        file_layout.addLayout(auto_name_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("Предварительный просмотр")
        self.preview_button.clicked.connect(self.preview_report)
        buttons_layout.addWidget(self.preview_button)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        self.generate_button = QPushButton("Создать отчет")
        self.generate_button.clicked.connect(self.accept)
        self.generate_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
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
        buttons_layout.addWidget(self.generate_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Генерируем имя файла по умолчанию
        self.generate_filename()
    
    def browse_file(self):
        """Выбор файла для сохранения"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить PDF-отчет",
            self.get_default_filename(),
            "PDF файлы (*.pdf);;Все файлы (*)"
        )
        
        if filename:
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            self.file_path_edit.setText(filename)
            self.output_path = filename
    
    def generate_filename(self):
        """Генерация автоматического имени файла"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        patient_name = self.patient_name_edit.text().strip()
        
        if patient_name:
            # Очищаем имя от недопустимых символов
            safe_name = "".join(c for c in patient_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            filename = f"EEG_Report_{safe_name}_{timestamp}.pdf"
        else:
            filename = f"EEG_Report_{timestamp}.pdf"
        
        # Пробуем найти доступную папку для сохранения
        possible_paths = [
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.expanduser("~"),
            os.getcwd(),  # Текущая рабочая папка
            os.path.dirname(os.path.abspath(__file__))  # Папка с приложением
        ]
        
        selected_path = None
        for path in possible_paths:
            try:
                if os.path.exists(path) and os.access(path, os.W_OK):
                    selected_path = path
                    break
            except:
                continue
        
        if selected_path is None:
            # Если ничего не найдено, используем временную папку
            import tempfile
            selected_path = tempfile.gettempdir()
        
        full_path = os.path.join(selected_path, filename)
        
        self.file_path_edit.setText(full_path)
        self.output_path = full_path
    
    def get_default_filename(self):
        """Получение имени файла по умолчанию"""
        if self.output_path:
            return self.output_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"EEG_Report_{timestamp}.pdf"
    
    def on_auto_name_changed(self):
        """Обработка изменения автоматического имени"""
        if self.auto_name_check.isChecked():
            self.generate_filename()
    
    def preview_report(self):
        """Предварительный просмотр настроек отчета"""
        info = self.get_report_info()
        
        preview_text = f"""
ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР ОТЧЕТА

ИНФОРМАЦИЯ О ПАЦИЕНТЕ:
• ФИО: {info['patient_info'].get('name', 'Не указано')}
• Возраст: {info['patient_info'].get('age', 'Не указан')}
• Пол: {info['patient_info'].get('gender', 'Не указан')}
• ID: {info['patient_info'].get('id', 'Не указан')}
• Дата обследования: {info['patient_info'].get('examination_date', 'Не указана')}
• Врач: {info['patient_info'].get('doctor', 'Не указан')}

РАЗДЕЛЫ ОТЧЕТА:
• Исходные сигналы: {'✓' if info['include_raw_signals'] else '✗'}
• Обработанные сигналы: {'✓' if info['include_processed_signals'] else '✗'}
• Спектральный анализ: {'✓' if info['include_spectral_analysis'] else '✗'}
• Анализ ритмов: {'✓' if info['include_rhythm_analysis'] else '✗'}
• Рекомендации: {'✓' if info['include_recommendations'] else '✗'}

ФАЙЛ СОХРАНЕНИЯ:
{info['output_path']}

КОММЕНТАРИИ:
{info['comments'] if info['comments'] else 'Нет комментариев'}
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Предварительный просмотр отчета")
        msg.setText(preview_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
    
    def get_report_info(self):
        """Получение всей информации для отчета"""
        patient_info = {}
        
        if self.patient_name_edit.text().strip():
            patient_info['ФИО'] = self.patient_name_edit.text().strip()
        
        if self.patient_age_spin.value() > 0:
            patient_info['Возраст'] = self.patient_age_spin.value()
        
        if self.patient_gender_combo.currentText() != "Не указан":
            patient_info['Пол'] = self.patient_gender_combo.currentText()
        
        patient_info['Дата'] = self.examination_date.date().toString("dd.MM.yyyy")
        
        if self.doctor_name_edit.text().strip():
            patient_info['Врач'] = self.doctor_name_edit.text().strip()
        
        return {
            'patient_info': patient_info,
            'include_raw_signals': self.include_raw_signals.isChecked(),
            'include_processed_signals': self.include_processed_signals.isChecked(),
            'include_spectral_analysis': self.include_spectral_analysis.isChecked(),
            'include_rhythm_analysis': self.include_rhythm_analysis.isChecked(),
            'include_recommendations': self.include_recommendations.isChecked(),
            'comments': '',  # Комментарии не используются
            'output_path': self.file_path_edit.text()
        }
    
    def accept(self):
        """Подтверждение создания отчета"""
        if not self.file_path_edit.text():
            QMessageBox.warning(self, "Ошибка", "Выберите файл для сохранения отчета!")
            return
        
        # Проверяем, что директория существует
        output_dir = os.path.dirname(self.file_path_edit.text())
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать директорию:\n{e}")
                return
        
        self.output_path = self.file_path_edit.text()
        self.patient_info = self.get_report_info()['patient_info']
        
        super().accept()