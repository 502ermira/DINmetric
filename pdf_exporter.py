from PyQt5.QtWidgets import QFileDialog
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from functools import partial
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import tempfile
from datetime import datetime
import os
import numpy as np
from PIL import Image as PILImage

def export_to_pdf(app):
    if app.graphs_stack.count() == 0:
        return

    file_path, _ = QFileDialog.getSaveFileName(app, "Save PDF", "", "PDF Files (*.pdf)")
    if not file_path:
        return
    if not file_path.endswith('.pdf'):
        file_path += '.pdf'

    # Create PDF document
    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    elements = []

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontSize = 9
    normal.leading = 11

    bold = ParagraphStyle(name='Bold', parent=normal, fontName='Helvetica-Bold')

    def p(text, style=normal):
        return Paragraph(text, style)

    # Top logos (Company and Accreditation)
    logo_row = []
    if app.company_logo_path and os.path.exists(app.company_logo_path):
        logo_row.append(Image(app.company_logo_path, width=3*cm, height=2*cm))
    else:
        logo_row.append(Spacer(3*cm, 2*cm))

    logo_row.append(Spacer(10*cm, 2*cm))

    if app.accreditation_logo_path and os.path.exists(app.accreditation_logo_path):
        logo_row.append(Image(app.accreditation_logo_path, width=3*cm, height=2*cm))
    else:
        logo_row.append(Spacer(3*cm, 2*cm))

    elements.append(Table([logo_row], colWidths=[3*cm, None, 3*cm]))
    elements.append(Spacer(1, 12))
    
    # --- Metadata Section ---
    metadata_data = [
        [Paragraph(f"<b>{app.company_name.text()}</b>", ParagraphStyle('meta-title', fontSize=12, alignment=1)), 'Code:', app.code.text()],
        ['', 'Version:', app.version.text()],
        [Paragraph(app.company_slogan.text(), ParagraphStyle('slogan', fontSize=9, alignment=1)), 'Date:', app.date.text()],
        [app.other_info.text(), '', '']
    ]
    
    metadata_table = Table(metadata_data, colWidths=[13*cm, 1.5*cm, 2.5*cm])
    
    metadata_table.setStyle(TableStyle([
        # Correct spans
        ('SPAN', (0,0), (0,1)),
        ('SPAN', (0,3), (2,3)), 
    
        # Grid and alignment
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,1), 'CENTER'),
        ('ALIGN', (0,2), (0,2), 'CENTER'),
        ('ALIGN', (1,0), (2,2), 'LEFT'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ]))
    
    elements.append(metadata_table)
    elements.append(Spacer(1, 20))

    # --- Title Section ---
    plate_diameter = app.plate_diameter.currentText()
    measurement_device = app.measurement_device_selector.currentText()
    
    # Test ID and Test Report in one row
    test_header_data = [
        [
            Paragraph(f"<b>Test ID:</b> {app.test_id.text()}", ParagraphStyle('test-id', fontSize=9, alignment=0)),
            Paragraph("<b>Test Report</b>", ParagraphStyle('title', fontSize=14.5, alignment=1)),
            Paragraph("<b> </b>", ParagraphStyle('space', fontSize=14.5, alignment=1)),
        ]
    ]
    
    # Calculate the widths for the columns
    test_header_table = Table(test_header_data, colWidths=[4.5*cm, 8*cm, 4.5*cm])
    
    # Apply styles to the table
    test_header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6), 
    ]))

    elements.append(test_header_table)
    elements.append(Spacer(1, 10))
    elements.append(p(f"Static Plate Strain Modulus (D = {plate_diameter} mm) ~ DIN 18134:2012-04", ParagraphStyle('subtitle', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 24))

    ## --- Table 1 ---
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

    table1 = Table(table1_data, colWidths=[4*cm, 13*cm])
    table1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(table1)
    elements.append(Spacer(1, 28))

    ## --- Table 2 ---
    table2_data = [
        ["Measurements Done By:", app.measured_by.text()],
        ["Supervisor:", app.supervisor.text()],
        ["Laboratory Technician:", app.laboratory.text()],
    ]

    table2 = Table(table2_data, colWidths=[4*cm, 13*cm])
    table2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(table2)
    elements.append(Spacer(1, 20))

    elements.append(PageBreak())
    add_summary_page(app, elements, styles)

    # Pages 3+
    add_graph_pages(app, elements, styles) 

    def draw_footer_dynamic(canvas_obj, doc_obj):
        page_num = doc_obj.page
        footer_y = 2.2 * cm
        line_spacing = 0.4 * cm
        canvas_obj.saveState()
    
        canvas_obj.setFont("Helvetica", 10)
    
        if page_num == 1:
            date_x = doc_obj.leftMargin
            canvas_obj.drawString(date_x, footer_y + line_spacing * 2, "Date:")
            canvas_obj.drawString(date_x, footer_y, app.date.text())
    
            designer_x = doc_obj.pagesize[0] - doc_obj.rightMargin
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing*3, "Designed and confirmed by:")
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing, "_______________________")
            canvas_obj.drawRightString(designer_x, footer_y, app.designed_by.text())
        
        elif page_num == 2:
            date_x = doc_obj.leftMargin
        
            canvas_obj.setFont("Helvetica-Oblique", 8)
            canvas_obj.drawString(date_x, footer_y + line_spacing * 2, "*Note: The results apply to the measured points.")
        
            designer_x = doc_obj.pagesize[0] - doc_obj.rightMargin
        
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing * 3, "Measurements done by:")
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing, "_______________________")
            canvas_obj.drawRightString(designer_x, footer_y, app.measured_by.text())

        elif page_num >= 3:
            date_x = doc_obj.leftMargin
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.drawString(date_x, footer_y + line_spacing * 2, f"Supervisor: {app.supervisor.text()}")
            canvas_obj.drawString(date_x, footer_y + line_spacing, f"The Contractor: {app.contractor_name.text()}")
            canvas_obj.drawString(date_x, footer_y, f"Laboratory Technician: {app.laboratory.text()}")
            
        # Common centered footer note
        canvas_obj.setFont("Helvetica-Oblique", 7)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawCentredString(doc_obj.pagesize[0] / 2.0, (1.85 * cm) - line_spacing, "Test report generated in compliance with DIN 18134:2012-04 | Software: DINmetric")
        if page_num > 1:
            canvas_obj.setFont("Helvetica", 7.5)
            canvas_obj.setFillColor(colors.black)
            canvas_obj.drawCentredString(
                doc_obj.pagesize[0] / 2.0,
                1 * cm, 
                f"Page {page_num}"
        )

    
        canvas_obj.restoreState()
    
    doc.build(
        elements,
        onFirstPage=draw_footer_dynamic,
        onLaterPages=draw_footer_dynamic
    )

