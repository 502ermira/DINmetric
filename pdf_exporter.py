from matplotlib.backends.backend_pdf import PdfPages
from PyQt5.QtWidgets import QFileDialog
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime
import io
A4_SIZE = (8.27, 11.69)

def export_to_pdf(app):
    if app.graphs_stack.count() == 0:
        return

    file_path, _ = QFileDialog.getSaveFileName(app, "Save PDF", "", "PDF Files (*.pdf)")
    if not file_path:
        return
    if not file_path.endswith('.pdf'):
        file_path += '.pdf'

    with PdfPages(file_path) as pdf:
        ## --- PAGE 1: Metadata Page with 2 Tables ---
        fig, ax = plt.subplots(figsize=A4_SIZE)
        ax.axis('off')

        # Draw logos
        if app.company_logo_path:
            company_logo_img = plt.imread(app.company_logo_path)
            ax_logo_left = fig.add_axes([0.08, 0.87, 0.15, 0.08])
            ax_logo_left.axis('off')
            ax_logo_left.imshow(company_logo_img)

        if app.accreditation_logo_path:
            accreditation_logo_img = plt.imread(app.accreditation_logo_path)
            ax_logo_right = fig.add_axes([0.77, 0.87, 0.15, 0.08])
            ax_logo_right.axis('off')
            ax_logo_right.imshow(accreditation_logo_img)

        # Metadata section
        draw_metadata_section(fig, app)

        plate_diameter = app.plate_diameter.currentText()
        measurement_device = app.measurement_device_selector.currentText()

        # Test Report Title and ID
        fig.text(0.15, 0.69, f"Test ID: {app.test_id.text()}", ha='center', fontsize=9)
        fig.text(0.5, 0.69, "Test report", ha='center', fontsize=14.5, fontweight='bold')
        fig.text(0.5, 0.66, f"Static Plate Strain Modulus (D = {plate_diameter} mm) ~ DIN 18134:2012-04", ha='center', fontsize=12.5)

        # Table 1: 6 rows, 2 columns
        table1_data = [
            ["Client:", app.client_name.text()],
            ["Project:", app.project_name.text()],
            ["The Contractor:", app.contractor_name.text()],
            ["Type of material:", app.material_type.text()],
            ["Request number:", app.request_number.text()],
            ["Weather/ Temperature:", app.weather_temp.text()],
            ["Measurement Device:", measurement_device]
        ]
        if measurement_device == "Lever-Arm System":
            table1_data.append(["Lever Ratio (hp/hm):", app.lever_ratio.text()])

        table1_ax = fig.add_axes([0.09, 0.44, 0.80, 0.12])
        table1_ax.axis('off')
        table1 = table1_ax.table(
            cellText=table1_data,
            colLabels=None,
            cellLoc='center',
            loc='center'
        )
        table1.auto_set_font_size(False)
        table1.set_fontsize(9)
        table1.scale(1, 1.5)

        # Set column widths (27% for labels, 73% for values)
        n_rows = len(table1_data)
        for row in range(n_rows):
            table1[(row, 0)].set_width(0.27)
            table1[(row, 1)].set_width(0.73)

        # Align column 0 left, column 1 center
        for row in range(len(table1_data)):
            table1[ (row,0) ].get_text().set_ha('left')
            table1[ (row,0) ].get_text().set_fontweight('normal')
            table1[ (row,1) ].get_text().set_ha('center')

        # Table 2: 3 rows, 2 columns
        table2_data = [
            ["Measurements Done By:", app.measured_by.text()],
            ["Supervisor:", app.supervisor.text()],
            ["Laboratory Technician:", app.laboratory.text()],
        ]

        table2_ax = fig.add_axes([0.09, 0.30, 0.80, 0.08])
        table2_ax.axis('off')
        table2 = table2_ax.table(
            cellText=table2_data,
            colLabels=None,
            cellLoc='center',
            loc='center'
        )
        table2.auto_set_font_size(False)
        table2.set_fontsize(9)
        table2.scale(1, 1.6)

        n_rows = len(table2_data)
        for row in range(n_rows):
            table2[(row, 0)].set_width(0.28)
            table2[(row, 1)].set_width(0.72)

        for row in range(len(table2_data)):
            table2[ (row,0) ].get_text().set_ha('left')
            table2[ (row,0) ].get_text().set_fontweight('normal')
            table2[ (row,1) ].get_text().set_ha('center')

        # Date and Designed By
        fig.text(0.08, 0.1, "Date:", ha='left', fontsize=8.5)
        fig.text(0.08, 0.08, f"{app.date.text()}", ha='left', fontsize=8.5)
        fig.text(0.68, 0.1255, "Designed and confirmed by:", ha='left', fontsize=8.5)
        fig.text(0.68, 0.101, "_____________________________", ha='left', fontsize=8.5)
        fig.text(0.68, 0.08, app.designed_by.text(), ha='left', fontsize=8.5)

        fig.text(0.08, 0.059, "Test report generated in compliance with DIN 18134:2012-04 | Software: DINmetric", ha='left', fontsize=6.8, alpha=0.45)

        pdf.savefig(fig)
        plt.close(fig)

        # --- PAGE 2: Summary Table Page ---
        fig, ax = plt.subplots(figsize=A4_SIZE)
        ax.axis('off')

        # Draw logos
        if app.company_logo_path:
            company_logo_img = plt.imread(app.company_logo_path)
            ax_logo_left = fig.add_axes([0.08, 0.87, 0.15, 0.08])
            ax_logo_left.axis('off')
            ax_logo_left.imshow(company_logo_img)

        if app.accreditation_logo_path:
            accreditation_logo_img = plt.imread(app.accreditation_logo_path)
            ax_logo_right = fig.add_axes([0.77, 0.87, 0.15, 0.08])
            ax_logo_right.axis('off')
            ax_logo_right.imshow(accreditation_logo_img)
        draw_metadata_section(fig, app)
        
        # Title
        fig.text(0.5, 0.7, "Summary of EV Results", ha='center', fontsize=14, fontweight='600')
        fig.text(0.15, 0.7, f"Test ID: {app.test_id.text()}", ha='center', fontsize=9)
        fig.text(0.5, 0.57, f"Static Plate Strain Modulus (D = {plate_diameter} mm) ~ DIN 18134:2012-04", ha='center', fontsize=12)
        
        # Prepare Table Data
        summary_headers = ["Test Point", "Station", "Side", "Type of Material", "Ev₁ (MN/m²)", "Ev₂ (MN/m²)", "Ev₂/Ev₁"]
        summary_data = []
        
        for idx, result in enumerate(app.summary_results, start=1):
            summary_data.append([
                str(idx),
                result['station'],
                result['side'],
                result['material'],
                f"{result['ev1']:.2f}",
                f"{result['ev2']:.2f}",
                f"{result['ev2_ev1_ratio']:.2f}" if result['ev2_ev1_ratio'] else "-"
            ])
        
        # Draw Table
        table_ax = fig.add_axes([0.05, 0.15, 0.9, 0.7])
        table_ax.axis('off')
        
        table = table_ax.table(
            cellText=summary_data,
            colLabels=summary_headers,
            cellLoc='center',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.4)

        # Note
        fig.text(0.08, 0.08, "*Note: The results apply to the measured points.", ha='left', fontsize=8, style='italic')

        # Date and Designed By
        fig.text(0.7, 0.13, "Measurments done by:", ha='left', fontsize=8.5)
        fig.text(0.7, 0.105, "_____________________________", ha='left', fontsize=8.5)
        fig.text(0.7, 0.085, app.measured_by.text(), ha='left', fontsize=8.5)

        # Footer
        fig.text(0.08, 0.059, "Test report generated in compliance with DIN 18134:2012-04 | Software: DINmetric", ha='left', fontsize=6.8, alpha=0.45)
        fig.text(0.5, 0.043, "Page 2", ha='center', fontsize=8)

        pdf.savefig(fig)
        plt.close(fig)

        ## --- Next Pages: Graph + Table ---
        for i in range(app.graphs_stack.count()):
            page_widget = app.graphs_stack.widget(i)
            layout = page_widget.layout()
            group_raw_points = getattr(page_widget, 'group_raw_points', [])
        
            canvas = layout.itemAt(0).widget()
            fig = canvas.figure
        
            new_fig = plt.figure(figsize=A4_SIZE)
            test_number = i + 1
            station = app.summary_results[test_number - 1]['station']
            side = app.summary_results[test_number - 1]['side']
            new_fig.text(0.5, 0.845, f"Test Point {test_number} | Station: {station} | Side: {side}", ha='center', fontsize=10)

            # Metadata table
            metadata_table_data = [
                ["Client:", app.client_name.text()],
                ["Project:", app.project_name.text()],
                ["The Contractor:", app.contractor_name.text()],
                ["Type of Material:", app.material_type.text()],
                ["Date:", app.date.text()],
                ["Weather/Temperature:", app.weather_temp.text()],
            ]
            
            meta_table_ax = new_fig.add_axes([0.08, 0.735, 0.84, 0.07])
            meta_table_ax.axis('off')
            meta_table = meta_table_ax.table(
                cellText=metadata_table_data,
                colLabels=None,
                cellLoc='center',
                loc='center'
            )
            meta_table.auto_set_font_size(False)
            meta_table.set_fontsize(8)
            meta_table.scale(1, 1.3)
            
            # Set left column to 27% and right column to 73%
            n_rows = len(metadata_table_data)
            for row in range(n_rows):
                meta_table[(row, 0)].set_width(0.27)
                meta_table[(row, 1)].set_width(0.73)
            
            # Align text: left for labels, center for values
            for row in range(n_rows):
                meta_table[(row, 0)].get_text().set_ha('left')
                meta_table[(row, 1)].get_text().set_ha('center')
        
            if app.company_logo_path:
                company_logo_img = plt.imread(app.company_logo_path)
                ax_logo_left = new_fig.add_axes([0.08, 0.87, 0.15, 0.08])
                ax_logo_left.axis('off')
                ax_logo_left.imshow(company_logo_img)
        
            new_fig.text(0.5, 0.87, f"Static Plate Strain Modulus (D = {plate_diameter} mm) ~ DIN 18134:2012-04", ha='center', fontsize=12)
        
            # Tables
            ev_table = layout.itemAt(1).layout().itemAt(1).widget()
        
            if not ev_table or ev_table.objectName() != "evResultsTable":
                continue
        
            # Extract EV Table data
            headers = [ev_table.horizontalHeaderItem(col).text().strip() for col in range(ev_table.columnCount())]
            table_data = []
            for row in range(ev_table.rowCount()):
                row_data = []
                for col in range(ev_table.columnCount()):
                    item = ev_table.item(row, col)
                    row_data.append(item.text().strip() if item else "")
                table_data.append(row_data)
        
            # Extract Load-Settlement Data
            raw_headers = ["Load\n(kN)", "Stress\n(MN/m²)", "Settlement\n(mm)"]
            grouped_data = {
                "First Loading": [],
                "Unloading": [],
                "Second Loading": []
            }
            for load, settlement, cycle in group_raw_points:
                if cycle in grouped_data:
                    grouped_data[cycle].append([f"{load:.2f}", f"{settlement:.2f}"])
        
            raw_data = []
            area = np.pi * (float(plate_diameter) / 1000) ** 2 / 4
            for key in ["First Loading", "Unloading", "Second Loading"]:
                for load_str, settl_str in grouped_data[key]:
                    try:
                        load = float(load_str)
                        settlement = float(settl_str)
                        stress = load / area / 1000  # Convert to MN/m²
                        raw_data.append([
                            f"{load:.2f}",
                            f"{stress:.3f}",
                            f"{settlement:.2f}"
                        ])
                    except ValueError:
                        raw_data.append([load_str, settl_str, ""])
                raw_data.extend([["", "", ""] for _ in range(2)])
            
            # Remove trailing empty rows
            while raw_data and raw_data[-1] == ["", "", ""]:
                raw_data.pop()
        
            # Layout parameters
            margin_left = 0.08
            margin_right = 0.08
            spacing = 0.06
            table_width = 0.24
            graph_left = margin_left + table_width + spacing
            graph_width = 1.0 - graph_left - margin_right
            graph_bottom = 0.27
            graph_height = 0.4
        
            # Load-Settlement-Stress Table (left)
            raw_table_ax = new_fig.add_axes([margin_left, 0.27, table_width, 0.4])
            raw_table_ax.axis('off')
            raw_table = raw_table_ax.table(
                cellText=raw_data,
                colLabels=raw_headers,
                loc='center',
                cellLoc='center',
                colLoc='center'
            )
            
            raw_table.auto_set_font_size(False)
            raw_table.set_fontsize(8)
            raw_table.scale(1, 1.1)
            
            # Only increase header height (row=0) manually
            for col in range(len(raw_headers)):
                raw_table[(0, col)].set_height(0.08)
        
            # Graph (right): Copy axes content from original figure
            orig_ax = fig.axes[0] if fig.axes else None
            if orig_ax:
                new_ax = new_fig.add_axes([graph_left, graph_bottom, graph_width, graph_height])
            
                # Copy lines
                for line in orig_ax.get_lines():
                    xdata = line.get_xdata()
                    ydata = line.get_ydata()
            
                    is_vertical = all(x == xdata[0] for x in xdata)
            
                    if is_vertical:
                        new_ax.axvline(
                            x=xdata[0],
                            color=line.get_color(),
                            linestyle=line.get_linestyle(),
                            linewidth=1
                        )
                    else:
                        new_ax.plot(
                            xdata,
                            ydata,
                            label=line.get_label(),
                            color=line.get_color(),
                            linestyle=line.get_linestyle(),
                            marker=line.get_marker(),
                            linewidth=1,
                            markersize=4
                        )
            
                # Copy axis labels, limits, title
                new_ax.set_title(orig_ax.get_title())
                new_ax.set_xlabel(orig_ax.get_xlabel())
                new_ax.set_ylabel(orig_ax.get_ylabel())
                new_ax.set_xlim(orig_ax.get_xlim())
                new_ax.set_ylim(orig_ax.get_ylim())
            
                # Copy legend
                if orig_ax.get_legend():
                    new_ax.legend()
            
                # Copy grid
                x_grid_on = any(line.get_visible() for line in orig_ax.get_xgridlines())
                y_grid_on = any(line.get_visible() for line in orig_ax.get_ygridlines())
                new_ax.grid(x_grid_on or y_grid_on)
            
                # Copy every text annotation exactly
                for text in orig_ax.texts:
                    new_ax.text(
                        *text.get_position(),
                        text.get_text(),
                        fontsize=text.get_fontsize(),
                        fontstyle=text.get_fontstyle(),
                        fontweight=text.get_fontweight(),
                        color=text.get_color(),
                        ha=text.get_ha(),
                        va=text.get_va(),
                        rotation=text.get_rotation()
                    )
            
            # EV Table (bottom full width)
            ev_table_ax = new_fig.add_axes([margin_left, 0.05, 1.0 - margin_left - margin_right, 0.25])
            ev_table_ax.axis('off')
            table = ev_table_ax.table(
                cellText=table_data,
                colLabels=headers,
                loc='center',
                cellLoc='center',
                colLoc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.2)
        
            new_fig.text(0.08, 0.115, f"Supervisor: {app.supervisor.text()}", ha='left', fontsize=8)
            new_fig.text(0.08, 0.1, f"The Contractor: {app.contractor_name.text()}", ha='left', fontsize=8)
            new_fig.text(0.08, 0.085, f"Laboratory Technician: {app.laboratory.text()}", ha='left', fontsize=8)

            # Footer
            new_fig.text(0.08, 0.059, "Test report generated in compliance with DIN 18134:2012-04 | Software: DINmetric", ha='left', fontsize=6.8, alpha=0.45)
            new_fig.text(0.5, 0.043, f"Page {i+3}", ha='center', fontsize=8)
        
            # Save page
            pdf.savefig(new_fig)
            plt.close(new_fig)

