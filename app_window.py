from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QFileDialog, QSizePolicy,
    QHeaderView, QMessageBox, QScrollArea, QStackedWidget, QStyle, QFormLayout
)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QPixmap, QIcon

from constants import CYCLE_TYPES, CYCLE_TYPE_IDS
from data_handler import evaluate_test_secant
from data_handler import evaluate_test_curve_fit
from pdf_exporter import export_to_pdf
from translations import translations

class PlateLoadTestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_language = "sq" 
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle(self.tr("app_title"))
        self.setMinimumSize(900, 650)
        self.sidebar_expanded = False
        self.init_ui()

    def tr(self, key):
        """Translation helper method"""
        return translations[self.current_language].get(key, key)

    def init_ui(self):
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setMinimumWidth(0)
        self.sidebar_widget.setMaximumWidth(0)
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.language_selector = QComboBox()
        self.language_selector.addItem("Shqip", "sq")
        self.language_selector.addItem("English", "en")
        self.language_selector.currentIndexChanged.connect(self.change_language)
        self.language_selector.setObjectName("languageComboBox")
        
        language_row = QHBoxLayout()
        language_row.setContentsMargins(0, 2, 0, 2)
        language_row.setSpacing(4)
        
        language_label = QLabel(self.tr("language"))
        language_label.setObjectName("languageLabel")
        language_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        language_row.addWidget(language_label)
        language_row.addWidget(self.language_selector, stretch=1)
        
        self.sidebar_layout.addLayout(language_row)

        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("sidebarToggle")
        self.toggle_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.toggle_button.setText(self.tr("show_report_details"))
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        hint_width = self.toggle_button.sizeHint().width()
        self.toggle_button.setFixedWidth(hint_width + 12)
        scale_factor = self.devicePixelRatioF()
        self.toggle_button.setFixedWidth(int((hint_width + 12) * scale_factor))

        # --- Top form: Meta Information ---
        top_form_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # --- Logos ---
        logos_layout = QVBoxLayout()
        self.company_logo_path = None
        self.accreditation_logo_path = None
        
        # Company Logo Upload
        company_layout = QHBoxLayout()
        self.company_logo_btn = QPushButton()
        self.company_logo_btn.setCursor(Qt.PointingHandCursor)
        self.company_logo_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Company Logo Container
        self.company_logo_container = QFrame()
        self.company_logo_container.setFixedSize(70, 35)
        self.company_logo_container.setLayout(QVBoxLayout())
        self.company_logo_container.layout().setContentsMargins(0, 0, 0, 0)
        self.company_logo_container.layout().setSpacing(0)
        
        # Company Logo Preview
        self.company_logo_preview = QLabel(self.company_logo_container)
        self.company_logo_preview.setAlignment(Qt.AlignCenter)
        self.company_logo_preview.setFixedSize(70, 35)
        
        # Company Logo Remove Button
        self.company_logo_remove_btn = QPushButton(self.company_logo_container)
        self.company_logo_remove_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.company_logo_remove_btn.setFixedSize(16, 16)
        self.company_logo_remove_btn.move(70 - 16, 0)
        self.company_logo_remove_btn.setObjectName("removeLogoButton")

        self.company_logo_remove_btn.setCursor(Qt.PointingHandCursor)
        self.company_logo_remove_btn.hide()
        self.company_logo_remove_btn.clicked.connect(self.remove_company_logo)
        
        self.company_logo_container.layout().addWidget(self.company_logo_preview)
        self.company_logo_container.hide()
        
        company_layout.addWidget(self.company_logo_btn)
        company_layout.addWidget(self.company_logo_container)
        company_layout.setAlignment(Qt.AlignLeft)
        
        # Accreditation Logo Upload
        accreditation_layout = QHBoxLayout()
        self.accreditation_logo_btn = QPushButton()
        self.accreditation_logo_btn.setCursor(Qt.PointingHandCursor)
        self.accreditation_logo_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Accreditation Logo Container
        self.accreditation_logo_container = QFrame()
        self.accreditation_logo_container.setFixedSize(70, 35)
        self.accreditation_logo_container.setLayout(QVBoxLayout())
        self.accreditation_logo_container.layout().setContentsMargins(0, 0, 0, 0)
        self.accreditation_logo_container.layout().setSpacing(0)
        
        # Accreditation Logo Preview
        self.accreditation_logo_preview = QLabel(self.accreditation_logo_container)
        self.accreditation_logo_preview.setAlignment(Qt.AlignCenter)
        self.accreditation_logo_preview.setFixedSize(70, 35)
        
        # Accreditation Logo Remove 
        self.accreditation_logo_remove_btn = QPushButton(self.accreditation_logo_container)
        self.accreditation_logo_remove_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.accreditation_logo_remove_btn.setFixedSize(16, 16)
        self.accreditation_logo_remove_btn.move(70 - 16, 0)
        self.accreditation_logo_remove_btn.setObjectName("removeLogoButton")
        self.accreditation_logo_remove_btn.setCursor(Qt.PointingHandCursor)
        self.accreditation_logo_remove_btn.hide()
        self.accreditation_logo_remove_btn.clicked.connect(self.remove_accreditation_logo)
        
        self.accreditation_logo_container.layout().addWidget(self.accreditation_logo_preview)
        self.accreditation_logo_container.hide()
        
        accreditation_layout.addWidget(self.accreditation_logo_btn)
        accreditation_layout.addWidget(self.accreditation_logo_container)
        accreditation_layout.setAlignment(Qt.AlignLeft)
        
        self.company_logo_btn.clicked.connect(self.upload_company_logo)
        self.accreditation_logo_btn.clicked.connect(self.upload_accreditation_logo)
        
        logos_layout.addLayout(company_layout)
        logos_layout.addLayout(accreditation_layout)
        self.sidebar_layout.addLayout(logos_layout)

        def make_row(label_key, widget):
            row = QHBoxLayout()
            label = QLabel(self.tr(label_key))
            row.addWidget(label)
            row.addWidget(widget)
            return row, label

        # --- Sidebar Content ---
        sidebar_info = [
            ("test_id", QLineEdit()),
            ("company_name", QLineEdit()),
            ("slogan", QLineEdit()),
            ("code", QLineEdit()),
            ("version", QLineEdit()),
            ("date", QLineEdit()),
            ("other_info", QLineEdit()),
            ("client_name", QLineEdit()),
            ("project_name", QLineEdit()),
            ("contractor_name", QLineEdit()),
            ("request_number", QLineEdit()),
            ("weather_temp", QLineEdit()),
            ("designed_by", QLineEdit()),
            ("measured_by", QLineEdit()),
            ("supervisor", QLineEdit()),
            ("laboratory", QLineEdit()),
            ("material_type", QLineEdit())
        ]

        self.sidebar_labels = []
        
        for label_key, field in sidebar_info:
            row_layout, label = make_row(label_key, field)
            self.sidebar_layout.addLayout(row_layout)
            self.sidebar_labels.append((label_key, label))

        (self.test_id, self.company_name, self.company_slogan, self.code, self.version,
         self.date, self.other_info, self.client_name, self.project_name,
         self.contractor_name, self.request_number, self.weather_temp,
         self.designed_by, self.measured_by, self.supervisor, self.laboratory,
         self.material_type) = [field for _, field in sidebar_info]

        # --- Always Visible Fields ---
        self.plate_diameter = QComboBox()
        self.plate_diameter.addItems(["300", "600", "762"])
        
        self.measurement_device_selector = QComboBox()
        self.measurement_device_selector.addItems([
            "Direct Measurement Device",
            "Lever-Arm System"
        ])
        self.measurement_device_selector.currentIndexChanged.connect(self.toggle_lever_ratio_field)
        
        self.lever_ratio_label = QLabel("Lever Ratio (hp/hm)")
        self.lever_ratio = QLineEdit("1.000")
        
        self.method_selector = QComboBox()
        self.method_selector.addItems([
            "DIN 18134 official method (2nd-degree curve fit)",
            "Practical Secant Approximation"
        ])
        
        self.lever_ratio_label.setVisible(False)
        self.lever_ratio.setVisible(False)
        
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setHorizontalSpacing(23)
        
        self.plate_diameter_label = QLabel(self.tr("plate_diameter"))
        self.measurement_device_label = QLabel(self.tr("measurement_device"))
        self.method_selector_label = QLabel(self.tr("calculation_method"))
        
        form_layout.addRow(self.plate_diameter_label, self.plate_diameter)
        form_layout.addRow(self.measurement_device_label, self.measurement_device_selector)
        form_layout.addRow(self.lever_ratio_label, self.lever_ratio)
        form_layout.addRow(self.method_selector_label, self.method_selector)
        
        # Store the form layout as an instance variable
        self.form_layout = form_layout

        scale_factor = self.devicePixelRatioF()
        label_width = int(60 * scale_factor)
        for i in range(form_layout.rowCount()):
            label_item = form_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item:
                label_widget = label_item.widget()
                if label_widget:
                    label_widget.setMinimumWidth(label_width)

        top_form_layout.addWidget(self.toggle_button)
        top_form_layout.addLayout(form_layout)
        top_form_layout.setContentsMargins(0, 0, 0, 19)

        # --- Table: Load-Settlement Data ---
        self.table = QTableWidget(16, 6)
        self.table.setHorizontalHeaderLabels([
            "Load (kN)", "Settlement (mm)", "Cycle Type",
            "Station", "Side", ""
        ])
        for col in range(6):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        for row in range(16):
            self.setup_row(row)

        # --- Action Buttons ---
        action_buttons_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("Add Row")
        self.calc_btn = QPushButton("Evaluate")
        self.export_btn = QPushButton("Export to PDF")
        self.clear_btn = QPushButton("Clear")

        action_buttons_layout.addWidget(self.add_row_btn)
        action_buttons_layout.addWidget(self.calc_btn)
        action_buttons_layout.addWidget(self.export_btn)
        action_buttons_layout.addWidget(self.clear_btn)

        self.add_row_btn.clicked.connect(self.add_row)
        self.clear_btn.clicked.connect(self.clear_fields)
        self.calc_btn.clicked.connect(self.run_selected_method)
        self.export_btn.clicked.connect(lambda: export_to_pdf(self))

        self.graphs_stack = QStackedWidget()
        self.graph_container = QWidget()
        self.graph_container.setLayout(QVBoxLayout())
        self.graph_container.layout().addWidget(self.graphs_stack)

        self.graph_scroll = QScrollArea()
        self.graph_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graph_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graph_scroll.setWidgetResizable(True)
        self.graph_scroll.setWidget(self.graph_container)
        self.graph_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton()
        self.prev_btn.setObjectName("prevButton")
        self.prev_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.prev_btn.setText(" Previous")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        
        self.next_btn = QPushButton()
        self.next_btn.setObjectName("nextButton")
        self.next_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.next_btn.setText(" Next")
        self.next_btn.setCursor(Qt.PointingHandCursor)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        self.prev_btn.clicked.connect(self.show_prev_graph)
        self.next_btn.clicked.connect(self.show_next_graph)

        center_split = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.data_label = QLabel(self.tr("enter_data"))
        left_panel.addWidget(self.data_label)
        left_panel.addWidget(self.table)
        left_panel.addLayout(action_buttons_layout)

        center_split.addWidget(self.sidebar_widget, stretch=1)
        center_split.addLayout(left_panel, stretch=4)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self.graph_scroll)
        right_panel.addLayout(nav_layout)
        center_split.addLayout(right_panel, stretch=4)

        # top form and center content combined into one vertical layout
        main_content_layout = QVBoxLayout()
        main_content_layout.addLayout(top_form_layout)
        main_content_layout.addLayout(center_split)

        # central widget that holds everything except the sidebar
        main_content_widget = QWidget()
        main_content_widget.setLayout(main_content_layout)

        # Horizontal layout to hold sidebar + everything else
        full_layout = QHBoxLayout()
        full_layout.addWidget(self.sidebar_widget)
        full_layout.addWidget(main_content_widget, stretch=1)

        self.setLayout(full_layout)
        self.update_ui_language()

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar_widget.setMaximumWidth(0)
            self.toggle_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
            self.toggle_button.setText(self.tr("show_report_details"))
            self.sidebar_expanded = False
        else:
            self.sidebar_widget.setMaximumWidth(self.width() // 5)
            self.toggle_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
            self.toggle_button.setText(self.tr("hide_report_details"))
            self.sidebar_expanded = True

    def setup_table_rows(self, num_rows):
        for row in range(num_rows):
            self.setup_row(row)

    def setup_row(self, row):
        combo = QComboBox()
        combo.addItem("", "")
        for cycle_id in CYCLE_TYPE_IDS:
            label = self.tr(cycle_id)
            combo.addItem(label, cycle_id)
        self.table.setCellWidget(row, 2, combo)
    
        self.table.setCellWidget(row, 3, QLineEdit())
        self.table.setCellWidget(row, 4, QLineEdit())
    
        delete_btn = QPushButton()
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.setToolTip(self.tr("delete_row_tooltip"))
        delete_btn.clicked.connect(lambda _, r=row: self.confirm_delete_row(r))
        self.table.setCellWidget(row, 5, delete_btn)

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
                delete_btn = QPushButton()
                delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
                delete_btn.clicked.connect(lambda _, r=i: self.confirm_delete_row(r))
            self.table.setCellWidget(i, 5, delete_btn)

    def clear_fields(self):
       # Clear text fields
       fields = [
           self.test_id, self.company_name, self.company_slogan, self.code, self.version,
           self.date, self.other_info, self.client_name, self.project_name,
           self.contractor_name, self.request_number, self.weather_temp,
           self.designed_by, self.measured_by, self.supervisor, self.laboratory,
           self.material_type, self.lever_ratio
       ]
       for field in fields:
           field.clear()
   
       # Reset combo boxes
       self.plate_diameter.setCurrentIndex(0)
       self.measurement_device_selector.setCurrentIndex(0)
       self.method_selector.setCurrentIndex(0)
   
       # Reset visibility of lever ratio
       self.toggle_lever_ratio_field()
   
       # Clear table contents
       self.table.setRowCount(16)
       for row in range(16):
           for col in range(self.table.columnCount()):
               item = self.table.item(row, col)
               if item:
                   self.table.setItem(row, col, QTableWidgetItem(""))
               widget = self.table.cellWidget(row, col)
               if isinstance(widget, QLineEdit):
                   widget.clear()
               elif hasattr(widget, 'setCurrentIndex'):
                   widget.setCurrentIndex(0)
   
       # Reset company and accreditation logos
       self.company_logo_preview.clear()
       self.company_logo_container.hide()
       self.company_logo_remove_btn.hide()
       self.company_logo_path = None
   
       self.accreditation_logo_preview.clear()
       self.accreditation_logo_container.hide()
       self.accreditation_logo_remove_btn.hide()
       self.accreditation_logo_path = None
   
       # Clear graphs
       while self.graphs_stack.count():
           widget = self.graphs_stack.widget(0)
           self.graphs_stack.removeWidget(widget)
           widget.deleteLater()
   
    def run_selected_method(self):
        method_index = self.method_selector.currentIndex()
        if method_index == 0:
            evaluate_test_curve_fit(self)
        elif method_index == 1:
            evaluate_test_secant(self)

    def show_prev_graph(self):
        index = self.graphs_stack.currentIndex()
        if index > 0:
            self.graphs_stack.setCurrentIndex(index - 1)

    def show_next_graph(self):
        index = self.graphs_stack.currentIndex()
        if index < self.graphs_stack.count() - 1:
            self.graphs_stack.setCurrentIndex(index + 1)

    def upload_company_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("add_company_logo"), "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.company_logo_path = file_path
            pixmap = QPixmap(file_path).scaled(self.company_logo_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.company_logo_preview.setPixmap(pixmap)
            self.company_logo_container.show() 
            self.company_logo_remove_btn.show()
            self.company_logo_btn.setText(self.tr("change_company_logo"))

    def upload_accreditation_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("add_accreditation_logo"), "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.accreditation_logo_path = file_path
            pixmap = QPixmap(file_path).scaled(self.accreditation_logo_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.accreditation_logo_preview.setPixmap(pixmap)
            self.accreditation_logo_container.show() 
            self.accreditation_logo_remove_btn.show()
            self.accreditation_logo_btn.setText(self.tr("add_accreditation_logo"))

    def remove_company_logo(self):
        self.company_logo_path = None
        self.company_logo_preview.clear()
        self.company_logo_container.hide()
        self.company_logo_remove_btn.hide()
        self.company_logo_btn.setText(self.tr("add_company_logo"))

    def remove_accreditation_logo(self):
        self.accreditation_logo_path = None
        self.accreditation_logo_preview.clear()
        self.accreditation_logo_container.hide()
        self.accreditation_logo_remove_btn.hide()
        self.accreditation_logo_btn.setText(self.tr("add_accreditation_logo"))

    def toggle_lever_ratio_field(self):
        lever_arm_text = self.tr("lever_arm_system") 
        if self.measurement_device_selector.currentText() == lever_arm_text:
            self.lever_ratio_label.setVisible(True)
            self.lever_ratio.setVisible(True)
        else:
            self.lever_ratio_label.setVisible(False)
            self.lever_ratio.setVisible(False)
            self.lever_ratio.setText("1.000")

    def update_ui_language(self):
        """Update all UI elements with the current language"""
        # Update toggle button
        if self.sidebar_expanded:
            self.toggle_button.setText(self.tr("hide_report_details"))
            self.toggle_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        else:
            self.toggle_button.setText(self.tr("show_report_details"))
            self.toggle_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))


        for i in range(self.sidebar_layout.count()):
            item = self.sidebar_layout.itemAt(i)
            if isinstance(item, QHBoxLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if isinstance(widget, QLabel) and widget.text() in ["Gjuha: ", "Language: "]:
                        widget.setText(self.tr("language"))
                        break
        
        # Update logos buttons
        if hasattr(self, 'company_logo_path') and self.company_logo_path is not None:
            self.company_logo_btn.setText(self.tr("change_company_logo"))
        else:
            self.company_logo_btn.setText(self.tr("add_company_logo"))
            
        if hasattr(self, 'accreditation_logo_path') and self.accreditation_logo_path is not None:
            self.accreditation_logo_btn.setText(self.tr("change_accreditation_logo"))
        else:
            self.accreditation_logo_btn.setText(self.tr("add_accreditation_logo"))
        
        # Update form labels - we need to get the label widgets from the form layout
        for i in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item:
                label_widget = label_item.widget()
                if label_widget:
                    if i == 0:  # Plate Diameter label
                        label_widget.setText(self.tr("plate_diameter"))
                    elif i == 1:  # Measurement Device label
                        label_widget.setText(self.tr("measurement_device"))
                    elif i == 2:  # Lever Ratio label
                        self.lever_ratio_label.setText(self.tr("lever_ratio"))
                    elif i == 3:  # Calculation Method label
                        label_widget.setText(self.tr("calculation_method"))
        
        # Update table headers
        self.table.setHorizontalHeaderLabels([
            self.tr("load"), self.tr("settlement"), self.tr("cycle_type"),
            self.tr("station"), self.tr("side"), ""
        ])
        
        # Update action buttons
        self.add_row_btn.setText(self.tr("add_row"))
        self.clear_btn.setText(self.tr("clear"))
        self.calc_btn.setText(self.tr("evaluate"))
        self.export_btn.setText(self.tr("export_pdf"))
        
        # Update navigation buttons
        self.prev_btn.setText(self.tr("previous"))
        self.next_btn.setText(self.tr("next"))
        
        # Update other labels - you'll need to create self.data_label in init_ui()
        if hasattr(self, 'data_label'):
            self.data_label.setText(self.tr("enter_data"))
        
        # Update combo boxes - we don't setText but update items
        current_measurement_device = self.measurement_device_selector.currentText()
        self.measurement_device_selector.clear()
        self.measurement_device_selector.addItems([
            self.tr("direct_measurement"),
            self.tr("lever_arm_system")
        ])
        # Try to restore selection
        for i in range(self.measurement_device_selector.count()):
            if self.measurement_device_selector.itemText(i) == current_measurement_device:
                self.measurement_device_selector.setCurrentIndex(i)
                break
        
        current_method = self.method_selector.currentText()
        self.method_selector.clear()
        self.method_selector.addItems([
            self.tr("din_method"),
            self.tr("secant_method")
        ])
        # Try to restore selection
        for i in range(self.method_selector.count()):
            if self.method_selector.itemText(i) == current_method:
                self.method_selector.setCurrentIndex(i)
                break

        # Update sidebar labels
        for label_key, label in self.sidebar_labels:
            label.setText(self.tr(label_key))

        # Update cycle types in table
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 2)
            if combo:
                current_data = combo.currentData()
                combo.clear()
                combo.addItem("", "")
                for cycle_id in CYCLE_TYPE_IDS:
                    combo.addItem(self.tr(cycle_id), cycle_id)
                index = combo.findData(current_data)
                if index != -1:
                    combo.setCurrentIndex(index)
        
        # Update delete button tooltips
        for row in range(self.table.rowCount()):
            delete_btn = self.table.cellWidget(row, 5)
            if delete_btn:
                delete_btn.setToolTip(self.tr("delete_row_tooltip"))

    def set_language(self, language_code):
        """Change the application language"""
        if language_code in translations:
            self.current_language = language_code
            self.update_ui_language()

    def change_language(self, index):
        language_code = self.language_selector.itemData(index)
        self.set_language(language_code)