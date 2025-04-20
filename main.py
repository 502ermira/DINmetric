import sys
from PyQt5.QtWidgets import QApplication
from app_window import PlateLoadTestApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlateLoadTestApp()
    window.show()
    sys.exit(app.exec_())