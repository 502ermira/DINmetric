from PyQt5.QtWidgets import QApplication
import sys
from app_window import PlateLoadTestApp
from styles import APP_STYLE

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlateLoadTestApp()
    window.setStyleSheet(APP_STYLE)
    window.show()
    sys.exit(app.exec_())