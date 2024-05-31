from PyQt6.QtWidgets import QApplication, QFileDialog
import fitz  # PyMuPDF


def insert_image_into_pdf():
    app = QApplication([])

    # Browse for the input PDF file
    input_pdf_path, _ = QFileDialog.getOpenFileName(None, "Select Input PDF", "", "PDF files (*.pdf)")
    if not input_pdf_path:
        print("No input PDF selected. Exiting.")
        return

    # Browse for the image file
    image_path, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Image files (*.jpg *.jpeg *.png)")
    if not image_path:
        print("No image selected. Exiting.")
        return

    doc = fitz.open(input_pdf_path)

    # Check the number of pages in the document
    num_pages = doc.page_count
    print("Number of pages in the document:", num_pages)

    # If there are pages in the document, insert the image on the last page
    if num_pages > 0:
        # Define coordinates and dimensions of the rectangle
        x = 100
        y = 100
        width = 200
        height = 150

        pno = num_pages - 1  # Index of the last page (0-based)
        rect = (x, y, x + width, y + height)  # the rectangle showing the image

        page = doc[pno]  # load desired page in the PDF
        page.insert_image(rect, filename=image_path)

        output_pdf_path, _ = QFileDialog.getSaveFileName(None, "Save Output PDF", "", "PDF files (*.pdf)")
        if output_pdf_path:
            doc.save(output_pdf_path)  # save new version of the PDF
            print("Image inserted successfully.")
        else:
            print("No output PDF selected. Exiting.")
    else:
        print("The document does not have any pages.")

    doc.close()

    app.exec()


insert_image_into_pdf()
