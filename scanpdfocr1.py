import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout,
                             QProgressBar, QLabel, QTabWidget, QComboBox)
from PyQt6.QtGui import QPixmap
from pdf2docx import Converter
from PIL import Image
import pytesseract

class PDFScannerConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Сканер и Конвертер PDF")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget(self)

        # Вкладка сканера
        self.scan_tab = QWidget()
        self.initScanTab()
        self.tabs.addTab(self.scan_tab, "Сканировать")

        # Вкладка конвертера
        self.convert_tab = QWidget()
        self.initConvertTab()
        self.tabs.addTab(self.convert_tab, "Конвертер PDF")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def initScanTab(self):
        layout = QVBoxLayout()

        self.scan_button = QPushButton("Сканировать и сохранить")
        self.scan_button.clicked.connect(self.scan_and_save)
        layout.addWidget(self.scan_button)

        self.save_path_label = QLabel("Путь сохранения: Не выбрано")
        layout.addWidget(self.save_path_label)

        self.save_path_button = QPushButton("Выбрать путь сохранения")
        self.save_path_button.clicked.connect(self.select_save_path)
        layout.addWidget(self.save_path_button)

        self.format_label = QLabel("Формат сохранения:")
        layout.addWidget(self.format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "DOCX"])
        layout.addWidget(self.format_combo)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.scan_tab.setLayout(layout)

    def initConvertTab(self):
        layout = QVBoxLayout()

        self.file_select_button = QPushButton("Выбрать PDF файл")
        self.file_select_button.clicked.connect(self.select_pdf_file)
        layout.addWidget(self.file_select_button)

        self.convert_button = QPushButton("Конвертировать в DOCX")
        self.convert_button.clicked.connect(self.convert_pdf_to_docx)
        layout.addWidget(self.convert_button)

        self.progress_bar_convert = QProgressBar()
        layout.addWidget(self.progress_bar_convert)

        self.convert_tab.setLayout(layout)

    def select_save_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать папку для сохранения")
        if folder:
            self.save_path_label.setText(f"Путь сохранения: {folder}")
            self.save_path = folder

    def scan_and_save(self):
        # Заглушка для сканирования
        self.progress_bar.setValue(50)
        format_selected = self.format_combo.currentText()
        save_path = self.save_path if hasattr(self, 'save_path') else os.getcwd()
        output_file = os.path.join(save_path, f"scan_result.{format_selected.lower()}")

        if format_selected == "PDF":
            image = Image.new('RGB', (200, 200), color='white')
            image.save(output_file, "PDF")
        elif format_selected == "DOCX":
            from docx import Document
            doc = Document()
            doc.add_paragraph("Распознанный текст")
            doc.save(output_file)

        self.progress_bar.setValue(100)

    def select_pdf_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать PDF файл", "", "PDF Files (*.pdf)")
        if file_path:
            self.selected_pdf = file_path

    def convert_pdf_to_docx(self):
        if hasattr(self, 'selected_pdf'):
            save_path, _ = QFileDialog.getSaveFileName(self, "Сохранить DOCX", "", "Word Document (*.docx)")
            if save_path:
                self.progress_bar_convert.setValue(50)
                cv = Converter(self.selected_pdf)
                cv.convert(save_path, start=0, end=None)
                cv.close()
                self.progress_bar_convert.setValue(100)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFScannerConverter()
    window.show()
    sys.exit(app.exec())
