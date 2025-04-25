from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import sys
from app_window import PlateLoadTestApp
from styles import APP_STYLE

if __name__ == '__main__':
    # 👇 Enable high DPI scaling before creating the QApplication
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    app = QApplication(sys.argv)
    window = PlateLoadTestApp()
    window.setStyleSheet(APP_STYLE)
    window.show()
    sys.exit(app.exec_())
