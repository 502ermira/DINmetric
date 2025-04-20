from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class GraphWindow(QMainWindow):
    def __init__(self, figure, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graph Viewer")
        self.resize(1200, 800)

        central_widget = QWidget()
        layout = QVBoxLayout()
        full_canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(full_canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(full_canvas)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)