import sys

from PyQt5.QtWidgets import QApplication

from app.eeg_app import EEGAnalyzerApp


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = EEGAnalyzerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
