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
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
import tempfile
from datetime import datetime
import os
import numpy as np
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.rl_config import defaultEncoding
from constants import CYCLE_TYPE_IDS
from utils import resource_path

font_path = resource_path("fonts/DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

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
    
    total_width = 17 * cm
    desired_height = 2 * cm
    
    # Load logos
    company_logo = None
    accreditation_logo = None
    
    if app.company_logo_path and os.path.exists(app.company_logo_path):
        company_reader = ImageReader(app.company_logo_path)
        w, h = company_reader.getSize()
        scale = desired_height / h
        company_logo = Image(app.company_logo_path, width=w * scale, height=desired_height)
    else:
        company_logo = Spacer(4*cm, desired_height)
    
    if app.accreditation_logo_path and os.path.exists(app.accreditation_logo_path):
        accred_reader = ImageReader(app.accreditation_logo_path)
        w, h = accred_reader.getSize()
        scale = desired_height / h
        accreditation_logo = Image(app.accreditation_logo_path, width=w * scale, height=desired_height)
    else:
        accreditation_logo = Spacer(4*cm, desired_height)
    
    # Create logo row using a 3-column table layout with calculated spacers
    logo_table = Table(
        [[company_logo, Spacer(1, desired_height), accreditation_logo]],
        colWidths=[total_width * 0.2, total_width * 0.6, total_width * 0.2]
    )
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
    ]))
    
    elements.append(logo_table)
    elements.append(Spacer(1, 12))
    
    # --- Metadata Section ---
    metadata_data = [
        [Paragraph(f"<b>{app.company_name.text()}</b>", ParagraphStyle('meta-title', fontSize=12, alignment=1)), app.tr("code"), app.code.text()],
        ['', app.tr("version"), app.version.text()],
        [Paragraph(app.company_slogan.text(), ParagraphStyle('slogan', fontSize=9.5, alignment=1)), app.tr("date"), app.date.text()],
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
            Paragraph(f"<b>{app.tr('test_report')}</b>", ParagraphStyle('title', fontSize=15, alignment=1)),
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
    elements.append(Spacer(1, 12))
    elements.append(p(f"{app.tr('static_plate_modulus')} (D = {plate_diameter} mm) ~ DIN 18134:2012-04", 
                 ParagraphStyle('subtitle', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 28))

    ## --- Table 1 ---
    table1_data = [
        [app.tr("client_name"), app.client_name.text()],
        [app.tr("project_name"), app.project_name.text()],
        [app.tr("contractor_name"), app.contractor_name.text()],
        [app.tr("material_type"), app.material_type.text()],
        [app.tr("request_number"), app.request_number.text()],
        [app.tr("weather_temp"), app.weather_temp.text()],
        [app.tr("measurement_device"), measurement_device]
    ]

    if measurement_device == "Lever-Arm System":
        table1_data.append([app.tr("lever_ratio"), app.lever_ratio.text()])

    table1 = Table(table1_data, colWidths=[4*cm, 13*cm])
    table1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(table1)
    elements.append(Spacer(1, 30))

    ## --- Table 2 ---
    table2_data = [
        [app.tr("measured_by"), app.measured_by.text()],
        [app.tr("supervisor"), app.supervisor.text()],
        [app.tr("laboratory"), app.laboratory.text()],
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

    # --- Calculation Method Section ---
    calc_method = app.method_selector.currentText()
    
    if "din" in calc_method.lower():
        calc_text = app.tr("curve_method_description")
    else:
        calc_text = app.tr("secant_method_description")
    
    # Title
    elements.append(Table([[Paragraph(f"<b>{app.tr('calculation_method')}</b>", bold)]], colWidths=[17*cm]))
    elements.append(Spacer(1, 4))
    
    calc_table = Table(
        [[Paragraph(calc_text, normal)]],
        colWidths=[17*cm]
    )
    calc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(calc_table)

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
            canvas_obj.drawString(date_x, footer_y + line_spacing * 2, app.tr("date"))
            canvas_obj.drawString(date_x, footer_y, app.date.text())
    
            designer_x = doc_obj.pagesize[0] - doc_obj.rightMargin
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing*3, app.tr("designed_by"))
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing, "_______________________")
            canvas_obj.drawRightString(designer_x, footer_y, app.designed_by.text())
        
        elif page_num == 2:
            date_x = doc_obj.leftMargin
        
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.drawString(date_x, footer_y + line_spacing * 2, app.tr("note"))
        
            designer_x = doc_obj.pagesize[0] - doc_obj.rightMargin
        
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing * 3, app.tr("measured_by"))
            canvas_obj.drawRightString(designer_x, footer_y + line_spacing, "______________________")
            canvas_obj.drawRightString(designer_x, footer_y, app.measured_by.text())

        elif page_num >= 3:
            date_x = doc_obj.leftMargin
            canvas_obj.setFont("DejaVuSans", 8)
            canvas_obj.drawString(date_x, footer_y + line_spacing * 2, f"{app.tr('supervisor')} {app.supervisor.text()}")
            canvas_obj.drawString(date_x, footer_y + line_spacing, f"{app.tr('contractor_name')} {app.contractor_name.text()}")
            canvas_obj.drawString(date_x, footer_y,f"{app.tr('laboratory')} {app.laboratory.text()}")
            
        # Common centered footer note
        canvas_obj.setFont("Helvetica-Oblique", 7)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawCentredString(doc_obj.pagesize[0] / 2.0, (1.86 * cm) - line_spacing, app.tr('footer_compliance'))
        if page_num > 1:
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(colors.black)
            canvas_obj.drawCentredString(
                doc_obj.pagesize[0] / 2.0,
                1 * cm, 
                f"{page_num}"
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
        image_reader = ImageReader(app.company_logo_path)
        original_width, original_height = image_reader.getSize()
        
        desired_height = 2 * cm
        scale_factor = desired_height / float(original_height)
        adjusted_width = original_width * scale_factor
        
        logo = Image(app.company_logo_path, width=adjusted_width, height=desired_height)
        logo_row.append(logo)
    else:
        logo_row.append(Spacer(3*cm, 2*cm))
    
    logo_row.append(Spacer(15*cm, 2*cm))
    
    # Create a table with the logo and spacer
    elements.append(Table([logo_row], colWidths=[3*cm, 15*cm]))
    elements.append(Spacer(1, 12))
    
    # --- Metadata Section ---
    metadata_data = [
        [Paragraph(f"<b>{app.company_name.text()}</b>", ParagraphStyle('meta-title', fontSize=12, alignment=1)), app.tr('code'), app.code.text()],
        ['', app.tr('version'), app.version.text()],
        [Paragraph(app.company_slogan.text(), ParagraphStyle('slogan', fontSize=9, alignment=1)), app.tr('date'), app.date.text()],
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
            Paragraph(f"<b>{app.tr('summary_results')}</b>", ParagraphStyle('title', fontSize=14.5, alignment=1)),
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
    elements.append(p(f"{app.tr('static_plate_modulus')} (D = {plate_diameter} mm) ~ DIN 18134:2012-04", 
                ParagraphStyle('subtitle', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 24))

    # Check data
    if not app.summary_results:
        return

    for result in app.summary_results:
        required_keys = ['station', 'side', 'material', 'ev1', 'ev2', 'ev2_ev1_ratio']
        if not all(k in result for k in required_keys):
            return

    header_style = ParagraphStyle(
        name='header-style',
        parent=styles['Normal'],
        alignment=1
    )
    
    summary_headers = [
        Paragraph(app.tr('test_point'), header_style),
        Paragraph(app.tr('station'), header_style),
        Paragraph(app.tr('side'), header_style),
        Paragraph(app.tr('material_type'), header_style),
        Paragraph("Ev<sub>1</sub> (MN/m²)", header_style),
        Paragraph("Ev<sub>2</sub> (MN/m²)", header_style),
        Paragraph("Ev<sub>2</sub>/Ev<sub>1</sub>", header_style),
    ]

    summary_data = []
    total_width = 17 * cm  

    # Proportional weights (these should sum up to 1)
    weights = [0.14, 0.16, 0.15, 0.16, 0.13, 0.13, 0.13]
    
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

    # Split summary_data into chunks of 24 rows
    chunk_size = 24
    total_pages = (len(summary_data) + chunk_size - 1) // chunk_size
    
    for page_num, i in enumerate(range(0, len(summary_data), chunk_size)):
        chunk = summary_data[i:i + chunk_size]
        
        # Add continuation header for pages after the first
        if page_num > 0:
            elements.append(Paragraph(
                f"<b>{app.tr('summary_results')} ({app.tr('continued')} {page_num + 1}/{total_pages})</b>",
                ParagraphStyle('continuation-title', fontSize=14.5, alignment=1)
            ))
            elements.append(Spacer(1, 24))
        
        # Create the table
        table = Table([summary_headers] + chunk, 
                     repeatRows=1, 
                     hAlign='CENTER', 
                     colWidths=colWidths)
        
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ]))
        
        elements.append(table)
        elements.append(PageBreak())
        
        if not chunk:
            elements.pop()


