import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QMessageBox
)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

CYCLE_TYPES = [
    "First Loading",
    "Unloading",
    "Second Loading",
    "Third Loading (optional)"
]

class PlateLoadTestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DIN 18134 - Plate Load Test")
        self.setMinimumSize(1100, 750)
        self.init_ui()

    def init_ui(self):
        # --- Metadata Section ---
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

        meta_layout.addLayout(meta_form)

        # --- Data Entry Table ---
        self.table = QTableWidget(16, 3)
        self.table.setHorizontalHeaderLabels(["Load (kN)", "Settlement (mm)", "Cycle Type"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row in range(self.table.rowCount()):
            combo = QComboBox()
            combo.addItems(CYCLE_TYPES)
            self.table.setCellWidget(row, 2, combo)

        # --- Plot Area ---
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # --- Evaluation Result ---
        self.result_label = QLabel("\nResults will be shown here.")

        # --- Buttons ---
        button_layout = QHBoxLayout()
        calc_btn = QPushButton("Evaluate")
        calc_btn.clicked.connect(self.evaluate_test)
        button_layout.addWidget(calc_btn)

        # --- Main Layout ---
        layout = QVBoxLayout()
        layout.addLayout(meta_layout)
        layout.addWidget(QLabel("Enter Load-Settlement Data:"))
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addWidget(self.canvas)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def evaluate_test(self):
        try:
            r = float(self.plate_diameter.currentText()) / 2  # radius in mm
            d = r * 2
            lever = float(self.lever_ratio.text())
            area = np.pi * (d / 1000) ** 2 / 4  # m²

            # Gather data per cycle
            data_cycles = {cycle: {'loads': [], 'settlements': []} for cycle in CYCLE_TYPES}

            print("\n---- Starting Evaluation ----")
            print(f"Plate diameter: {d} mm (r = {r} mm), Lever ratio: {lever}, Area: {area:.4f} m²")

            for row in range(self.table.rowCount()):
                try:
                    load_item = self.table.item(row, 0)
                    settl_item = self.table.item(row, 1)
                    if load_item is None or settl_item is None:
                        continue
                    load = float(load_item.text())
                    settlement = float(settl_item.text()) * lever
                    cycle_type = self.table.cellWidget(row, 2).currentText()
                    data_cycles[cycle_type]['loads'].append(load)
                    data_cycles[cycle_type]['settlements'].append(settlement)
                    print(f"Row {row}: Load={load:.2f} kN, Settlement={settlement:.2f} mm, Type={cycle_type}")
                except Exception as e:
                    # skip empty or invalid row
                    continue

            # At least 4 points in the most important cycles
            if len(data_cycles["First Loading"]['loads']) < 4 or len(data_cycles["Second Loading"]['loads']) < 2:
                raise ValueError("Not enough data points in first or second loading cycles")

            # Prepare for plotting
            self.ax.clear()

            result_lines = []
            colors = {
                "First Loading": "blue",
                "Unloading": "gray",
                "Second Loading": "green",
                "Third Loading (optional)": "orange"
            }
            ev_results = []


            first_cycle_sigma_max = None

            for idx, cycle in enumerate(CYCLE_TYPES):
                loads = np.array(data_cycles[cycle]['loads'])
                settlements = np.array(data_cycles[cycle]['settlements'])
                if len(loads) < 2:
                    continue  # skip empty cycles
            
                # Convert to stress (MN/m²)
                stress = loads / area / 1000  # MN/m²
            
                # Sort by stress
                sort_idx = np.argsort(stress)
                stress = stress[sort_idx]
                settlements = settlements[sort_idx]
                loads = loads[sort_idx]
            
                # Plot measured points
                self.ax.plot(settlements, loads, 'o-', label=f"{cycle} (measured)", color=colors[cycle], alpha=0.7)
            
                # Only "loading" cycles get polynomial fit and Ev
                if "Loading" in cycle:
                    # Special: DIN says for 1st fit, skip the first point(!)
                    fit_stress = stress
                    fit_settl = settlements
                    if cycle == "First Loading" and len(stress) > 2:
                        fit_stress = stress[1:]  # skip very first point per DIN
                        fit_settl = settlements[1:]
            
                    # Fit quadratic: settlement = a0 + a1*σ + a2*σ²
                    coeffs = np.polyfit(fit_stress, fit_settl, 2)
                    a2, a1, a0 = coeffs
            
                    # Calculate sigma_max for Ev
                    if cycle == "First Loading":
                        sigma_max = np.max(fit_stress)
                        first_cycle_sigma_max = sigma_max  # Store for use in later cycles
                    else:
                        sigma_max = first_cycle_sigma_max  # Use first cycle's sigma_max
            
                    Ev = (1.5 * r) / (a1 + a2 * sigma_max)  # in kN/m² (since r in mm)
                    print(f"[{cycle}] sigma_max = {sigma_max:.4f} MN/m²; Ev = {Ev:.2f} kN/m²")
            
                    # Save result for display
                    ev_results.append({
                        'cycle': cycle,
                        'Ev': Ev,
                        'a0': a0,
                        'a1': a1,
                        'a2': a2,
                        'sigma_max': sigma_max
                    })
            
                    # Plot fit
                    sigma_range = np.linspace(np.min(fit_stress), np.max(fit_stress), 200)
                    fit_settlement = a0 + a1 * sigma_range + a2 * sigma_range ** 2
                    fit_loads = sigma_range * area * 1000  # back to kN
                    self.ax.plot(fit_settlement, fit_loads, '--', color=colors[cycle], label=f"{cycle} Fit")
            
            self.ax.set_xlabel("Settlement (mm)")
            self.ax.set_ylabel("Load (kN)")
            self.ax.set_title("Load-Settlement Curve (DIN 18134)")
            self.ax.legend()
            self.canvas.draw()

            # Format result text
            result_lines.append(f"<b>Plate Radius:</b> {r:.1f} mm (Diameter: {d:.0f} mm)")
            for ev in ev_results:
                result_lines.append(
                    f"<b>{ev['cycle']}:</b><br>"
                    f"&nbsp;&nbsp;Ev = <b>{ev['Ev']:.2f} kN/m²</b><br>"
                    f"&nbsp;&nbsp;a0 = {ev['a0']:.4f}, a1 = {ev['a1']:.4f}, a2 = {ev['a2']:.4f}<br>"
                    f"&nbsp;&nbsp;sigma_max = {ev['sigma_max']:.4f} MN/m²"
                )
            self.result_label.setText("<br><br>".join(result_lines))
            print("---- Evaluation Done ----\n")

        except Exception as e:
            print("!!! ERROR:", str(e))
            QMessageBox.critical(self, "Evaluation Error", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlateLoadTestApp()
    window.show()
    sys.exit(app.exec_())