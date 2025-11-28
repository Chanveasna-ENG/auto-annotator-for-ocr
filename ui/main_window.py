# ui/main_window.py
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from .canvas import CanvasView
from .box_item import BoxItem
from backend.model_wrapper import OCREngine
from backend.exporter import save_to_voc_xml, save_to_yolo

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto-OCR Annotation Tool")
        self.resize(1200, 800)

        # Logic Engine
        self.engine = OCREngine()
        self.current_image_path = None
        self.current_mode = "VIEW" # VIEW, MOVE, EDIT

        self.setup_ui()
        
    def setup_ui(self):
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 10, 10, 10)
        
        self.btn_load_yolo = QPushButton("Load YOLO")
        self.btn_load_crnn = QPushButton("Load CRNN")
        self.btn_open_img = QPushButton("Open Image")
        self.btn_run_ocr = QPushButton("Run OCR")
        self.btn_save = QPushButton("Save")
        
        # Connect Buttons
        self.btn_load_yolo.clicked.connect(self.load_yolo)
        self.btn_load_crnn.clicked.connect(self.load_crnn)
        self.btn_open_img.clicked.connect(self.open_image)
        self.btn_run_ocr.clicked.connect(self.run_ocr)
        self.btn_save.clicked.connect(self.save_data)

        toolbar.addWidget(self.btn_load_yolo)
        toolbar.addWidget(self.btn_load_crnn)
        toolbar.addSpacing(20)
        toolbar.addWidget(self.btn_open_img)
        toolbar.addWidget(self.btn_run_ocr)
        toolbar.addSpacing(20)
        toolbar.addWidget(self.btn_save)
        toolbar.addStretch()

        # Mode Label
        self.lbl_mode = QLabel("Mode: VIEW (Press 'M' or 'E')")
        self.lbl_mode.setStyleSheet("color: #AAA; font-weight: bold;")
        toolbar.addWidget(self.lbl_mode)

        main_layout.addLayout(toolbar)

        # 2. Canvas
        self.canvas = CanvasView()
        main_layout.addWidget(self.canvas)

        # 3. Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready. Load models to begin.")

    # --- Key Events ---
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_M:
            self.set_mode("MOVE")
        elif event.key() == Qt.Key.Key_E:
            self.set_mode("EDIT")
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(event)

    def set_mode(self, mode):
        self.current_mode = mode
        self.lbl_mode.setText(f"Mode: {mode}")
        
        # Update all items in scene
        for item in self.canvas.scene.items():
            if isinstance(item, BoxItem):
                item.set_mode(mode)

    # --- Actions ---
    def load_yolo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select YOLO Model", "", "Model Files (*.pt *.onnx)")
        if path:
            success, msg = self.engine.load_yolo(path)
            self.status.showMessage(msg)

    def load_crnn(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CRNN Checkpoint", "", "Checkpoint Files (*.pth *.pt *.onnx)")
        if path:
            success, msg = self.engine.load_crnn(path)
            self.status.showMessage(msg)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.current_image_path = path
            self.canvas.scene.clear()
            pixmap = QPixmap(path)
            self.canvas.scene.addPixmap(pixmap)
            self.canvas.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
            self.status.showMessage(f"Loaded {os.path.basename(path)}")

    def run_ocr(self):
        if not self.current_image_path:
            return
        
        self.status.showMessage("Running OCR...")
        QApplication.processEvents() # Force UI update
        
        try:
            results = self.engine.run(self.current_image_path)
            
            # Clear existing boxes (keep image)
            # A simple way is to reload image, or filter items. Let's filter.
            for item in self.canvas.scene.items():
                if isinstance(item, BoxItem):
                    self.canvas.scene.removeItem(item)

            # Add new boxes
            for res in results:
                x1, y1, x2, y2 = res['bbox']
                box = BoxItem(x1, y1, x2-x1, y2-y1, res['text'])
                box.set_mode(self.current_mode)
                self.canvas.scene.addItem(box)
                
            self.status.showMessage(f"Found {len(results)} words.")
            
        except Exception as e:
            self.status.showMessage(f"Error: {str(e)}")
            print(e)

    def delete_selected(self):
        for item in self.canvas.scene.selectedItems():
            self.canvas.scene.removeItem(item)

    def save_data(self):
        if not self.current_image_path: return
        
        # Collect data from scene
        boxes = []
        for item in self.canvas.scene.items():
            if isinstance(item, BoxItem):
                r = item.rect()
                boxes.append({
                    'bbox': [r.x(), r.y(), r.x() + r.width(), r.y() + r.height()],
                    'text': item.text_item.toPlainText()
                })
        
        if not boxes:
            self.status.showMessage("No boxes to save.")
            return

        # Prepare paths
        base_name = os.path.basename(self.current_image_path)
        name_no_ext = os.path.splitext(base_name)[0]
        
        # Ensure directories
        os.makedirs("data/labels", exist_ok=True)
        os.makedirs("xml_labels", exist_ok=True)
        
        yolo_path = f"data/labels/{name_no_ext}.txt"
        xml_path = f"xml_labels/{name_no_ext}.xml"
        
        img_size = (int(self.canvas.scene.width()), int(self.canvas.scene.height()))
        
        # Save
        save_to_yolo(boxes, img_size[0], img_size[1], yolo_path)
        save_to_voc_xml(boxes, base_name, img_size, xml_path)
        
        self.status.showMessage(f"Saved to {yolo_path} and {xml_path}")

from PyQt6.QtWidgets import QApplication