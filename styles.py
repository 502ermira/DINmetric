APP_STYLE = """
/* Main Window and General Styling */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    color: #333333;
    background-color: #f8f8f8;
}

/* Sidebar Styling */
QWidget#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
}

/* Buttons */
QPushButton {
    background-color: #eee;
    border: 1px solid #d0d0d0;
    border-radius: 5px;
    padding: 6px 12px;
    font-weight: 500;
    font-size: 12.5px;
}

QPushButton:hover {
    background-color: #d0d0d0;
    border-color: #c0c0c0;
}

QPushButton:pressed {
    background-color: #ddd;
}

QPushButton#sidebarToggle:hover,
QPushButton#prevButton:hover,
QPushButton#nextButton:hover {
    background-color: #d0d0d0;
}

/* Line Edits */
QLineEdit {
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
}

QLineEdit:focus {
    border: 1px solid #a0a0a0;
}

/* Combo Boxes */
QComboBox {
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
}

QComboBox:hover {
    border-color: #c0c0c0;
}

/* Table Widget */
QTableWidget {
    background-color: white;
    border: 1px solid #d0d0d0;
    gridline-color: #e0e0e0;
    selection-background-color: #e0e0e0;
    selection-color: #333333;
}

QHeaderView::section {
    background-color: #f0f0f0;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #d0d0d0;
    font-weight: 500;
}

QTableCornerButton::section {
    background-color: #f0f0f0;
    border: none;
    border-bottom: 1px solid #d0d0d0;
    border-right: 1px solid #d0d0d0;
}

/* Scroll Area */
QScrollArea {
    border: 1px solid #d0d0d0;
    background-color: white;
}

/* Form Layout Labels */
QLabel {
    font-weight: 500;
}

/* Message Box */
QMessageBox {
    background-color: white;
}

QMessageBox QLabel {
    font-size: 12px;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* Graph Container */
GraphCanvas {
    background-color: white;
    border: 1px solid #d0d0d0;
}
"""