import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSplitter, QWidget, QLabel, QTreeView, QVBoxLayout, QPushButton,
                             QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, QDir
import PyPDF2
from config import *
from PyQt6.QtGui import QIcon, QFileSystemModel
from PyQt6.QtWidgets import QFileDialog


class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Explorer")
        self.setGeometry(X_AXIS, Y_AXIS, WINDOW_WIDTH, WINDOW_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        splitter = QSplitter()
        layout.addWidget(splitter)

        # Left panel (Source)
        source_panel = QWidget()
        source_layout = QVBoxLayout()
        source_panel.setLayout(source_layout)

        source_label = QLabel("Source")
        source_layout.addWidget(source_label)

        self.source_tree = QTreeView()
        self.source_model = QFileSystemModel()
        self.source_model.setRootPath(QDir.rootPath())
        self.source_tree.setModel(self.source_model)
        self.source_tree.setRootIndex(self.source_model.index(""))
        self.source_tree.setColumnWidth(0, 150)
        self.source_tree.setColumnWidth(1, 50)
        self.source_tree.setColumnWidth(2, 100)
        self.source_tree.setColumnWidth(3, 100)
        self.source_tree.setAnimated(False)
        self.source_tree.setIndentation(20)
        self.source_tree.setSortingEnabled(True)
        self.source_tree.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        source_layout.addWidget(self.source_tree)

        splitter.addWidget(source_panel)

        # Arrow buttons layout
        arrow_buttons_layout = QVBoxLayout()
        arrow_buttons_widget = QWidget()
        arrow_buttons_widget.setLayout(arrow_buttons_layout)
        splitter.addWidget(arrow_buttons_widget)

        # Arrow buttons
        add_button = QPushButton("->")
        remove_button = QPushButton("<-")

        arrow_buttons_layout.addWidget(add_button)
        arrow_buttons_layout.addWidget(remove_button)

        # Right panel (Target)
        target_panel = QWidget()
        target_layout = QVBoxLayout()
        target_panel.setLayout(target_layout)

        target_label = QLabel("Target (PDF Files to Merge)")
        target_layout.addWidget(target_label)

        # Table layout for checkboxes, names, and sequences
        self.table_layout = QTableWidget()
        self.table_layout.setColumnCount(len(TABLE_COLUMN_WIDTHS))
        self.table_layout.setHorizontalHeaderLabels(TABLE_HEADER_LABELS)
        for i, width in enumerate(TABLE_COLUMN_WIDTHS):
            self.table_layout.setColumnWidth(i, width)
        target_layout.addWidget(self.table_layout)

        splitter.addWidget(target_panel)

        # Bottom: Merge Button
        merge_button = QPushButton("Merge PDFs")
        layout.addWidget(merge_button)

        merge_button.clicked.connect(self.merge_pdf)

        # Connect arrow buttons to functions
        add_button.clicked.connect(self.add_to_target)
        remove_button.clicked.connect(self.remove_from_target)

    def add_to_target(self):
        selected_indexes = self.source_tree.selectionModel().selectedIndexes()
        inc_index = 0
        while inc_index < len(selected_indexes):
            # Get the index for the file name (assuming it's the first column)
            file_index = selected_indexes[inc_index]
            file_path = self.source_model.filePath(file_index)
            print(file_path)  # Debug statement to check file paths
            if file_path.endswith(".pdf"):
                if not self.is_duplicate(file_path):
                    row_count = self.table_layout.rowCount()
                    self.table_layout.setRowCount(row_count + 1)

                    # Create checkbox
                    checkbox = QCheckBox()
                    checkbox.setChecked(True)
                    self.table_layout.setCellWidget(row_count, 0, checkbox)

                    # Create label for file name
                    name_item = QTableWidgetItem(os.path.basename(file_path))
                    self.table_layout.setItem(row_count, 1, name_item)

                    # Create sequence input box
                    sequence_input = QLineEdit()
                    sequence_input.setText(str(row_count + 1))  # Default sequence starts from 1
                    self.table_layout.setCellWidget(row_count, 2, sequence_input)

                    # Store file path in data role
                    self.table_layout.item(row_count, 1).setData(Qt.ItemDataRole.UserRole, file_path)
                else:
                    QMessageBox.warning(self, "Warning", "File is already added")
                    return
            inc_index += 4

        # If all files are added successfully, show a success message
        QMessageBox.information(self, "Success", "Files added successfully.")

    def remove_from_target(self):
        selected_rows = set(index.row() for index in self.table_layout.selectedIndexes())
        self.table_layout.rowCount()
        for row in sorted(selected_rows, reverse=True):
            self.table_layout.removeRow(row)

    def merge_pdf(self):
        if self.table_layout.rowCount() == 0:
            QMessageBox.warning(self, "Warning", "No files selected.")
            return

        # Get the output file path from the user
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF As", "", "PDF Files (*.pdf)")

        if output_file:
            pdf_writer = PyPDF2.PdfWriter()

            try:
                page_number = 1
                for row in range(self.table_layout.rowCount()):
                    checkbox = self.table_layout.cellWidget(row, 0)
                    if checkbox.isChecked():
                        file_path = self.table_layout.item(row, 1).data(Qt.ItemDataRole.UserRole)
                        pdf_reader = PyPDF2.PdfReader(file_path)
                        for page_index in range(len(pdf_reader.pages)):
                            page = pdf_reader.pages[page_index]
                            pdf_writer.add_page(page)  # Add the page to the writer
                            page_number += 1  # Increment page number

                with open(output_file, 'wb') as output:
                    pdf_writer.write(output)

                QMessageBox.information(self, "Success",
                                        "PDF files merged successfully! Output saved as {}".format(output_file))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def is_duplicate(self, file_path):
        for row in range(self.table_layout.rowCount()):
            path_item = self.table_layout.item(row, 1)
            if path_item and path_item.data(Qt.ItemDataRole.UserRole) == file_path:
                return True
        return False


def main():
    app = QApplication(sys.argv)
    window = FileExplorer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