def add_summary_page(app, elements, styles):

    def p(text, style=styles['Normal']):
        return Paragraph(text, style)

    logo_row = []
    
    # Add company logo if the path exists
    if app.company_logo_path and os.path.exists(app.company_logo_path):
        logo_row.append(Image(app.company_logo_path, width=3*cm, height=2*cm))
    else:
        logo_row.append(Spacer(3*cm, 2*cm))
    
    logo_row.append(Spacer(15*cm, 2*cm))
    
    # Create a table with the logo and spacer
    elements.append(Table([logo_row], colWidths=[3*cm, 15*cm]))
    elements.append(Spacer(1, 12))
    
    # --- Metadata Section ---
    metadata_data = [
        [Paragraph(f"<b>{app.company_name.text()}</b>", ParagraphStyle('meta-title', fontSize=12, alignment=1)), 'Code:', app.code.text()],
        ['', 'Version:', app.version.text()],
        [Paragraph(app.company_slogan.text(), ParagraphStyle('slogan', fontSize=9, alignment=1)), 'Date:', app.date.text()],
        [app.other_info.text(), '', '']
    ]
    
    metadata_table = Table(metadata_data, colWidths=[13*cm, 1.5*cm, 2.5*cm])
    
    metadata_table.setStyle(TableStyle([
        ('SPAN', (0,0), (0,1)),
        ('SPAN', (0,3), (2,3)), 
    
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,1), 'CENTER'),
        ('ALIGN', (0,2), (0,2), 'CENTER'),
        ('ALIGN', (1,0), (2,2), 'LEFT'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ]))
    
    elements.append(metadata_table)
    elements.append(Spacer(1, 20))

    # Title
    plate_diameter = app.plate_diameter.currentText()
    
    # Test ID and Test Report in one row
    test_header_data = [
        [
            Paragraph(f"<b>Test ID:</b> {app.test_id.text()}", ParagraphStyle('test-id', fontSize=9, alignment=0)),
            Paragraph("<b>Summary of EV Results</b>", ParagraphStyle('title', fontSize=14.5, alignment=1)),
            Paragraph("<b> </b>", ParagraphStyle('space', fontSize=14.5, alignment=1)),
        ]
    ]
    
    # Calculate the widths for the columns
    test_header_table = Table(test_header_data, colWidths=[4.5*cm, 8*cm, 4.5*cm])
    
    # Apply styles to the table
    test_header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6), 
    ]))

    elements.append(test_header_table)
    elements.append(Spacer(1, 10))
    elements.append(p(f"Static Plate Strain Modulus (D = {plate_diameter} mm) ~ DIN 18134:2012-04", ParagraphStyle('subtitle', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 24))

    # Check data
    if not app.summary_results:
        print("Summary results are empty")
        return

    for result in app.summary_results:
        required_keys = ['station', 'side', 'material', 'ev1', 'ev2', 'ev2_ev1_ratio']
        if not all(k in result for k in required_keys):
            print(f"Incomplete summary result: {result}")
            return

    summary_headers = [
        Paragraph("Test Point", styles['Normal']),
        Paragraph("Station", styles['Normal']),
        Paragraph("Side", styles['Normal']),
        Paragraph("Type of Material", styles['Normal']),
        Paragraph("Ev<sub>1</sub> (MN/m²)", styles['Normal']),
        Paragraph("Ev<sub>2</sub> (MN/m²)", styles['Normal']),
        Paragraph("Ev<sub>2</sub>/Ev<sub>1</sub>", styles['Normal']),
    ]

    summary_data = []
    total_width = 17 * cm  

    # Proportional weights (these should sum up to 1)
    weights = [0.13, 0.16, 0.16, 0.16, 0.13, 0.13, 0.13]
    
    colWidths = [w * total_width for w in weights]

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

    table = Table([summary_headers] + summary_data, repeatRows=1, hAlign='CENTER', colWidths=colWidths)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ]))

    elements.append(table)
    elements.append(PageBreak())


