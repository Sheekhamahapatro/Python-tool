import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QByteArray
import fitz  # PyMuPDF


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.viewer = QWidget()
        self.viewer_layout = QVBoxLayout()
        self.viewer.setLayout(self.viewer_layout)
        self.layout.addWidget(self.viewer)

        self.open_button = QPushButton("Open PDF")
        self.open_button.clicked.connect(self.open_pdf)
        self.layout.addWidget(self.open_button)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.document = None

    def open_pdf(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")

        if file_path:
            try:
                self.document = fitz.open(file_path)
                if self.document:
                    self.display_page(0)
            except Exception as e:
                print("Error:", e)

    def display_page(self, page_number):
        if self.document:
            try:
                page = self.document.load_page(page_number)
                pixmap = self.render_page(page)
                self.viewer_layout.addWidget(pixmap)
            except Exception as e:
                print("Error:", e)

    @staticmethod
    def render_page(page):
        try:
            pixmap = page.get_pixmap()
            image = QImage(pixmap.toImage())
            pixmap = QPixmap.fromImage(image)
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label
        except Exception as e:
            print("Error:", e)


def main():
    app = QApplication(sys.argv)
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
