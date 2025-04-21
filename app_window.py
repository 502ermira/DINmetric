from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from constants import CYCLE_TYPES
from data_handler import evaluate_test_secant
from data_handler import evaluate_test_curve_fit
from pdf_exporter import export_to_pdf
from graph_window import GraphWindow

class PlateLoadTestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DIN 18134 - Plate Load Test")
        self.setMinimumSize(1100, 750)
        self.init_ui()

    def init_ui(self):
        meta_layout = QHBoxLayout()

        self.test_id = QLineEdit()
        self.plate_diameter = QComboBox()
        self.plate_diameter.addItems(["300", "600", "762"])
        self.lever_ratio = QLineEdit("1.000")

        meta_form = QVBoxLayout()
        meta_form.addWidget(QLabel("Test ID"))
        meta_form.addWidget(self.test_id)
        meta_form.addWidget(QLabel("Plate Diameter (mm)"))
        meta_form.addWidget(self.plate_diameter)
        meta_form.addWidget(QLabel("Lever Ratio (hp/hm)"))
        meta_form.addWidget(self.lever_ratio)
        self.method_selector = QComboBox()
        self.method_selector.addItems(["Secant Method", "Curve Fitting Method"])
        meta_form.addWidget(QLabel("Calculation Method"))
        meta_form.addWidget(self.method_selector)


        meta_layout.addLayout(meta_form)

        self.table = QTableWidget(14, 4)
        self.table.setHorizontalHeaderLabels(["Load (kN)", "Settlement (mm)", "Cycle Type", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.currentCellChanged.connect(self.handle_cell_changed)
        self.setup_table_rows(14)

        self.add_row_btn = QPushButton("➕ Add Row")
        self.add_row_btn.clicked.connect(self.add_row)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        self.result_label = QLabel("\nResults will be shown here.")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_row_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_fields)
        button_layout.addWidget(clear_btn)

        calc_btn = QPushButton("Evaluate")
        calc_btn.clicked.connect(self.run_selected_method)
        button_layout.addWidget(calc_btn)

        export_btn = QPushButton("Export to PDF")
        export_btn.clicked.connect(lambda: export_to_pdf(self))
        button_layout.addWidget(export_btn)

        maximize_btn = QPushButton("Maximize Graph")
        maximize_btn.clicked.connect(self.show_fullscreen_graph)
        button_layout.addWidget(maximize_btn)

        layout = QVBoxLayout()
        layout.addLayout(meta_layout)
        layout.addWidget(QLabel("Enter Load-Settlement Data:"))
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addWidget(self.canvas)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def setup_table_rows(self, num_rows):
        for row in range(num_rows):
            self.setup_row(row)

    def setup_row(self, row):
        combo = QComboBox()
        combo.addItem("")
        combo.addItems(CYCLE_TYPES)
        self.table.setCellWidget(row, 2, combo)

        delete_btn = QPushButton("🗑")
        delete_btn.clicked.connect(lambda _, r=row: self.confirm_delete_row(r))
        self.table.setCellWidget(row, 3, delete_btn)

    def handle_cell_changed(self, currentRow, currentColumn, previousRow, previousColumn):
        if currentRow == self.table.rowCount() - 1 and currentColumn in [0, 1, 2]:
            self.add_row()

    def add_row(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.setup_row(row_position)

    def confirm_delete_row(self, row):
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete row {row + 1}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.table.removeRow(row)
            for i in range(self.table.rowCount()):
                delete_btn = QPushButton("🗑")
                delete_btn.clicked.connect(lambda _, r=i: self.confirm_delete_row(r))
                self.table.setCellWidget(i, 3, delete_btn)

    def clear_fields(self):
        self.test_id.clear()
        self.plate_diameter.setCurrentIndex(0)
        self.lever_ratio.setText("1.000")
        self.table.setRowCount(14)
        self.setup_table_rows(14)
        for row in range(14):
            for col in range(2):
                self.table.setItem(row, col, QTableWidgetItem(""))
            combo = self.table.cellWidget(row, 2)
            if isinstance(combo, QComboBox):
                combo.setCurrentIndex(0)
        self.ax.clear()
        self.canvas.draw()
        self.result_label.setText("\nResults will be shown here.")

    def show_fullscreen_graph(self):
        self.graph_window = GraphWindow(self.figure)
        self.graph_window.show()

    def run_selected_method(self):
        method = self.method_selector.currentText()
        if method == "DIN 18134 official method (2nd-degree curve fit)":
            from data_handler import evaluate_test_curve_fit
            evaluate_test_curve_fit(self)
        elif method == "Practical Secant Approximation (not DIN 18134)":
            from data_handler import evaluate_test_secant
            evaluate_test_secant(self)

    