def add_graph_pages(app, elements, styles):
    
    plate_diameter = app.plate_diameter.currentText()

    elements.append(Spacer(1, 0.1 * inch))
 
    for i in range(app.graphs_stack.count()): 
        def p(text, style=styles['Normal']):
            return Paragraph(text, style)
    
        logo_row = []
        
        if app.company_logo_path and os.path.exists(app.company_logo_path):
            image_reader = ImageReader(app.company_logo_path)
            original_width, original_height = image_reader.getSize()
            
            desired_height = 2 * cm
            scale_factor = desired_height / float(original_height)
            adjusted_width = original_width * scale_factor
            
            logo = Image(app.company_logo_path, width=adjusted_width, height=desired_height)
            logo_row.append(logo)
        else:
            logo_row.append(Spacer(3*cm, 2*cm))
        
        logo_row.append(Spacer(15*cm, 2*cm))
        
        # Create a table with the logo and spacer
        elements.append(Table([logo_row], colWidths=[3*cm, 15*cm]))
        elements.append(Spacer(1, 10))
    
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
        elements.append(p(f"{app.tr('static_plate_modulus')} (D = {plate_diameter} mm) ~ DIN 18134:2012-04", 
                ParagraphStyle('title', fontSize=12, alignment=1)))
        
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            f"{app.tr('test_point')} {test_number} | {app.tr('station')}: {station} | {app.tr('side')}: {side}", 
            ParagraphStyle('centered_info', parent=styles['Normal'], alignment=1, fontSize=11)
        ))
    
        elements.append(Spacer(1, 20))
    
        # Metadata Table
        metadata_table_data = [
            [app.tr('client_name'), app.client_name.text()],
            [app.tr('project_name'), app.project_name.text()],
            [app.tr('contractor_name'), app.contractor_name.text()],
            [app.tr('material_type'), app.material_type.text()],
            [app.tr('date'), app.date.text()],
            [app.tr('weather_temp'), app.weather_temp.text()],
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
    
        grouped_data = {cycle: [] for cycle in CYCLE_TYPE_IDS}
    
        for load, settlement, cycle in group_raw_points:
            if cycle in grouped_data:
                grouped_data[cycle].append((load, settlement))
    
        for cycle in CYCLE_TYPE_IDS:
            for load, settlement in grouped_data[cycle]:
                stress = load / area / 1000
                raw_data.append([
                    f"{load:.2f}",
                    f"{stress:.3f}",
                    f"{settlement:.2f}"
                ])
            
            if cycle != "second_loading":
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
            Paragraph(f"{app.tr('load_header')}<br/><font size=7>{app.tr('kN_unit')}</font>", header_style),
            Paragraph(f"{app.tr('stress_header')}<br/><font size=7>{app.tr('MNm2_unit')}</font>", header_style),
            Paragraph(f"{app.tr('settlement_header')}<br/><font size=7>{app.tr('mm_unit')}</font>", header_style)
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
    
        # Plot to image - create a NEW figure for PDF export only
        canvas = layout.itemAt(0).widget()
        original_fig = canvas.figure
        
        # Create a new figure specifically for PDF export
        pdf_fig = plt.figure(figsize=(8, 6), dpi=300)
        new_ax = pdf_fig.add_subplot(111)
        orig_ax = original_fig.axes[0]
        
        # Copy all lines and their properties
        for orig_line in orig_ax.lines:
            xdata = orig_line.get_xdata()
            ydata = orig_line.get_ydata()
        
            if len(set(xdata)) == 1:
                x = xdata[0]
                new_ax.axvline(
                    x=x,
                    color=orig_line.get_color(),
                    linestyle=orig_line.get_linestyle(),
                    linewidth=orig_line.get_linewidth() * 1.5,
                    label=orig_line.get_label() if orig_line.get_label() != '_nolegend_' else None
                )
            elif len(set(ydata)) == 1:
                y = ydata[0]
                new_ax.axhline(
                    y=y,
                    color=orig_line.get_color(),
                    linestyle=orig_line.get_linestyle(),
                    linewidth=orig_line.get_linewidth() * 1.5,
                    label=orig_line.get_label() if orig_line.get_label() != '_nolegend_' else None
                )
            else:
                new_ax.plot(
                    xdata,
                    ydata,
                    color=orig_line.get_color(),
                    linestyle=orig_line.get_linestyle(),
                    linewidth=orig_line.get_linewidth() * 1.5,
                    marker=orig_line.get_marker(),
                    markersize=orig_line.get_markersize(),
                    label=orig_line.get_label() if orig_line.get_label() != '_nolegend_' else None
                )

        # Copy patches (like bars, rectangles, etc.)
        for patch in orig_ax.patches:
            new_patch = copy.copy(patch)
            new_ax.add_patch(new_patch)
        
        # Copy collections (like scatter plots)
        for collection in orig_ax.collections:
            new_collection = copy.copy(collection)
            new_ax.add_collection(new_collection)
        
        # Copy text elements
        for text in orig_ax.texts:
            if text.get_transform() == orig_ax.transData:
                # Probably a manual annotation, safe to copy
                font_props = text.get_fontproperties()
                new_ax.text(text.get_position()[0], text.get_position()[1],
                            text.get_text(),
                            fontsize=font_props.get_size(),
                            fontfamily=font_props.get_family()[0] if font_props.get_family() else None,
                            fontweight=font_props.get_weight(),
                            fontstyle=font_props.get_style(),
                            transform=text.get_transform())

        # Copy axis properties
        new_ax.set_xlabel(orig_ax.get_xlabel(), fontsize=10)
        new_ax.set_ylabel(orig_ax.get_ylabel(), fontsize=10)
        new_ax.set_title(orig_ax.get_title(), fontsize=11.5)
        new_ax.tick_params(axis='both', which='major', labelsize=9)
        
        # FORCE GRID TO APPEAR with nice styling
        new_ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        
        # Copy axis limits
        new_ax.set_xlim(orig_ax.get_xlim())
        new_ax.set_ylim(orig_ax.get_ylim())
        
        # Copy tick labels and formatting
        new_ax.xaxis.set_major_formatter(orig_ax.xaxis.get_major_formatter())
        new_ax.yaxis.set_major_formatter(orig_ax.yaxis.get_major_formatter())
        
        # Copy legend if it exists
        if orig_ax.get_legend() is not None:
            handles, labels = orig_ax.get_legend_handles_labels()
            legend = new_ax.legend(handles, labels, 
                                 loc=orig_ax.get_legend()._loc)
            # Set legend font properties
            for text in legend.get_texts():
                orig_text = orig_ax.get_legend().get_texts()[0]
                font_props = orig_text.get_fontproperties()
                text.set_fontsize(font_props.get_size())
                text.set_family(font_props.get_family()[0] if font_props.get_family() else None)
                text.set_weight(font_props.get_weight())
                text.set_style(font_props.get_style())
        
        # Save the PDF-specific figure
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            pdf_fig.savefig(tmpfile.name, dpi=300, bbox_inches='tight', facecolor='white')
            
            # Load image and calculate dimensions
            img = PILImage.open(tmpfile.name)
            img_width_px, img_height_px = img.size
            image_width_cm = img_width_px / 300 * 2.54
            image_height_cm = img_height_px / 300 * 2.54
            
            # Page layout calculations
            PAGE_WIDTH = 21 * cm
            LEFT_MARGIN = 1 * cm
            RIGHT_MARGIN = 1 * cm
            GAP = 0.1 * cm
            available_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
            table_width = 5.4 * cm  # 3 columns × 1.8cm
            max_plot_width = available_width - table_width - GAP
            
            # Scale plot if needed while maintaining aspect ratio
            if image_width_cm * cm > max_plot_width:
                scale_factor = float(max_plot_width) / float(image_width_cm * cm)
                plot_width = max_plot_width
                plot_height = image_height_cm * cm * scale_factor
            else:
                plot_width = image_width_cm * cm
                plot_height = image_height_cm * cm
            
            plot_image = Image(tmpfile.name, width=plot_width, height=plot_height)
        
        # Clean up the PDF figure
        plt.close(pdf_fig)
        
        table_height_lines = len(stress_table._cellvalues)
        row_height_cm = 0.5
        table_height_cm = table_height_lines * row_height_cm
        vertical_padding_cm = max((plot_height/cm - table_height_cm) / 2, 0)
        
        table_with_padding = [
            Spacer(1, vertical_padding_cm * cm),
            stress_table,
            Spacer(1, vertical_padding_cm * cm)
        ]
        
        content_row = [
            Spacer(LEFT_MARGIN, 0),
            table_with_padding,
            Spacer(GAP, 0),
            plot_image,
            Spacer(RIGHT_MARGIN, 0)
        ]
        
        col_widths = [
            LEFT_MARGIN,
            table_width,
            GAP,
            plot_width,
            RIGHT_MARGIN
        ]
        
        combined_table = Table([content_row], colWidths=col_widths)
        combined_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(combined_table)
        elements.append(Spacer(1, 20))

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
                ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('SPAN', (-1, -2), (-1, -1)),
            ]))

            elements.append(ev_table)
            if i < app.graphs_stack.count() - 1:
                elements.append(PageBreak())

    elements.append(Spacer(1, 0.1 * inch))