from matplotlib.backends.backend_pdf import PdfPages
from PyQt5.QtWidgets import QFileDialog
import matplotlib.pyplot as plt
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
        ## --- PAGE 1: Metadata (Sidebar Info) ---
        fig, ax = plt.subplots(figsize=A4_SIZE)
        ax.axis('off')

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
            ("Type of Material", app.material_type.text())
        ]

        text_lines = [f"{label}: {value}" for label, value in fields]
        full_text = "\n".join(text_lines)

        ax.text(0.5, 0.5, full_text, transform=ax.transAxes,
                fontsize=10, ha='center', va='center', wrap=True)
        fig.text(0.5, 0.04, "Page 1", ha='center', fontsize=8)

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
            gs = new_fig.add_gridspec(2, 1, height_ratios=[2, 1])

            # Graph
            ax_graph = new_fig.add_subplot(gs[0])
            ax_graph.axis('off')

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300)
            buf.seek(0)
            img = plt.imread(buf)
            ax_graph.imshow(img)
            ax_graph.set_aspect('auto')

            # Tables
            ev_table = layout.itemAt(1).layout().itemAt(1).widget()

            # Safety: check objectName
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
            raw_headers = ["Load (kN)", "Settlement (mm)", "Cycle Type"]
            raw_data = [[f"{load:.2f}", f"{settlement:.2f}", cycle] for load, settlement, cycle in group_raw_points]

            # Plot Raw Data Table
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

            # Plot EV Table
            ev_table_ax = new_fig.add_axes([0.1, 0.05, 0.8, 0.3])
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

            # Footer
            new_fig.text(0.5, 0.02, f"Page {i+2}", ha='center', fontsize=8)

            pdf.savefig(new_fig)
            plt.close(new_fig)
