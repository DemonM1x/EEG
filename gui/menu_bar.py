from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QMessageBox


class EEGMenuBar:
    def __init__(self, parent):
        self.parent = parent
        self.create_menu_bar()

    def create_menu_bar(self):
        menubar = self.parent.menuBar()
        self.create_file_menu(menubar)
        self.create_processing_menu(menubar)
        self.create_analysis_menu(menubar)
        self.create_help_menu(menubar)

    def create_file_menu(self, menubar):
        file_menu = menubar.addMenu('&Файл')
        open_action = QAction('&Открыть...', self.parent)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.parent.load_data)
        file_menu.addAction(open_action)
        test_action = QAction('&Тестовые данные', self.parent)
        test_action.setShortcut('Ctrl+T')
        test_action.triggered.connect(self.parent.generate_test_data)
        file_menu.addAction(test_action)
        file_menu.addSeparator()
        exit_action = QAction('В&ыход', self.parent)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.parent.close)
        file_menu.addAction(exit_action)

    def create_processing_menu(self, menubar):
        processing_menu = menubar.addMenu('&Обработка')
        process_action = QAction('&Обработать сигнал', self.parent)
        process_action.setShortcut('Ctrl+P')
        process_action.triggered.connect(self.parent.process_data)
        processing_menu.addAction(process_action)

    def create_analysis_menu(self, menubar):
        analysis_menu = menubar.addMenu('&Анализ')
        analyze_action = QAction('&Анализ ритмов', self.parent)
        analyze_action.setShortcut('Ctrl+A')
        analyze_action.triggered.connect(self.parent.analyze_rhythms)
        analysis_menu.addAction(analyze_action)

    def create_help_menu(self, menubar):
        help_menu = menubar.addMenu('&Справка')
        about_action = QAction('&О программе', self.parent)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        about_text = """
<h2>EEG Analyzer</h2>
<p><b>Профессиональный анализатор ЭЭГ</b></p>
<p>Версия: 2.0.0 (Оптимизированная)</p>
<p>Комплексная система для анализа электроэнцефалограмм</p>
        """
        QMessageBox.about(self.parent, "О программе", about_text)
