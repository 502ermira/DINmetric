APP_STYLE = """
QWidget {
    background-color: #fafafa;
    font-family: Arial;
    font-size: 23px;
}

QLabel {
    font-weight: normal;
    color: #333;
}

QLineEdit, QComboBox, QPushButton {
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

QPushButton {
    background-color: #e8e8e8;
}

QPushButton:hover {
    background-color: #d0d0d0;
}

QTableWidget {
    background-color: #fff;
    border: 1px solid #ccc;
    gridline-color: #ddd;
}

QHeaderView::section {
    background-color: #eee;
    font-weight: bold;
    padding: 4px;
    border: 1px solid #ccc;
}

QScrollArea {
    border: none;
}

/* Table Delete Button Styling */
QTableWidget QPushButton {
    padding: 0;
    margin: 0;
    border: none;
    background: transparent;
    min-width: 0;
}

QTableWidget QPushButton:hover {
    background: rgba(255, 0, 0, 20);
}

/* Compact delete button in last column */
QTableWidget QHeaderView::section:last {
    padding: 0;
    margin: 0;
}

/* Station and Side columns */
QTableWidget QLineEdit {
    font-size: 25px;
    padding: 5px;
}

QComboBox {
    min-width: 200px;
    height: 40px;
}

QComboBox QAbstractItemView {
    font-size: 25px;
    padding: 10px;
}

QComboBox::drop-down {
    width: 30px;
}


"""