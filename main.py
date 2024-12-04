import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QProgressBar, 
                             QSplitter, QHeaderView, QComboBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
import piexif
import hashlib
import time

class ImageAnalyzerThread(QThread):
    update_progress = pyqtSignal(int)
    update_table = pyqtSignal(list)

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        total_files = len(self.file_paths)
        for i, file_path in enumerate(self.file_paths):
            self.analyze_image(file_path)
            self.update_progress.emit(int((i + 1) / total_files * 100))

    def analyze_image(self, file_path):
        try:
            with Image.open(file_path) as img:
                filename = os.path.basename(file_path)
                size = f"{img.width}x{img.height}"
                format = img.format
                mode = img.mode

                dpi = img.info.get('dpi', (72, 72))
                resolution = f"{dpi[0]}x{dpi[1]} dpi"

                color_depth = self.get_color_depth(mode)
                compression = img.info.get('compression', 'No info')
                file_size = os.path.getsize(file_path)
                file_size_mb = round(file_size / (1024 * 1024), 2)
                file_hash = self.get_file_hash(file_path)
                
                creation_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(file_path)))
                modification_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))
                access_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getatime(file_path)))
                
                additional_info = self.get_additional_info(img, format)

                self.update_table.emit([filename, size, resolution, color_depth, str(compression), format, 
                                        additional_info, file_size_mb, file_hash, 
                                        creation_time, modification_time, access_time, file_path])
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    @staticmethod
    def get_color_depth(mode):
        mode_depths = {'1': "1 bit (B&W)", 'L': "8 bit (Grayscale)", 'RGB': "24 bit", 'RGBA': "32 bit"}
        return mode_depths.get(mode, "Unknown")

    @staticmethod
    def get_file_hash(file_path):
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    @staticmethod
    def get_additional_info(img, format):
        if format == 'JPEG':
            try:
                exif_dict = piexif.load(img.info["exif"])
                return f"EXIF data: {len(exif_dict['0th'])} fields"
            except:
                return "No EXIF data"
        elif format == 'GIF':
            return f"Palette colors: {len(img.getcolors())}"
        elif format == 'PNG':
            return f"Colors: {len(img.getcolors()) if img.getcolors() else 'More than 256'}"
        return ""

class ImageAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Analyzer")
        self.setGeometry(100, 100, 1400, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_themes()
        self.create_ui()
        self.set_theme("Hacker")
        self.file_paths = {}

    def create_ui(self):
        top_panel = QHBoxLayout()
        
        self.select_folder_button = QPushButton("Select Folder")
        self.select_folder_button.clicked.connect(self.select_folder)

        self.select_file_button = QPushButton("Select Files")
        self.select_file_button.clicked.connect(self.select_files)

        self.theme_selector = QComboBox()
        self.theme_selector.addItems(self.themes.keys())
        self.theme_selector.currentTextChanged.connect(self.set_theme)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #00ff00; }")

        top_panel.addWidget(self.select_folder_button)
        top_panel.addWidget(self.select_file_button)
        top_panel.addWidget(self.theme_selector)
        top_panel.addWidget(self.progress_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Filename", "Dimensions", "Resolution", "Color Depth", "Compression", 
            "Format", "Additional Info", "File Size (MB)", "MD5 Hash", 
            "Creation Time", "Modification Time", "Last Access Time"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.show_image)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSortingEnabled(True)

        preview_panel = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        preview_panel.addWidget(self.image_label)
        preview_panel.addWidget(self.info_label)

        preview_widget = QWidget()
        preview_widget.setLayout(preview_panel)

        splitter.addWidget(self.table)
        splitter.addWidget(preview_widget)

        self.layout.addLayout(top_panel)
        self.layout.addWidget(splitter)

    def create_themes(self):
        self.themes = {
            "Hacker": {
                "bg": "#0a0a0a",
                "fg": "#00ff00",
                "accent": "#003300",
                "font": "Courier New",
                "font_size": "12px",
                "border": "2px solid #00ff00",
                "border_radius": "0px",
            },
            "Dark": {
                "bg": "#0b0b0b",
                "fg": "#eeeeee",
                "accent": "#8800ff",
                "font": "BahnSchrift SemiBold Condensed",
                "font_size": "16px",
                "border": "2px solid #eeeeee",
                "border_radius": "4px",
            },
            "Light": {
                "bg": "#ffffff",
                "fg": "#000000",
                "accent": "#ff8800",
                "font": "Comic Sans MS",
                "font_size": "14px",
                "border": "2px solid #000000",
                "border_radius": "6px",
            }
        }

    def set_theme(self, theme_name):
        theme = self.themes[theme_name]
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['bg']};
                color: {theme['fg']};
                font-family: {theme['font']};
                font-size: {theme['font_size']};
                border-radius: {theme['border_radius']};
                border: {theme.get('border', 'none')};
            }}
            QTableWidget {{
                gridline-color: {theme['fg']};
                border: 1px solid {theme['fg']};
            }}
            QTableWidget::item:selected {{
                background-color: {theme['accent']};
            }}
            QHeaderView::section {{
                background-color: {theme['bg']};
                color: {theme['fg']};
                border: 1px solid {theme['fg']};
            }}
            QPushButton {{
                background-color: {theme['bg']};
                color: {theme['fg']};
                border: 2px solid {theme['fg']};
                padding: 5px;
                border-radius: {theme['border_radius']};
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
            }}
        """)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.progress_bar.setVisible(True)
            self.table.setRowCount(0)
            self.file_paths.clear()
            self.thread = ImageAnalyzerThread([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.pcx'))])
            self.thread.update_progress.connect(self.update_progress)
            self.thread.update_table.connect(self.update_table)
            self.thread.finished.connect(lambda: self.progress_bar.setVisible(False))
            self.thread.start()

    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.pcx)")
        if file_paths:
            self.table.setRowCount(0)
            self.thread = ImageAnalyzerThread(file_paths)
            self.thread.update_progress.connect(self.update_progress)
            self.thread.update_table.connect(self.update_table)
            self.thread.finished.connect(lambda: self.progress_bar.setVisible(False))
            self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_table(self, data):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for i, value in enumerate(data[:-1]):
            self.table.setItem(row, i, QTableWidgetItem(str(value)))
        self.file_paths[row] = data[-1]

    def show_image(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            file_path = self.file_paths[selected_items[0].row()]
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    self.image_label.setText("Unable to load image")

                info = "File Analysis Report:\n\n"
                for i in range(12):
                    info += f"{self.table.horizontalHeaderItem(i).text()}: {self.table.item(selected_items[0].row(), i).text()}\n"
                self.info_label.setText(info)
            except Exception as e:
                print(f"Error displaying image: {e}")
                self.image_label.setText("Error displaying image")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageAnalyzer()
    window.show()
    sys.exit(app.exec())
