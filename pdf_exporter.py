import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QTextDocument

def export_to_pdf(app):
    try:
        filename = f"PlateLoadTest_{app.test_id.text() or 'Untitled'}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 30, "LOAD TEST PLATE - DIN 18134")

        # Metadata
        c.setFont("Helvetica", 10)
        y = height - 50
        spacing = 14
        meta_fields = [
            ("Test ID:", app.test_id.text()),
            ("Plate Diameter:", app.plate_diameter.currentText() + " mm"),
            ("Lever Ratio:", app.lever_ratio.text()),
        ]
        for label, val in meta_fields:
            c.drawString(40, y, f"{label} {val}")
            y -= spacing

        # Plot
        temp_plot_path = os.path.join(tempfile.gettempdir(), "plot.png")
        app.figure.savefig(temp_plot_path, bbox_inches="tight")

        c.drawImage(temp_plot_path, 40, y - 280, width=520, height=250)
        y -= 300

        # Results
        from PyQt5.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(app.result_label.text())
        result_text = doc.toPlainText()

        for line in result_text.split("\n"):
            if y < 100:
                c.showPage()
                y = height - 40
            c.drawString(40, y, line.strip())
            y -= spacing

        c.save()

        QMessageBox.information(app, "Export Complete", f"PDF exported to:\n{filepath}")
        os.startfile(filepath)  # Opens the file on Windows (optional)
    except Exception as e:
        QMessageBox.critical(app, "Export Error", str(e))
    
