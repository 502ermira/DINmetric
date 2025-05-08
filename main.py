from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import sys
from app_window import PlateLoadTestApp
from styles import APP_STYLE
from utils import resource_path

if __name__ == '__main__':
    # Enable high DPI scaling
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    app = QApplication(sys.argv)
    app_icon_path = resource_path("icons/app_icon.ico")
    app_icon = QIcon(app_icon_path)
    app.setWindowIcon(app_icon)

    window = PlateLoadTestApp()
    window.setWindowIcon(app_icon)
    window.setStyleSheet(APP_STYLE)
    window.show()

    sys.exit(app.exec_())