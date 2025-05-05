import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMessageBox, QLabel, QTableWidget, QTableWidgetItem, QSizePolicy, QHBoxLayout, QAbstractScrollArea, QAbstractItemView
from PyQt5.QtCore import Qt
from constants import CYCLE_TYPES
from collections import defaultdict
import warnings
from numpy.polynomial import Polynomial
from numpy.polynomial.polynomial import polyfit as np_polyfit
import numpy.linalg as linalg
from sklearn.metrics import r2_score

def evaluate_test_secant(app):
    try:
        r = float(app.plate_diameter.currentText()) / 2  # radius in mm
        d = r * 2
        lever = float(app.lever_ratio.text())
        area = np.pi * (d / 1000) ** 2 / 4  # m²

        CYCLE_TYPES = ["First Loading", "Unloading", "Second Loading"]
        grouped_data = defaultdict(lambda: {cycle: {'loads': [], 'settlements': []} for cycle in CYCLE_TYPES})
        app.summary_results = []

        for row in range(app.table.rowCount()):
            try:
                load_item = app.table.item(row, 0)
                settl_item = app.table.item(row, 1)
                cycle_combo = app.table.cellWidget(row, 2)
                station_widget = app.table.cellWidget(row, 3)
                side_widget = app.table.cellWidget(row, 4)

                if not all([load_item, settl_item, cycle_combo, station_widget, side_widget]):
                    continue

                load = float(load_item.text())
                settlement = float(settl_item.text()) * lever
                cycle_type = cycle_combo.currentText().strip()
                station = station_widget.text().strip()
                side = side_widget.text().strip()

                if cycle_type not in CYCLE_TYPES:
                    continue

                key = (station, side)
                grouped_data[key][cycle_type]['loads'].append(load)
                grouped_data[key][cycle_type]['settlements'].append(settlement)
            except Exception:
                continue

        if not grouped_data:
            raise ValueError("No valid data found")

        while app.graphs_stack.count():
            widget = app.graphs_stack.widget(0)
            app.graphs_stack.removeWidget(widget)
            widget.deleteLater()

        cycle_markers = {
            "First Loading": "o",
            "Unloading": "s",
            "Second Loading": "^"
        }

        colors = {
            "First Loading": "blue",
            "Unloading": "gray",
            "Second Loading": "green",
        }

        for (station, side), data_cycles in grouped_data.items():
            group_raw_points = []
            fig, ax = plt.subplots()
            SMALL_SIZE = 7
            MEDIUM_SIZE = 7
            BIGGER_SIZE = 8
            marker_size = 3
            line_width = 0.85
            
            plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
            plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
            plt.rc('axes', labelsize=MEDIUM_SIZE)     # fontsize of the x and y labels
            plt.rc('xtick', labelsize=SMALL_SIZE)      # fontsize of the tick labels
            plt.rc('ytick', labelsize=SMALL_SIZE)      # fontsize of the tick labels
            plt.rc('legend', fontsize=SMALL_SIZE)      # legend fontsize
            plt.rc('figure', titlesize=BIGGER_SIZE)    # fontsize of the figure title

            ax.set_title(f"{station} - {side} | Load-Settlement Curve (Secant Method)", pad=13)
            ax.set_xlabel("Normal Stress σ (MN/m²)")
            ax.set_ylabel("Settlement s (mm)")
            ax.xaxis.label.set_size(7)
            ax.yaxis.label.set_size(7)
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.tick_params(axis='both', which='minor', labelsize=6)
            ax.grid(True)

            group_result_lines = [f"<b>Group: Station={station}, Side={side}</b>", f"<b>Plate Radius:</b> {r:.1f} mm (Diameter: {d:.0f} mm)"]
            ev_results = []
            first_cycle_sigma_max = None

            for cycle in CYCLE_TYPES:

                for l, s in zip(data_cycles[cycle]['loads'], data_cycles[cycle]['settlements']):
                    group_raw_points.append((l, s, cycle))

                loads = np.array(data_cycles[cycle]['loads'])
                settlements = np.array(data_cycles[cycle]['settlements'])

                if len(loads) < 2:
                    continue

                stress = loads / area / 1000  # Convert to MN/m²
                sort_idx = np.argsort(stress)
                stress = stress[sort_idx]
                settlements = settlements[sort_idx]

                ax.plot(stress, settlements, marker=cycle_markers[cycle], linestyle='None',
                        label=cycle, color=colors[cycle], markersize=marker_size, linewidth=line_width)

                # Use actual data only, i.e., skip preload from fit if desired
                fit_stress = stress[1:] if cycle == "First Loading" and len(stress) > 2 else stress
                fit_settlements = settlements[1:] if cycle == "First Loading" and len(settlements) > 2 else settlements

                if cycle == "First Loading":
                    # Mark the actual first point (optional)
                    ax.plot(stress[0], settlements[0], marker='o', color='gray', markersize=marker_size, linewidth=line_width)
                    ax.annotate('Preload', xy=(stress[0], settlements[0]), xytext=(5, 5),
                                textcoords='offset points', fontsize=6.5, color='gray')

                if len(fit_stress) >= 3:
                    coeffs = np.polyfit(fit_stress, fit_settlements, 2)
                    poly_curve = np.poly1d(coeffs)
                    sigma_min = np.min(fit_stress)
                    sigma_max = np.max(fit_stress)
                    sigma_range = np.linspace(0, 1.2 * sigma_max, 200)
                    settlement_fit = poly_curve(sigma_range)
                    ax.plot(sigma_range, settlement_fit, linestyle='--', color=colors[cycle], label=f"{cycle} Fit", markersize=marker_size, linewidth=line_width)

                if "Loading" in cycle:
                    sigma_max = np.max(stress)
                    if cycle == "First Loading":
                        first_cycle_sigma_max = sigma_max
                    else:
                        sigma_max = first_cycle_sigma_max

                    sigma1 = 0.3 * sigma_max
                    sigma2 = 0.7 * sigma_max

                    s1 = np.interp(sigma1, stress, settlements)
                    s2 = np.interp(sigma2, stress, settlements)

                    delta_sigma = sigma2 - sigma1
                    delta_s = s2 - s1
                    Ev = (0.75 * d * delta_sigma) / delta_s  # Ev in MN/m²

                    ev_results.append({
                        'cycle': cycle,
                        'Ev': Ev,
                        'sigma_max': sigma_max,
                        'sigma1': sigma1,
                        'sigma2': sigma2,
                        's1': s1,
                        's2': s2
                    })

                    ax.plot([sigma1, sigma2], [s1, s2], 'k-', label=f"{cycle} Secant", markersize=marker_size, linewidth=line_width)
                    
                    # Vertical reference lines and labels at σ₁, σ₂, σ₃=σ_max
                    for val, label in zip(
                        [sigma1, sigma2, sigma_max],
                        ["σ₁", "σ₂", "σ₃=σ_max"]
                    ):
                        ax.axvline(x=val, color='black', linestyle=':', linewidth=0.6)
                        ax.text(val, 1.005, label, rotation=0, ha='center', va='bottom', transform=ax.get_xaxis_transform(), fontsize=7)

                    # Horizontal lines at s₁ and s₂
                    ax.axhline(y=s1, color='black', linestyle=':', linewidth=0.6)
                    ax.axhline(y=s2, color='black', linestyle=':', linewidth=0.6)
                    
                    x_pos = -0.015  # Negative value means a little outside of plot
                        
                    for s_val, s_label in zip([s1, s2], [f"s₁ ({cycle[0]})", f"s₂ ({cycle[0]})"]):
                        ax.text(x_pos, s_val, s_label, va='center', ha='right', transform=ax.get_yaxis_transform(), fontsize=7, clip_on=False)

            for ev in ev_results:
                group_result_lines.append(
                    f"&nbsp;&nbsp;<b>{ev['cycle']}:</b> Ev = <b>{ev['Ev']:.2f} MN/m²</b><br>"
                    f"&nbsp;&nbsp;σ₁ = {ev['sigma1']:.3f}, σ₂ = {ev['sigma2']:.3f}<br>"
                    f"&nbsp;&nbsp;s₁ = {ev['s1']:.3f}, s₂ = {ev['s2']:.3f}"
                )

            ev1 = next((ev['Ev'] for ev in ev_results if ev['cycle'] == "First Loading"), None)
            ev2 = next((ev['Ev'] for ev in ev_results if ev['cycle'] == "Second Loading"), None)

            if ev1 and ev2:
                group_result_lines.append(f"<b>&nbsp;&nbsp;Ev Ratio (Ev2 / Ev1):</b> {ev2 / ev1:.2f}")

            group_result_lines.append("<hr>")

            if ev1 and ev2:
                app.summary_results.append({
                    'station': station,
                    'side': side,
                    'material': app.material_type.text(),
                    'ev1': ev1,
                    'ev2': ev2,
                    'ev2_ev1_ratio': ev2 / ev1
                })

            ax.legend(fontsize=6, markerscale=0.7, handlelength=0.7)
            ax.invert_yaxis()

            fig.tight_layout()

            canvas = FigureCanvas(fig)
            page_widget = QWidget()
            page_widget.group_raw_points = group_raw_points
            page_layout = QVBoxLayout()
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(5)
            canvas.setMinimumHeight(300)
            page_layout.addWidget(canvas, stretch=1)

            ev_table = QTableWidget()
            ev_table.setObjectName("evResultsTable")
            ev_table.setColumnCount(8)
            ev_table.setHorizontalHeaderLabels([
                " Cycle ", " σ₃ (MN/m²) ", " σ₁ (MN/m²) ", " σ₂ (MN/m²) ", " s₁ (mm) ", " s₂ (mm) ", " Ev (MN/m²) ", " Ev₂/Ev₁ "
            ])

            ev_table.verticalHeader().setVisible(False)
            ev_table.verticalHeader().setDefaultSectionSize(0)
            ev_table.setEditTriggers(QTableWidget.NoEditTriggers)
            ev_table.setSelectionMode(QTableWidget.NoSelection)
            ev_table.setFocusPolicy(Qt.NoFocus)
            ev_table.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            ev_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            ev_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            ev_table.horizontalHeader().setStretchLastSection(False)
            ev_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
            ev_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
            
            # Fill the table
            ev_table.setRowCount(len(ev_results))
            for i, ev in enumerate(ev_results):
                ev_table.setItem(i, 0, QTableWidgetItem(ev['cycle']))
                ev_table.setItem(i, 1, QTableWidgetItem(f"{ev['sigma_max']:.3f}"))
                ev_table.setItem(i, 2, QTableWidgetItem(f"{ev['sigma1']:.3f}"))
                ev_table.setItem(i, 3, QTableWidgetItem(f"{ev['sigma2']:.3f}"))
                ev_table.setItem(i, 4, QTableWidgetItem(f"{ev['s1']:.3f}"))
                ev_table.setItem(i, 5, QTableWidgetItem(f"{ev['s2']:.3f}"))
                ev_table.setItem(i, 6, QTableWidgetItem(f"{ev['Ev']:.2f}"))
            
            # Add merged Ev2/Ev1 value in the last column
            if ev1 and ev2:
                ev2_ev1_value = f"{ev2 / ev1:.2f}"
                merged_item = QTableWidgetItem(ev2_ev1_value)
                merged_item.setTextAlignment(Qt.AlignCenter)
                ev_table.setItem(0, 7, merged_item)
                ev_table.setSpan(0, 7, len(ev_results), 1)
            # Resize
            ev_table.resizeColumnsToContents()
            ev_table.resizeRowsToContents()
            ev_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            ev_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            
            # Center table
            table_container = QHBoxLayout()
            table_container.setSpacing(0)
            table_container.setContentsMargins(0, 0, 0, 0)
            table_container.addStretch(1) 
            table_container.addWidget(ev_table)
            table_container.addStretch(1)
            table_container.setAlignment(Qt.AlignCenter) 
            
            page_layout.addLayout(table_container, stretch=0)

            page_widget.setLayout(page_layout)
            page_widget.setContentsMargins(0, 0, 0, 0)
            app.graphs_stack.addWidget(page_widget)

        if app.graphs_stack.count() > 0:
            app.graphs_stack.setCurrentIndex(0)

    except Exception as e:
        print("!!! ERROR:", str(e))
        QMessageBox.critical(app, "Evaluation Error", str(e))
        