def add_graph_pages(app, elements, styles):
    
    plate_diameter = app.plate_diameter.currentText()

    elements.append(Spacer(1, 0.1 * inch))

    for i in range(app.graphs_stack.count()): 
        def p(text, style=styles['Normal']):
            return Paragraph(text, style)
    
        logo_row = []
        
        if app.company_logo_path and os.path.exists(app.company_logo_path):
            logo_row.append(Image(app.company_logo_path, width=3*cm, height=2*cm))
        else:
            logo_row.append(Spacer(3*cm, 2*cm))
        
        logo_row.append(Spacer(15*cm, 2*cm))
        
        # Create a table with the logo and spacer
        elements.append(Table([logo_row], colWidths=[3*cm, 15*cm]))
        elements.append(Spacer(1, 12))
    
        page_widget = app.graphs_stack.widget(i)
        layout = page_widget.layout()
        group_raw_points = getattr(page_widget, 'group_raw_points', [])
    
        if not group_raw_points or not isinstance(group_raw_points, list):
            continue
    
        test_number = i + 1
        if i >= len(app.summary_results):
            continue
    
        station = app.summary_results[test_number - 1]['station']
        side = app.summary_results[test_number - 1]['side']
    
        # Centered title
        elements.append(Paragraph(
            f"Static Plate Strain Modulus (D = {plate_diameter} mm) ~ DIN 18134:2012-04", 
            ParagraphStyle('title', fontSize=13.5, alignment=1)
        ))
        
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            f"Test Point {test_number} | Station: {station} | Side: {side}", 
            ParagraphStyle('centered_info', parent=styles['Normal'], alignment=1, fontSize=11)
        ))
    
        elements.append(Spacer(1, 20))
    
        # Metadata Table
        metadata_table_data = [
            ["Client:", app.client_name.text()],
            ["Project:", app.project_name.text()],
            ["The Contractor:", app.contractor_name.text()],
            ["Type of Material:", app.material_type.text()],
            ["Date:", app.date.text()],
            ["Weather/Temperature:", app.weather_temp.text()],
        ]
        table = Table(metadata_table_data, colWidths=[3.5*cm, 13.5*cm])
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
    
        # Load-settlement-stress table creation
        area = np.pi * (float(plate_diameter) / 1000) ** 2 / 4
        raw_data = []
    
        grouped_data = {
            "First Loading": [],
            "Unloading": [],
            "Second Loading": []
        }
    
        for load, settlement, cycle in group_raw_points:
            if cycle in grouped_data:
                grouped_data[cycle].append((load, settlement))
    
        for key in ["First Loading", "Unloading", "Second Loading"]:
            for load, settlement in grouped_data[key]:
                stress = load / area / 1000
                raw_data.append([
                    f"{load:.2f}",
                    f"{stress:.3f}",
                    f"{settlement:.2f}"
                ])
            if key != "Second Loading":
                raw_data.append(["", "", ""]) 
                raw_data.append(["", "", ""])
    
        header_style = ParagraphStyle(
            'header_style',
            fontSize=8,
            alignment=1,
            spaceAfter=0,
            spaceBefore=0,
            leading=9
        )
    
        # Header with name and unit split
        raw_headers = [
            Paragraph("Load<br/><font size=7>(kN)</font>", header_style),
            Paragraph("Stress<br/><font size=7>(MN/m²)</font>", header_style),
            Paragraph("Settlement<br/><font size=7>(mm)</font>", header_style)
        ]
    
        # Create the table with tighter columns
        stress_table = Table([raw_headers] + raw_data, colWidths=[1.8*cm, 1.8*cm, 1.8*cm])
        stress_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
    
        # Plot to image
        canvas = layout.itemAt(0).widget()
        fig = canvas.figure
    
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            FigureCanvas(fig).print_png(tmpfile.name)
    
            # Load image size
            img_reader = PILImage.open(tmpfile.name)
            image_width_px, image_height_px = img_reader.size
            dpi = fig.get_dpi()
    
            # Convert to cm
            image_width_cm = image_width_px / dpi * 2.54
            image_height_cm = image_height_px / dpi * 2.54
            aspect_ratio = image_height_cm / image_width_cm
    
            plot_image = Image(tmpfile.name, width=image_width_cm * cm, height=image_height_cm * cm)
    
            # Estimate row height and table height
            table_height_lines = len(stress_table._cellvalues)
            row_height_cm = 0.5
            table_height_cm = table_height_lines * row_height_cm
            vertical_padding_cm = max((image_height_cm - table_height_cm) / 2, 0)
    
            # Wrap the table with padding
            stress_table_flowable = [
                Spacer(1, vertical_padding_cm * cm),
                stress_table,
                Spacer(1, vertical_padding_cm * cm)
            ]
    
            table_column = []
            table_column.extend(stress_table_flowable)
    
            # Assemble final layout
            combined_table = Table(
                [[table_column, plot_image]],
                colWidths=[(image_width_cm * 0.35) * cm, image_width_cm * cm],
                hAlign='CENTER'
            )
            combined_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
    
        elements.append(combined_table)
        elements.append(Spacer(1, 12))

        # EV Table
        ev_table_widget = layout.itemAt(1).layout().itemAt(1).widget()
        if ev_table_widget.objectName() == "evResultsTable":
            headers = [ev_table_widget.horizontalHeaderItem(col).text() for col in range(ev_table_widget.columnCount())]
            ev_data = []
            for row in range(ev_table_widget.rowCount()):
                row_data = []
                for col in range(ev_table_widget.columnCount()):
                    item = ev_table_widget.item(row, col)
                    row_data.append(item.text() if item else "")
                ev_data.append(row_data)

            ev_table = Table([headers] + ev_data, colWidths=[None]*len(headers))
            ev_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            elements.append(ev_table)
            if i < app.graphs_stack.count() - 1:
                elements.append(PageBreak())

    elements.append(Spacer(1, 0.1 * inch))