import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QMenu,
                             QMessageBox, QScrollArea, QComboBox, QDialog, QRadioButton, QLineEdit, QDialogButtonBox,
                             QInputDialog, QTableWidget, QTableWidgetItem, QHBoxLayout,
                             QSpacerItem, QSizePolicy, QSplitter, QDialogButtonBox)
from PyQt6.QtGui import QImage, QPixmap, QPainter, QFont, QImageReader, QPalette, QBrush
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, Qt
import fitz  # PyMuPDF
import PyPDF2
import os


class SavePDFDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Save as PDF Options")
        self.layout = QVBoxLayout(self)

        self.radio_save = QRadioButton("Save")
        self.layout.addWidget(self.radio_save)

        self.radio_compression = QRadioButton("Save using Compression")
        self.layout.addWidget(self.radio_compression)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                           QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_save_option(self):
        if self.radio_save.isChecked():
            return "Save"
        elif self.radio_compression.isChecked():
            return "Save using Compression"


class PDFPageWidget(QLabel):
    def __init__(self, pixmap, page_num, doc_details):
        super().__init__()
        self.setPixmap(pixmap)
        self.page_num = page_num  # Store the page number
        self.page_name = ""  # Initialize page name
        self.custom_page_number = ""  # Custom page number text
        self.doc_details = doc_details

        self.page_number_label = QLabel(f"Page: {self.page_num}", self)
        self.page_number_label.move(10, 10)  # Adjust position as needed
        self.page_number_label.setStyleSheet("background-color: rgba(255, 255, 255, 150); padding: 5px;")

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        move_action = menu.addAction("Move Page...")
        delete_action = menu.addAction("Delete Page...")
        insert_action = menu.addAction("Insert File...")
        insert_image_action = menu.addAction("Insert Image...")
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == move_action:
            self.move_page()
        elif action == delete_action:
            self.delete_page()
        elif action == insert_action:
            self.insert_file()
        elif action == insert_image_action:  # Handle insert image action
            self.insert_image()

    def move_page(self):
        dialog = MovePageDialog(self)
        if dialog.exec():
            target_page = dialog.get_target_page()
            position = dialog.get_position()
            total_pages = self.parent().layout().count()

            # Adjust target_page if it exceeds the available indexes
            if position == "after" and target_page >= total_pages - 1:
                target_page = total_pages - 2  # Adjust to insert before the last page

            if 0 <= target_page < total_pages:
                if position == "before":
                    self.parent().layout().insertWidget(target_page, self)
                elif position == "after":
                    self.parent().layout().insertWidget(target_page + 1, self)

                # Update page numbers for all affected pages
                self.update_page_numbers()

    def delete_page(self):
        reply = QMessageBox.question(self, "Delete Page", "Are you sure you want to delete this page?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.parent().layout().removeWidget(self)  # Remove the widget from layout
            self.deleteLater()  # Delete the widget from memory

            # Update page numbers for all affected pages
            self.update_page_numbers()

    def insert_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("PDF files (*.pdf)")
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            reply = QMessageBox.question(self, "Insert Pages",
                                         f"Are you sure you want to insert {len(file_paths)} page(s) at page"
                                         f" {self.page_num + 1}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    insert_index = self.parent().layout().indexOf(self) + 1  # Get index of current widget
                    for file_path in file_paths:
                        doc = fitz.open(file_path)
                        for page_num in range(len(doc)):
                            page = doc.load_page(page_num)
                            pixmap = QPixmap.fromImage(QImage(page.get_pixmap().samples,
                                                              page.get_pixmap().width,
                                                              page.get_pixmap().height,
                                                              page.get_pixmap().stride,
                                                              QImage.Format.Format_RGB888))
                            new_page_widget = PDFPageWidget(pixmap, page_num,
                                                            self.doc_details)  # Create a new page widget
                            self.parent().layout().insertWidget(insert_index,
                                                                new_page_widget)  # Insert at proper index
                            insert_index += 1  # Increment insertion index
                        doc.close()

                    # Update page numbers for all affected pages
                    self.update_page_numbers()

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(self, "Error", f"Error inserting PDF: {e}")

    def update_page_numbers(self):
        layout = self.parent().layout()
        total_pages = layout.count()

        # Update page numbers for all pages in the layout
        for index in range(total_pages):
            widget = layout.itemAt(index).widget()
            if isinstance(widget, PDFPageWidget):
                widget.page_num = index + 1
                widget.page_number_label.setText(f"Page: {widget.page_num}")

    def insert_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("PNG files (*.png)")
        file_dialog.setViewMode(QFileDialog.List)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            options = self.get_image_options()  # Get user options (not defined in provided script)
            if options:
                page_selection, position, size = options
                for file_path in file_paths:
                    pixmap = QPixmap(file_path)
                    if page_selection == "Current Page":
                        self.insert_image_on_page(pixmap, position, size)
                    elif page_selection == "All Pages":
                        for index in range(self.parent().layout().count()):
                            widget = self.parent().layout().itemAt(index).widget()
                            if isinstance(widget, PDFPageWidget):  # Assuming PDFPageWidget is defined elsewhere
                                self.insert_image_on_page(pixmap, position, size)
                    else:
                        QMessageBox.critical(self, "Error", "Invalid page selection")
                    try:
                        reply = QMessageBox.question(
                            self, "Insert Image",
                            f"Are you sure you want to insert the image at page {self.page_num + 1}?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            self.insert_image_on_page(pixmap, position, size)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Error inserting image: {e}")
                        print(traceback.format_exc())

    def insert_image_on_page(self, pixmap, position, size):
        # Create a QLabel to hold the image
        image_widget = QLabel(self.parentWidget())  # Use the parent widget of the page widget

        # Check if the pixmap is loaded correctly
        if pixmap.isNull():
            print("Error: Pixmap is null.")
            return

        # Set the fixed size for the image widget
        fixed_width = fixed_height = 100  # Adjust the size as needed
        image_widget.setFixedSize(fixed_width, fixed_height)

        # Scale the pixmap to fit the fixed size
        scaled_pixmap = pixmap.scaled(fixed_width, fixed_height, Qt.AspectRatioMode.KeepAspectRatio)

        # Set the scaled pixmap as the image
        image_widget.setPixmap(scaled_pixmap)

        # Get the dimensions of the parent widget (the page widget)
        parent_width = self.width()
        parent_height = self.height()

        # Default values for image position
        image_x = image_y = 0

        # Adjust position based on the selected position
        if position == "Top Left":
            image_x = 0
            image_y = 0
        elif position == "Top Right":
            image_x = parent_width - fixed_width
            image_y = 0
        elif position == "Center":
            image_x = (parent_width - fixed_width) / 2
            image_y = (parent_height - fixed_height) / 2
        elif position == "Bottom Left":
            image_x = 0
            image_y = parent_height - fixed_height
        elif position == "Bottom Right":
            image_x = parent_width - fixed_width
            image_y = parent_height - fixed_height

        # Set the geometry of the image widget
        image_widget.move(image_x, image_y)

        # Show the image widget
        image_widget.show()

    def get_image_options(self):
        page_options = ["Current Page", "All Pages"]
        position_options = ["Top Left", "Top Right", "Center", "Bottom Left", "Bottom Right"]
        size_options = ["Small", "Medium", "Large"]

        page_selection, ok1 = QInputDialog.getItem(self, "Select Pages", "Select pages to insert the image:",
                                                   page_options, 0, False)
        position, ok2 = QInputDialog.getItem(self, "Select Position", "Select position to insert the image:",
                                             position_options, 0, False)
        size, ok3 = QInputDialog.getItem(self, "Select Size", "Select size for the image:",
                                         size_options, 0, False)

        if ok1 and ok2 and ok3:
            return page_selection, position, size
        else:
            return None


class MovePageDialog(QDialog):
    def __init__(self, parent=None):
        try:
            super().__init__(parent)

            print("Initializing MovePageDialog")

            self.setWindowTitle("Move Page")
            self.layout = QVBoxLayout(self)

            self.radio_before = QRadioButton("Before")
            self.radio_before.setChecked(True)
            self.layout.addWidget(self.radio_before)

            self.radio_after = QRadioButton("After")
            self.layout.addWidget(self.radio_after)

            self.page_number = QLineEdit(self)
            self.page_number.setPlaceholderText("Enter page number")
            self.layout.addWidget(self.page_number)

            self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                               QDialogButtonBox.StandardButton.Cancel)
            self.layout.addWidget(self.button_box)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)

            print("MovePageDialog initialization completed")

        except Exception as e:
            print("Error in MovePageDialog initialization:", e)

    def get_target_page(self):
        return int(self.page_number.text()) - 1

    def get_position(self):
        if self.radio_before.isChecked():
            return "before"
        elif self.radio_after.isChecked():
            return "after"


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Viewer")
        self.setGeometry(50, 50, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Create a splitter to manage the layout between table and scroll area
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)

        # Initialize table widget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)  # Add one more column for the delete button
        self.table_widget.setHorizontalHeaderLabels(["Document Name", "Start Page", "End Page", "Update Page", "", ""])
        self.table_widget.setColumnWidth(0, 100)
        self.table_widget.setColumnWidth(1, 80)
        self.table_widget.setColumnWidth(2, 80)
        self.table_widget.setColumnWidth(3, 80)
        self.table_widget.setColumnWidth(4, 50)  # Adjust column width for delete button
        # self.table_widget.setColumnWidth(5, 100)  # Adjust column width for delete button
        self.splitter.addWidget(self.table_widget)

        # Initialize scroll area
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedWidth(650)
        self.scroll_area.setWidget(self.scroll_widget)
        self.splitter.addWidget(self.scroll_area)

        # Buttons
        self.open_button = QPushButton("Open PDF")
        self.open_button.clicked.connect(self.open_pdf)
        self.layout.addWidget(self.open_button)

        self.save_button = QPushButton("Save as PDF")
        self.save_button.clicked.connect(self.save_as_pdf_dialog)
        self.layout.addWidget(self.save_button)

        self.doc_details = {}
        self.table_widget.cellClicked.connect(self.delete_row)

        self.table_widget.cellClicked.connect(self.add_page_number)

    def delete_row(self, row, column):
        if isinstance(self.sender(), QPushButton):  # Check if the signal is from a QPushButton
            button = self.sender()
            row = self.table_widget.indexAt(button.pos()).row()

            doc_name_item = self.table_widget.item(row, 0)
            if doc_name_item is not None:
                doc_name = doc_name_item.text()
                if doc_name in self.doc_details:
                    start_page_deleted = self.doc_details[doc_name]["start_page"]
                    end_page_deleted = self.doc_details[doc_name]["end_page"]
                    del self.doc_details[doc_name]

                    # Remove corresponding file widget from scroll area
                    for i in reversed(range(self.scroll_layout.count())):
                        widget = self.scroll_layout.itemAt(i).widget()
                        if isinstance(widget, PDFPageWidget) and widget.page_name == doc_name:
                            self.scroll_layout.removeWidget(widget)
                            widget.setParent(None)
                            widget.deleteLater()

                    # Update the page numbers and end page numbers of the remaining documents
                    for name, details in sorted(self.doc_details.items(), key=lambda x: x[1]["start_page"]):
                        if details["start_page"] > start_page_deleted:
                            details["start_page"] -= (end_page_deleted - start_page_deleted + 1)
                            details["end_page"] -= (end_page_deleted - start_page_deleted + 1)

                    # Update the displayed page widgets
                    for i in range(self.scroll_layout.count()):
                        widget = self.scroll_layout.itemAt(i).widget()
                        if isinstance(widget, PDFPageWidget):
                            widget.page_num = i + 1
                            widget.page_number_label.setText(f"Page: {widget.page_num}")
                            widget.page_name = self.get_doc_name_from_page_num(widget.page_num)

                    self.update_table()
                else:
                    QMessageBox.warning(self, "Error", "Document not found in details.")
            else:
                QMessageBox.warning(self, "Error", "Document name item is None.")

    def get_doc_name_from_page_num(self, page_num):
        for name, details in self.doc_details.items():
            if details["start_page"] <= page_num <= details["end_page"]:
                return name
        return None

    def add_page_number(self, doc_name):
        try:
            if doc_name in self.doc_details:
                page_number_name, ok = QInputDialog.getText(self, "Enter Page Number Name",
                                                            "Enter the page number name:")
                if ok and page_number_name:
                    self.doc_details[doc_name]['end_page'] += 1
                    # Update the doc_details dictionary with page number name
                    self.doc_details[doc_name][page_number_name] = self.doc_details[doc_name]['end_page']
                    self.update_table()
                elif not ok:
                    QMessageBox.warning(self, "Error", "Page number name cannot be empty.")
            else:
                QMessageBox.warning(self, "Error", "Document not found in details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding page number: {e}")

    def open_pdf(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("PDF files (*.pdf)")
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            for file_path in file_paths:
                self.display_pdf(file_path)

    def display_pdf(self, file_path):
        try:
            doc = fitz.open(file_path)
            start_page = 1 if not self.doc_details else max(self.doc_details.values(), key=lambda x: x["end_page"])[
                                                            "end_page"] + 1
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pixmap = QPixmap.fromImage(QImage(page.get_pixmap().samples, page.get_pixmap().width, page.get_pixmap().
                                                  height, page.get_pixmap().stride, QImage.Format.Format_RGB888))
                page_widget = PDFPageWidget(pixmap, start_page + page_num, self.doc_details)  # Adjust start page number
                page_widget.page_num = start_page + page_num  # Set the page number attribute
                page_widget.page_name = file_path.split("/")[-1]  # Set the page name attribute
                self.scroll_layout.addWidget(page_widget)

                # Overlay image on the PDF content
                image_path = "path/to/your/image.png"  # Adjust the path to your image
                image_pixmap = QPixmap(image_path)
                image_widget = QLabel(page_widget)
                image_widget.setPixmap(image_pixmap)
                image_widget.move(500, 800)  # Adjust the position as needed

            end_page = start_page + len(doc) - 1  # End page number
            doc_name = file_path.split("/")[-1]  # Document name
            # Update document details dictionary
            self.doc_details[doc_name] = {"start_page": start_page, "end_page": end_page}
            self.update_table()
        except Exception as e:
            print("Error opening PDF:", e)

    def update_table(self):
        self.table_widget.clearContents()
        self.table_widget.setRowCount(len(self.doc_details))
        row = 0
        prev_end_page = 0
        sorted_details = sorted(self.doc_details.items(), key=lambda x: x[1]["start_page"])
        for name, details in sorted_details:
            self.table_widget.setItem(row, 0, QTableWidgetItem(name))
            self.table_widget.setItem(row, 1, QTableWidgetItem(str(details["start_page"])))
            self.table_widget.setItem(row, 2, QTableWidgetItem(str(details["end_page"])))
            self.table_widget.setItem(row, 3, QTableWidgetItem(f"{details['start_page']}-{details['end_page']}"))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, r=row, c=4: self.delete_row(r, c))
            self.table_widget.setCellWidget(row, 4, delete_button)
            add_page_button = QPushButton("Add Page Number")
            add_page_button.clicked.connect(lambda _, doc_name=name: self.add_page_number(doc_name))
            self.table_widget.setCellWidget(row, 5, add_page_button)
            row += 1

    def delete_button_clicked(self):
        button = self.sender()
        index = self.table_widget.indexAt(button.pos())
        if index.isValid():
            self.table_widget.cellClicked.emit(index.row(), index.column())

    def save_as_pdf_dialog(self):
        dialog = SavePDFDialog(self)
        if dialog.exec():
            save_option = dialog.get_save_option()
            if save_option == "Save":
                self.save_as_pdf()
            elif save_option == "Save using Compression":
                self.save_as_pdf_compressed()

    def save_as_pdf(self):
        try:
            file_dialog = QFileDialog(self)
            file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setNameFilter("PDF files (*.pdf)")
            file_dialog.setDefaultSuffix("pdf")
            file_dialog.setViewMode(QFileDialog.ViewMode.List)

            if file_dialog.exec():
                file_path = file_dialog.selectedFiles()[0]
                if not file_path.lower().endswith('.pdf'):
                    file_path += '.pdf'
                self.save_pdf(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")

    def save_pdf(self, file_path):
        try:
            # Check if the directory exists, if not create it
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            print("Saving PDF to:", file_path)  # Debugging statement
            pdf_writer = fitz.open()
            for doc_name, details in sorted(self.doc_details.items(), key=lambda x: x[1]["start_page"]):
                doc = fitz.open(doc_name)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pdf_writer.insert_pdf(doc, from_page=page_num,
                                          to_page=page_num)  # Pass document object instead of name
                doc.close()
            pdf_writer.save(file_path)
            pdf_writer.close()
            QMessageBox.information(self, "Success", "PDF saved successfully.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "File not found.")
        except PermissionError:
            QMessageBox.critical(self, "Error", "Permission denied. Cannot save PDF to this location.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving PDF: {e}")

    def save_as_pdf_compressed(self):
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("PDF files (*.pdf)")
        file_dialog.setDefaultSuffix("pdf")
        file_dialog.setViewMode(QFileDialog.ViewMode.List)

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'
            self.save_pdf_compressed(file_path)

    def save_pdf_compressed(self, file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            print("Saving compressed PDF to:", file_path)  # Debugging statement
            pdf_writer = fitz.open()  # Create a new PDF writer object

            # Iterate over each document and insert pages into the PDF writer
            for doc_name, details in sorted(self.doc_details.items(), key=lambda x: x[1]["start_page"]):
                doc = fitz.open(doc_name)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pdf_writer.insert_pdf(doc, from_page=page_num, to_page=page_num)  # Insert page into writer
                doc.close()

            pdf_writer.save(file_path, deflate=True)  # Use deflate option for compression
            pdf_writer.close()

            QMessageBox.information(self, "Success", "PDF saved successfully.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "File not found.")
        except PermissionError:
            QMessageBox.critical(self, "Error", "Permission denied. Cannot save PDF to this location.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving compressed PDF: {e}")
            print(traceback.format_exc())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PDFViewer()
    window.show()
    sys.exit(app.exec())