def draw_metadata_section(fig, app):
    ax_meta = fig.add_axes([0, 0, 1, 1])
    ax_meta.axis('off')

    # Common params
    table_x = 0.08
    col1_w = 0.57
    col2_w = 0.08
    col3_w = 0.17
    row_h = 0.02
    spacing = 0

    y = 0.83

    def draw_cell(x, y, w, h, text, fontsize=8.5, weight='normal', ha='left', centered=False):
        ax_meta.add_patch(patches.Rectangle((x, y), w, h, fill=False, edgecolor='black', linewidth=0.7))
        text_x = x + w/2 if centered else x + 0.005
        text_ha = 'center' if centered else ha
        fig.text(text_x, y + h / 2, text, fontsize=fontsize, weight=weight, va='center', ha=text_ha)

    # Company Name
    draw_cell(table_x, y - row_h, col1_w, row_h * 2, app.company_name.text(), fontsize=11.5, weight='500', centered=True)
    draw_cell(table_x + col1_w, y, col2_w, row_h, "Code")
    draw_cell(table_x + col1_w + col2_w, y, col3_w, row_h, app.code.text())

    y -= (row_h + spacing)
    # Version
    draw_cell(table_x + col1_w, y, col2_w, row_h, "Version")
    draw_cell(table_x + col1_w + col2_w, y, col3_w, row_h, app.version.text())

    y -= (row_h + spacing)
    # Slogan
    draw_cell(table_x, y, col1_w, row_h, app.company_slogan.text(), fontsize=8, centered=True)
    draw_cell(table_x + col1_w, y, col2_w, row_h, "Date")
    draw_cell(table_x + col1_w + col2_w, y, col3_w, row_h, app.date.text())

    y -= (row_h + spacing)
    # Other Info
    draw_cell(table_x, y, col1_w + col2_w + col3_w, row_h, app.other_info.text(), fontsize=7.5)

    return
