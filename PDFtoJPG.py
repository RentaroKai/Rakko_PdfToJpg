import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QProgressBar, QComboBox, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import fitz
from PIL import Image
import os

class ConversionThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, pdf_path, output_folder, quality, prefix, resolution):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_folder = output_folder
        self.quality = quality
        self.prefix = prefix
        self.resolution = resolution

    def run(self):
        try:
            pdf_document = fitz.open(self.pdf_path)
            total_pages = len(pdf_document)

            for page_num in range(total_pages):
                page = pdf_document.load_page(page_num)
                zoom = self.resolution  # 解像度を選択した倍率に設定
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                quality = {'低': 60, '中': 80, '高': 95, '超高': 100}[self.quality]
                output_file = os.path.join(self.output_folder, f"{self.prefix}page_{page_num + 1}.jpg")
                img.save(output_file, "JPEG", quality=quality)

                self.progress.emit(int((page_num + 1) / total_pages * 100))

            pdf_document.close()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class PDFtoJPGConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF to JPG Converter')
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # PDF file selection
        self.pdf_button = QPushButton('Select PDF')
        self.pdf_button.clicked.connect(self.select_pdf)
        self.pdf_label = QLabel('No file selected')
        layout.addWidget(self.pdf_button)
        layout.addWidget(self.pdf_label)

        # Output folder selection
        self.output_button = QPushButton('Select Output Folder')
        self.output_button.clicked.connect(self.select_output_folder)
        self.output_label = QLabel('No folder selected')
        layout.addWidget(self.output_button)
        layout.addWidget(self.output_label)

        # Quality setting
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel('Quality:'))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['低', '中', '高', '超高'])
        quality_layout.addWidget(self.quality_combo)
        layout.addLayout(quality_layout)

        # Resolution setting
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel('Resolution:'))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['1x', '2x', '3x', '4x'])
        resolution_layout.addWidget(self.resolution_combo)
        layout.addLayout(resolution_layout)

        # Prefix setting
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel('File prefix:'))
        self.prefix_input = QLineEdit()
        prefix_layout.addWidget(self.prefix_input)
        layout.addLayout(prefix_layout)

        # Convert button
        self.convert_button = QPushButton('Convert')
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        central_widget.setLayout(layout)

        self.pdf_path = None
        self.output_folder = None

    def select_pdf(self):
        file_dialog = QFileDialog()
        self.pdf_path, _ = file_dialog.getOpenFileName(self, 'Select PDF', '', 'PDF files (*.pdf)')
        if self.pdf_path:
            self.pdf_label.setText(os.path.basename(self.pdf_path))

    def select_output_folder(self):
        file_dialog = QFileDialog()
        self.output_folder = file_dialog.getExistingDirectory(self, 'Select Output Folder')
        if self.output_folder:
            self.output_label.setText(self.output_folder)

    def start_conversion(self):
        if not self.pdf_path or not self.output_folder:
            return

        resolution = int(self.resolution_combo.currentText()[0])  # '1x' -> 1, '2x' -> 2, etc.
        self.conversion_thread = ConversionThread(
            self.pdf_path,
            self.output_folder,
            self.quality_combo.currentText(),
            self.prefix_input.text(),
            resolution
        )
        self.conversion_thread.progress.connect(self.update_progress)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.error.connect(self.show_error)
        self.conversion_thread.start()

        self.convert_button.setEnabled(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def conversion_finished(self):
        self.progress_bar.setValue(100)
        self.convert_button.setEnabled(True)

    def show_error(self, error_message):
        # ここでエラーメッセージを表示するダイアログを実装できます
        print(f"Error: {error_message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    converter = PDFtoJPGConverter()
    converter.show()
    sys.exit(app.exec_())