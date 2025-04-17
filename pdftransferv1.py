import sys
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLabel, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap


class PDFFormatterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PDF Formatter")
        self.setGeometry(100, 100, 600, 400)

        self.label_input = QLabel("Выберите входной PDF")
        self.label_template = QLabel("Выберите PDF-шаблон")
        self.label_output = QLabel("Выберите путь для сохранения")

        self.btn_input = QPushButton("Выбрать входной PDF")
        self.btn_input.clicked.connect(self.select_input_pdf)

        self.btn_template = QPushButton("Выбрать PDF-шаблон")
        self.btn_template.clicked.connect(self.select_template_pdf)

        self.btn_output = QPushButton("Выбрать путь сохранения")
        self.btn_output.clicked.connect(self.select_output_pdf)

        self.btn_preview = QPushButton("Предпросмотр")
        self.btn_preview.clicked.connect(self.preview_pdf)

        self.btn_process = QPushButton("Применить формат")
        self.btn_process.clicked.connect(self.process_pdf)

        self.preview_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.preview_view.setScene(self.scene)

        layout = QVBoxLayout()
        layout.addWidget(self.label_input)
        layout.addWidget(self.btn_input)
        layout.addWidget(self.label_template)
        layout.addWidget(self.btn_template)
        layout.addWidget(self.label_output)
        layout.addWidget(self.btn_output)

        preview_layout = QHBoxLayout()
        preview_layout.addWidget(self.btn_preview)
        preview_layout.addWidget(self.preview_view)

        layout.addLayout(preview_layout)
        layout.addWidget(self.btn_process)

        self.setLayout(layout)

        self.input_pdf = None
        self.template_pdf = None
        self.output_pdf = None

    def select_input_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выбрать входной PDF", "", "PDF Files (*.pdf)")
        if file:
            self.input_pdf = file
            self.label_input.setText(f"Выбран: {file}")

    def select_template_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выбрать PDF-шаблон", "", "PDF Files (*.pdf)")
        if file:
            self.template_pdf = file
            self.label_template.setText(f"Выбран: {file}")

    def select_output_pdf(self):
        file, _ = QFileDialog.getSaveFileName(self, "Сохранить PDF как", "", "PDF Files (*.pdf)")
        if file:
            self.output_pdf = file
            self.label_output.setText(f"Сохранить как: {file}")

    def preview_pdf(self):
        if self.template_pdf:
            images = convert_pdf_to_images(self.template_pdf)
            if images:
                pixmap = QPixmap(images[0])
                self.scene.clear()
                self.scene.addPixmap(pixmap)
        else:
            self.label_output.setText("Выберите шаблон!")

    def process_pdf(self):
        if self.input_pdf and self.template_pdf and self.output_pdf:
            apply_format(self.input_pdf, self.output_pdf, self.template_pdf)
        else:
            self.label_output.setText("Выберите все файлы!")


def extract_format(template_pdf):
    """Извлекает шрифты, размеры текста, отступы и таблицы из шаблона PDF."""
    data = {"text": [], "tables": [], "fonts": {}}

    with pdfplumber.open(template_pdf) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            for word in words:
                data["text"].append({
                    "text": word["text"],
                    "x": word["x0"],
                    "y": page.height - word["top"],
                    "size": word["height"]
                })
            tables = page.extract_tables()
            if tables:
                data["tables"].append(tables)

    doc = fitz.open(template_pdf)
    for page in doc:
        for text in page.get_text("dict")["blocks"]:
            if "spans" in text:
                for span in text["spans"]:
                    font_name = span["font"]
                    font_size = span["size"]
                    data["fonts"][font_name] = font_size

    return data


def apply_format(input_pdf, output_pdf, template_pdf):
    """Применяет формат шаблона к новому PDF."""
    template_data = extract_format(template_pdf)
    doc = fitz.open(input_pdf)
    output = canvas.Canvas(output_pdf, pagesize=letter)

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]

    for page_num, page in enumerate(doc):
        if page_num < len(template_data["text"]):
            text_data = template_data["text"]
            for item in text_data:
                font_name = list(template_data["fonts"].keys())[0] if template_data["fonts"] else "Helvetica"
                font_size = template_data["fonts"].get(font_name, 12)
                output.setFont(font_name, font_size)
                output.drawString(item["x"], item["y"], item["text"])

        if page_num < len(template_data["tables"]):
            table_data = template_data["tables"]

            # Преобразование всех значений в Paragraph
            formatted_table = []
            for row in table_data[0]:  # Берем первую таблицу на странице
                formatted_table.append([Paragraph(str(cell), normal_style) for cell in row])

            table = Table(formatted_table, colWidths=100, rowHeights=20)
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 10)
            ]))
            table.wrapOn(output, 100, 600)
            table.drawOn(output, 100, 600)

        output.showPage()

    output.save()
    print(f"Файл сохранен: {output_pdf}")


def convert_pdf_to_images(pdf_path):
    """Конвертирует PDF в изображения для предпросмотра."""
    images = []
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_path = f"preview_page.png"
        img.save(img_path)
        images.append(img_path)
    return images


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFFormatterApp()
    window.show()
    sys.exit(app.exec())