def evaluate_test_curve_fit(app):
    try:
        r = float(app.plate_diameter.currentText()) / 2
        d = r * 2
        lever = float(app.lever_ratio.text())
        area = np.pi * (d / 1000) ** 2 / 4  # m²

        CYCLE_TYPES = ["First Loading", "Unloading", "Second Loading"]
        SIGMA_RATIO_1 = 0.3
        SIGMA_RATIO_2 = 0.7

        grouped_data = defaultdict(lambda: {cycle: {'loads': [], 'settlements': []} for cycle in CYCLE_TYPES})
        app.summary_results = []

        for row in range(app.table.rowCount()):
            try:
                load_item = app.table.item(row, 0)
                settl_item = app.table.item(row, 1)
                cycle_combo = app.table.cellWidget(row, 2)
                station_widget = app.table.cellWidget(row, 3)
                side_widget = app.table.cellWidget(row, 4)

                if not all([load_item, settl_item, cycle_combo, station_widget, side_widget]):
                    continue

                load = float(load_item.text().strip())
                settlement = float(settl_item.text().strip()) * lever
                station = station_widget.text().strip()
                side = side_widget.text().strip()
                cycle_type = cycle_combo.currentText().strip()

                if cycle_type not in CYCLE_TYPES:
                    continue

                key = (station, side)
                grouped_data[key][cycle_type]['loads'].append(load)
                grouped_data[key][cycle_type]['settlements'].append(settlement)
            except Exception:
                continue

        if not grouped_data:
            raise ValueError("No valid data found")

        while app.graphs_stack.count():
            widget = app.graphs_stack.widget(0)
            app.graphs_stack.removeWidget(widget)
            widget.deleteLater()

        result_lines = []
        cycle_markers = {"First Loading": "o", "Unloading": "s", "Second Loading": "^"}
        cycle_colors = {"First Loading": "#1f77b4", "Unloading": "#7f7f7f", "Second Loading": "#2ca02c"}

        for (station, side), data_cycles in grouped_data.items():
            group_raw_points = []
            fig, ax = plt.subplots()
            SMALL_SIZE = 7
            MEDIUM_SIZE = 7
            BIGGER_SIZE = 8
            marker_size = 3
            line_width_curve = 0.85
            
            plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
            plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
            plt.rc('axes', labelsize=MEDIUM_SIZE)     # fontsize of the x and y labels
            plt.rc('xtick', labelsize=SMALL_SIZE)      # fontsize of the tick labels
            plt.rc('ytick', labelsize=SMALL_SIZE)      # fontsize of the tick labels
            plt.rc('legend', fontsize=SMALL_SIZE)      # legend fontsize
            plt.rc('figure', titlesize=BIGGER_SIZE)    # fontsize of the figure title

            ax.set_title(f"{station} - {side} | Load-Settlement Curve", pad=13)
            ax.set_xlabel("Normal Stress σ (MN/m²)")
            ax.set_ylabel("Settlement s (mm)")
            ax.xaxis.label.set_size(7)
            ax.yaxis.label.set_size(7)
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.tick_params(axis='both', which='minor', labelsize=6)

            ax.grid(True)

            group_result_lines = [f"<b>Group: Station={station}, Side={side}</b>"]
            ev_results = []
            first_cycle_sigma_max = None

            for cycle in CYCLE_TYPES:
  
                for l, s in zip(data_cycles[cycle]['loads'], data_cycles[cycle]['settlements']):
                    group_raw_points.append((l, s, cycle))
                
                loads = np.array(data_cycles[cycle]['loads'])
                settlements = np.array(data_cycles[cycle]['settlements'])

                if len(loads) < 2:
                    continue

                stress = loads / area / 1000
                sort_idx = np.argsort(stress)
                stress = stress[sort_idx]
                settlements = settlements[sort_idx]

                if cycle == "First Loading":
                    ax.plot(stress[1:], settlements[1:], marker=cycle_markers[cycle],
                            linestyle='None', label=f"{cycle}", color=cycle_colors[cycle], markersize=marker_size, linewidth=line_width_curve)
                    ax.plot(stress[0], settlements[0], 'x', color='gray', label="Preload point", markersize=marker_size, linewidth=line_width_curve)
                else:
                    ax.plot(stress, settlements, marker=cycle_markers[cycle],
                            linestyle='None', label=f"{cycle}", color=cycle_colors[cycle], markersize=marker_size, linewidth=line_width_curve)

                # Fit curve for all cycles (including Unloading)
                if cycle == "First Loading" and len(stress) > 2:
                    fit_stress = stress[1:]
                    fit_settl = settlements[1:]
                else:
                    fit_stress = stress
                    fit_settl = settlements


                coeffs, fit_successful, fit_pred = safe_polyfit(fit_stress, fit_settl, degree=2)
                
                if not fit_successful:
                    print(f"⚠️ Fallback to secant: Fit failed or too few points")
                    from data_handler import evaluate_test_secant
                    evaluate_test_secant(app)
                    return
                
                # Check R² threshold (0.95)
                r2 = r2_score(fit_settl, fit_pred)
                print(f"R² for {cycle}: {r2:.3f}")
                if r2 < 0.95:
                    print(f"⚠️ Fallback to secant: Bad fit quality (R²={r2:.3f})")
                    from data_handler import evaluate_test_secant
                    evaluate_test_secant(app)
                    return
                
                if not fit_successful:
                    # Fallback to secant method if curve fit failed
                    from data_handler import evaluate_test_secant
                    evaluate_test_secant(app)
                    return  # Exit current function
                else:
                    a2, a1, a0 = coeffs

                sigma_range = np.linspace(np.min(stress), np.max(stress), 200)
                fit_curve = a0 + a1 * sigma_range + a2 * sigma_range ** 2
                ax.plot(sigma_range, fit_curve, '-', color=cycle_colors[cycle], label=f"{cycle} Fit", linewidth=line_width_curve)

                # Ev calculation only for Loading cycles
                if "Loading" in cycle:
                    if cycle == "First Loading":
                        sigma_max = np.max(fit_stress)
                        first_cycle_sigma_max = sigma_max
                    else:
                        sigma_max = first_cycle_sigma_max

                    Ev = (1.5 * r) / (a1 + a2 * sigma_max)
                    ev_results.append({
                        'cycle': cycle,
                        'Ev': Ev,
                        'a0': a0,
                        'a1': a1,
                        'a2': a2,
                        'sigma_max': sigma_max
                    })

                    if cycle == "First Loading":
                        sigma1 = SIGMA_RATIO_1 * sigma_max
                        sigma2 = SIGMA_RATIO_2 * sigma_max
                        s1 = a0 + a1 * sigma1 + a2 * sigma1 ** 2
                        s2 = a0 + a1 * sigma2 + a2 * sigma2 ** 2
                    
                        # Plot secant line between (σ₁, s₁) and (σ₂, s₂)
                        ax.plot([sigma1, sigma2], [s1, s2], 'k-', linewidth=line_width_curve)
                    
                        # Vertical reference lines and labels at σ₁, σ₂, σ₃=σ_max
                        for val, label in zip(
                            [sigma1, sigma2, sigma_max],
                            [f"σ₁ ({SIGMA_RATIO_1:.1f}σ₃)", f"σ₂ ({SIGMA_RATIO_2:.1f}σ₃)", "σ₃=σ_max"]
                        ):
                            ax.axvline(x=val, color='black', linestyle=':', linewidth=0.6)
                            ax.text(val, 1.005, label, rotation=0, ha='center', va='bottom', transform=ax.get_xaxis_transform())

                        # Horizontal lines at s₁ and s₂
                        ax.axhline(y=s1, color='black', linestyle=':', linewidth=0.6)
                        ax.axhline(y=s2, color='black', linestyle=':', linewidth=0.6)
                        # Label s1 and s2 on the y-axis
                        x_pos = -0.015
                        
                        ax.text(x_pos, s1, "s₁", va='center', ha='right', transform=ax.get_yaxis_transform(), fontsize=7, clip_on=False)
                        ax.text(x_pos, s2, "s₂", va='center', ha='right', transform=ax.get_yaxis_transform(), fontsize=7, clip_on=False)
                        
            for ev in ev_results:
                group_result_lines.append(
                    f"&nbsp;&nbsp;<b>{ev['cycle']}:</b> Ev = {ev['Ev']:.2f} MN/m²<br>"
                    f"&nbsp;&nbsp;a0 = {ev['a0']:.4f}, a1 = {ev['a1']:.4f}, a2 = {ev['a2']:.4f}<br>"
                    f"&nbsp;&nbsp;σ₃ = {ev['sigma_max']:.4f} MN/m²"
                )

            ev1 = next((ev['Ev'] for ev in ev_results if ev['cycle'] == "First Loading"), None)
            ev2 = next((ev['Ev'] for ev in ev_results if ev['cycle'] == "Second Loading"), None)
            if ev1 and ev2:
                group_result_lines.append(f"<b>&nbsp;&nbsp;Ev Ratio (Ev2 / Ev1):</b> {ev2 / ev1:.2f}")

            if ev1 and ev2:
                app.summary_results.append({
                    'station': station,
                    'side': side,
                    'material': app.material_type.text(),
                    'ev1': ev1,
                    'ev2': ev2,
                    'ev2_ev1_ratio': ev2 / ev1
                })

                
            group_result_lines.append("<hr>")
            result_lines.extend(group_result_lines)

            ax.legend(fontsize=6, markerscale=0.7, handlelength=0.7)
            ax.invert_yaxis()

            fig.tight_layout()

            canvas = FigureCanvas(fig)
            page_widget = QWidget()
            page_widget.group_raw_points = group_raw_points
            page_layout = QVBoxLayout()
            page_layout.addWidget(canvas)
            # Create styled table for Ev results
            ev_table = QTableWidget()
            ev_table.setObjectName("evResultsTable")
            ev_table.setColumnCount(7)
            ev_table.setHorizontalHeaderLabels([
                " Cycle ", " σ₃ (MN/m²) ", " a₀ ", " a₁ ", " a₂ ", " Ev (MN/m²) ", " Ev₂ / Ev₁ "
            ])
            ev_table.verticalHeader().setVisible(False)
            ev_table.verticalHeader().setDefaultSectionSize(0)
            ev_table.setEditTriggers(QTableWidget.NoEditTriggers)
            ev_table.setSelectionMode(QTableWidget.NoSelection)
            ev_table.setFocusPolicy(Qt.NoFocus)
            
            ev_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Populate rows
            ev_table.setRowCount(len(ev_results))
            for i, ev in enumerate(ev_results):
                if ev['cycle'] == "1":
                    cycle_text = "First Loading"
                elif ev['cycle'] == "2":
                    cycle_text = "Second Loading"
                else:
                    cycle_text = ev['cycle'] 
                     
                ev_table.setItem(i, 0, QTableWidgetItem(cycle_text))
                ev_table.setItem(i, 1, QTableWidgetItem(f" {ev['sigma_max']:.3f} "))
                ev_table.setItem(i, 2, QTableWidgetItem(f" {ev['a0']:.4f} "))
                ev_table.setItem(i, 3, QTableWidgetItem(f" {ev['a1']:.4f} "))
                ev_table.setItem(i, 4, QTableWidgetItem(f" {ev['a2']:.4f} "))
                ev_table.setItem(i, 5, QTableWidgetItem(f" {ev['Ev']:.1f} "))
            
            # Merge Ev2/Ev1 column
            if ev1 and ev2:
                ev2_ev1_value = f" {ev2 / ev1:.2f} "
            
                merged_item = QTableWidgetItem(ev2_ev1_value)
                merged_item.setTextAlignment(Qt.AlignCenter)
                ev_table.setItem(0, 6, merged_item)
            
                # Merge the Ev2/Ev1 column cells vertically across all rows
                ev_table.setSpan(0, 6, len(ev_results), 1)
            
            # Add table to layout
            ev_table.resizeColumnsToContents()

            total_width = sum([ev_table.columnWidth(i) for i in range(ev_table.columnCount())])
            ev_table.setMinimumWidth(total_width + ev_table.verticalHeader().width() + 2)

            ev_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            ev_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            ev_table.horizontalHeader().setStretchLastSection(False)
            ev_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
            ev_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
            
            # Resize rows to content
            ev_table.resizeRowsToContents()
            
            ev_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            table_container = QHBoxLayout()
            table_container.addStretch(1)
            table_container.addWidget(ev_table)
            table_container.addStretch(1)
            page_layout.addLayout(table_container)

            page_layout.addStretch(1)
            page_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            page_widget.setLayout(page_layout)
            app.graphs_stack.addWidget(page_widget)

        if app.graphs_stack.count() > 0:
            app.graphs_stack.setCurrentIndex(0)

    except Exception as e:
        print("!!! ERROR:", str(e))
        QMessageBox.critical(app, "Evaluation Error", str(e))


def safe_polyfit(x, y, degree=2):
    if len(x) < degree + 1:
        return None, False, None

    x_mean = np.mean(x)
    x_std = np.std(x)
    if x_std == 0:
        return None, False, None

    x_norm = (x - x_mean) / x_std

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        coeffs_norm = np.polyfit(x_norm, y, degree)

        for w in caught_warnings:
            if "polyfit may be poorly conditioned" in str(w.message).lower():
                return None, False, None

    # Convert normalized poly back to original scale
    p = np.poly1d(coeffs_norm)
    t = np.poly1d([1 / x_std, -x_mean / x_std])  # t(x) = (x - mean)/std
    p_orig = p(t)

    y_pred = p_orig(x)

    return p_orig.coefficients, True, y_pred