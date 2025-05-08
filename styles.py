APP_STYLE = """
/* Main Window and General Styling */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    color: #333333;
    background-color: #f9f9f9;
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

QComboBox:hover {
    border-color: #c0c0c0;
}

/* Table Widget */
QTableWidget {
    background-color: white;
    border: 1px solid #ccc;
    gridline-color: #aaa;
    selection-background-color: #e0e0e0;
    selection-color: #333333;
}

QTableWidget QLineEdit {
    background-color: white;
    border: none;
    selection-background-color: #e0e0e0;
    selection-color: #333333;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    outline: none;
}

QTableWidget QComboBox {
    border: none;
    background-color: white;
    outline: none;
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
    background-color: 111;
}

/* Form Layout Labels */
QLabel {
    font-weight: normal;
}

/* Message Box */
QMessageBox {
    background-color: white;
}

QMessageBox QLabel {
    font-size: 12px;
}

/* Graph Container */
GraphCanvas {
    border: 1px solid #d0d0d0;
}


QTableWidget#evResultsTable::item {
    font-size: 16px;
}

QPushButton#removeLogoButton {
    background-color: #FF5C5C;
    border: none;
    border-radius: 8px;
    padding: 0;
}

QPushButton#removeLogoButton:hover {
    background-color: #e53935;
}

/* Language Selector Compact Style */
#languageLabel {
    padding: 0;
    margin: 0;
    font-size: 12px;
}

#languageComboBox {
    min-height: 22px;
    max-height: 22px;
    padding: 0 4px;
    margin: 0;
}

"""