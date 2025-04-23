import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from constants import CYCLE_TYPES
from collections import defaultdict

def evaluate_test_secant(app):
    try:
        r = float(app.plate_diameter.currentText()) / 2  # radius in mm
        d = r * 2
        lever = float(app.lever_ratio.text())
        area = np.pi * (d / 1000) ** 2 / 4  # m²
        data_cycles = {cycle: {'loads': [], 'settlements': []} for cycle in CYCLE_TYPES}
        print("\n---- Starting Evaluation ----")
        print(f"Plate diameter: {d} mm (r = {r} mm), Lever ratio: {lever}, Area: {area:.4f} m²")

        for row in range(app.table.rowCount()):
            try:
                load_item = app.table.item(row, 0)
                settl_item = app.table.item(row, 1)
                if not load_item or not settl_item or not load_item.text().strip() or not settl_item.text().strip():
                    continue
                load = float(load_item.text())
                settlement = float(settl_item.text()) * lever
                cycle_type = app.table.cellWidget(row, 2).currentText()
                if not cycle_type:
                    continue
                data_cycles[cycle_type]['loads'].append(load)
                data_cycles[cycle_type]['settlements'].append(settlement)
                print(f"Row {row}: Load={load:.2f} kN, Settlement={settlement:.2f} mm, Type={cycle_type}")
            except Exception:
                continue

        if len(data_cycles["First Loading"]['loads']) < 4 or len(data_cycles["Second Loading"]['loads']) < 2:
            raise ValueError("Not enough data points in first or second loading cycles")

        app.ax.clear()
        group_results = []
        app.ax.set_title("Load-Settlement Curve (DIN 18134 Format)")
        app.ax.set_xlabel("Normal Stress σ (MN/m²)")
        app.ax.set_ylabel("Settlement s (mm)")
        app.ax.grid(True)

        # Custom markers
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

        ev_results = []
        first_cycle_sigma_max = None

        for cycle in CYCLE_TYPES:
            loads = np.array(data_cycles[cycle]['loads'])
            settlements = np.array(data_cycles[cycle]['settlements'])

            if len(loads) < 2:
                continue

            stress = loads / area / 1000  # Convert to MN/m²
            sort_idx = np.argsort(stress)
            stress = stress[sort_idx]
            settlements = settlements[sort_idx]

            # Plot measurement points
            app.ax.plot(stress, settlements, marker=cycle_markers[cycle], linestyle='None',
                        label=cycle, color=colors[cycle])

            if "Loading" in cycle:
                sigma_max = np.max(stress)
                if cycle == "First Loading":
                    first_cycle_sigma_max = sigma_max
                else:
                    sigma_max = first_cycle_sigma_max

                sigma1 = 0.3 * sigma_max
                sigma2 = 0.7 * sigma_max

                # Interpolate to get s1 and s2
                s1 = np.interp(sigma1, stress, settlements)
                s2 = np.interp(sigma2, stress, settlements)

                delta_sigma = sigma2 - sigma1
                delta_s = s2 - s1

                Ev = (0.75 * 300 * delta_sigma) / delta_s  # Ev in MN/m²

                ev_results.append({
                    'cycle': cycle,
                    'Ev': Ev,
                    'sigma_max': sigma_max,
                    'sigma1': sigma1,
                    'sigma2': sigma2,
                    's1': s1,
                    's2': s2
                })

                # Plot secant
                app.ax.plot([sigma1, sigma2], [s1, s2], 'k-', lw=1.5, label=f"{cycle} Secant")

                # Annotations
                for val, label in zip([sigma1, sigma2, sigma_max], ["σ₁", "σ₂", "σ₃=σ_max"]):
                    app.ax.axvline(x=val, color='black', linestyle=':', linewidth=0.8)
                    app.ax.text(val, app.ax.get_ylim()[0], label, rotation=0, ha='center', va='bottom')

        # Finalize plot
        app.ax.legend()
        app.ax.invert_yaxis()
        app.canvas.draw()

        group_results.append(f"<b>Plate Radius:</b> {r:.1f} mm (Diameter: {d:.0f} mm)")

        for ev in ev_results:
            group_results.append(
                f"<b>{ev['cycle']}:</b><br>"
                f"&nbsp;&nbsp;Ev = <b>{ev['Ev']:.2f} MN/m²</b><br>"
                f"&nbsp;&nbsp;σ₁ = {ev['sigma1']:.3f}, σ₂ = {ev['sigma2']:.3f}<br>"
                f"&nbsp;&nbsp;s₁ = {ev['s1']:.3f}, s₂ = {ev['s2']:.3f}"
            )

        # General Ev ratio
        ev1 = next((ev['Ev'] for ev in ev_results if ev['cycle'] == "First Loading"), None)
        ev2 = next((ev['Ev'] for ev in ev_results if ev['cycle'] == "Second Loading"), None)

        if ev1 and ev2:
            ev_ratio = ev2 / ev1
            group_results.append(
                f"<b>General Ev Ratio (Ev2 / Ev1):</b> <b>{ev_ratio:.2f}</b>"
            )

        app.result_label.setText("<br><br>".join(result_lines))
        print("---- Evaluation Done ----\n")

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

        grouped_data = defaultdict(lambda: {cycle: {'loads': [], 'settlements': []} for cycle in CYCLE_TYPES})

        for row in range(app.table.rowCount()):
            try:
                load_item = app.table.item(row, 0)
                settl_item = app.table.item(row, 1)
                cycle_combo = app.table.cellWidget(row, 2)
                station_widget = app.table.cellWidget(row, 3)
                side_widget = app.table.cellWidget(row, 4)

                if not all([load_item, settl_item, cycle_combo, station_widget, side_widget]):
                    continue

                load_text = load_item.text().strip()
                settl_text = settl_item.text().strip()
                station = station_widget.text().strip()
                side = side_widget.text().strip()
                cycle_type = cycle_combo.currentText().strip()

                if cycle_type not in CYCLE_TYPES:
                    continue

                load = float(load_text)
                settlement = float(settl_text) * lever
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
        color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
        cycle_markers = {
            "First Loading": "o",
            "Unloading": "s",
            "Second Loading": "^"
        }

        for group_index, ((station, side), data_cycles) in enumerate(grouped_data.items()):
            fig, ax = plt.subplots()
            ax.set_title(f"{station} - {side} | Load-Settlement Curve")
            ax.set_xlabel("Normal Stress σ (MN/m²)")
            ax.set_ylabel("Settlement s (mm)")
            ax.grid(True)

            group_result_lines = [f"<b>Group: Station={station}, Side={side}</b>"]
            ev_results = []
            cycle_colors = {cycle: color_cycle[i % len(color_cycle)] for i, cycle in enumerate(CYCLE_TYPES)}
            first_cycle_sigma_max = None

            for cycle in CYCLE_TYPES:
                loads = np.array(data_cycles[cycle]['loads'])
                settlements = np.array(data_cycles[cycle]['settlements'])

                if len(loads) < 2:
                    continue

                stress = loads / area / 1000
                sort_idx = np.argsort(stress)
                stress = stress[sort_idx]
                settlements = settlements[sort_idx]

                ax.plot(stress, settlements,
                        marker=cycle_markers[cycle],
                        linestyle='None',
                        label=f"{cycle}",
                        color=cycle_colors[cycle])

                if "Loading" in cycle:
                    fit_stress = stress
                    fit_settl = settlements
                    if cycle == "First Loading" and len(stress) > 2:
                        fit_stress = stress[1:]
                        fit_settl = settlements[1:]

                    coeffs = np.polyfit(fit_stress, fit_settl, 2)
                    a2, a1, a0 = coeffs

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

                    sigma_range = np.linspace(np.min(fit_stress), np.max(fit_stress), 200)
                    fit_curve = a0 + a1 * sigma_range + a2 * sigma_range ** 2
                    ax.plot(sigma_range, fit_curve, '--', color=cycle_colors[cycle],
                            label=f"{cycle} Fit")

                    if cycle == "First Loading":
                        sigma1 = 0.3 * sigma_max
                        sigma2 = 0.7 * sigma_max
                        s1 = a0 + a1 * sigma1 + a2 * sigma1 ** 2
                        s2 = a0 + a1 * sigma2 + a2 * sigma2 ** 2
                        ax.plot([sigma1, sigma2], [s1, s2], 'k-', lw=1.5)

                        for val, label in zip([sigma1, sigma2, sigma_max], ["σ₁", "σ₂", "σ₃=σ_max"]):
                            ax.axvline(x=val, color='black', linestyle=':', linewidth=0.8)
                            ax.text(val, ax.get_ylim()[0], label, rotation=0, ha='center', va='bottom')

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

            group_result_lines.append("<hr>")
            result_lines.extend(group_result_lines)

            ax.legend()
            ax.invert_yaxis()

            canvas = FigureCanvas(fig)

            # Group Page Widget
            page_widget = QWidget()
            page_layout = QVBoxLayout()

            page_layout.addWidget(canvas)

            result_lbl = QLabel("<br>".join(group_result_lines))
            result_lbl.setWordWrap(True)
            result_lbl.setTextFormat(Qt.RichText)
            page_layout.addWidget(result_lbl)

            page_widget.setLayout(page_layout)
            app.graphs_stack.addWidget(page_widget)

        if app.graphs_stack.count() > 0:
            app.graphs_stack.setCurrentIndex(0)

    except Exception as e:
        print("!!! ERROR:", str(e))
        QMessageBox.critical(app, "Evaluation Error", str(e))