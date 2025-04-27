from matplotlib.backends.backend_pdf import PdfPages
from PyQt5.QtWidgets import QFileDialog
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def export_to_pdf(app):
    if app.graphs_stack.count() == 0:
        return 

    # Ask user where to save
    file_path, _ = QFileDialog.getSaveFileName(app, "Save PDF", "", "PDF Files (*.pdf)")
    if not file_path:
        return

    if not file_path.endswith('.pdf'):
        file_path += '.pdf'

    with PdfPages(file_path) as pdf:
        ## --- PAGE 1: Metadata (Sidebar Info) ---
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')

        text_lines = []
        fields = [
            ("Test ID", app.test_id.text()),
            ("Company Name", app.company_name.text()),
            ("Slogan", app.company_slogan.text()),
            ("Code", app.code.text()),
            ("Version", app.version.text()),
            ("Date", app.date.text()),
            ("Other Info", app.other_info.text()),
            ("Client Name", app.client_name.text()),
            ("Project Name", app.project_name.text()),
            ("Contractor's Name", app.contractor_name.text()),
            ("Request Number", app.request_number.text()),
            ("Weather / Temperature", app.weather_temp.text()),
            ("Designed & Confirmed By", app.designed_by.text()),
            ("Measurements Done By", app.measured_by.text()),
            ("Supervisor", app.supervisor.text()),
            ("Laboratory", app.laboratory.text()),
            ("Type of Measurement", app.measurement_type.text())
        ]

        for label, value in fields:
            text_lines.append(f"{label}: {value}")

        full_text = "\n".join(text_lines)

        # Center the text
        ax.text(0.5, 0.5, full_text, transform=ax.transAxes,
                fontsize=10, ha='center', va='center', wrap=True)

        # Footer: Page Number
        fig.text(0.5, 0.04, f"Page 1", ha='center', fontsize=8)

        pdf.savefig(fig)
        plt.close(fig)

        ## --- Next Pages: Graph + Table ---
        for i in range(app.graphs_stack.count()):
            page_widget = app.graphs_stack.widget(i)
            layout = page_widget.layout()
            group_raw_points = getattr(page_widget, 'group_raw_points', [])

            # Get the Canvas (figure)
            canvas = layout.itemAt(0).widget()
            fig = canvas.figure
            
            # Create a new blank figure
            new_fig = plt.figure(figsize=(8.27, 11.69))  # A4 size
            gs = new_fig.add_gridspec(2, 1, height_ratios=[2, 1])
            
            # First subplot: Graph
            ax_graph = new_fig.add_subplot(gs[0])
            ax_graph.axis('off')
            
            # Save original figure to buffer
            import io
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300)
            buf.seek(0)
            
            # Load it back with imread
            img = plt.imread(buf)
            ax_graph.imshow(img)
            ax_graph.set_aspect('auto')

            # --- Below: Table ---
            table_ax = new_fig.add_subplot(gs[1])
            table_ax.axis('off')

            # --- Add Table Below ---
            ev_table = layout.itemAt(1).layout().itemAt(1).widget()
            
            # --- Extract Load-Settlement-Cycle Data ---
            # Search the parent layout to find the original table of data points
            raw_data_table = layout.itemAt(1).layout().itemAt(1).widget()
            
            # fallback if structure changes
            if raw_data_table.objectName() != "evResultsTable":
                raw_data_table = None
            
            # Create a list for the raw data
            raw_data = []
            raw_headers = ["Load (kN)", "Settlement (mm)", "Cycle Type"]
            
            # --- Ev Results Table ---
            table_data = []
            headers = []
            for col in range(ev_table.columnCount()):
                header_item = ev_table.horizontalHeaderItem(col)
                if header_item:
                    headers.append(header_item.text().strip())
            
            for row in range(ev_table.rowCount()):
                row_data = []
                for col in range(ev_table.columnCount()):
                    item = ev_table.item(row, col)
                    if item:
                        row_data.append(item.text().strip())
                    else:
                        row_data.append("")
                table_data.append(row_data)
            
            # --- Create Load-Settlement Table ---
            raw_data = []
            raw_headers = ["Load (kN)", "Settlement (mm)", "Cycle Type"]
            
            for load, settlement, cycle in group_raw_points:
                raw_data.append([f"{load:.2f}", f"{settlement:.2f}", cycle])
            
            raw_table_ax = new_fig.add_axes([0.1, 0.7, 0.8, 0.2])
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
            raw_table.scale(1, 1.2)
            
            # --- Create Ev Table ---
            table_ax = new_fig.add_axes([0.1, 0.05, 0.8, 0.3])
            table_ax.axis('off')
            
            table = table_ax.table(
                cellText=table_data,
                colLabels=headers,
                loc='center',
                cellLoc='center',
                colLoc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.2)

            # Insert page number
            new_fig.text(0.5, 0.02, f"Page {i+2}", ha='center', fontsize=8)

            pdf.savefig(new_fig)
            plt.close(new_fig)