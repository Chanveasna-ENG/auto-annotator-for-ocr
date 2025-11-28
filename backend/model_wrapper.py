# backend/model_wrapper.py
import torch
from torchvision import transforms
from PIL import Image
from ultralytics import YOLO  # Standard library
import sys
import os

# Add root to path so we can import MyCRNN if it's in the root
sys.path.append(os.getcwd())

from MyCRNN import CRNN # Expecting this file in root
from .config import ModelConfig, NUM_CLASSES, INT_TO_CHAR
from .image_ops import ResizeAndPad

class OCREngine:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.yolo_model = None
        self.crnn_model = None
        
        # Preprocessing for CRNN
        self.transform = transforms.Compose([
            ResizeAndPad(ModelConfig.IMG_HEIGHT, ModelConfig.IMG_WIDTH),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

    def load_yolo(self, path):
        """Loads standard YOLOv8 model"""
        try:
            print(f"Loading YOLO from {path}")
            self.yolo_model = YOLO(path)
            return True, "YOLO Loaded"
        except Exception as e:
            return False, str(e)

    def load_crnn(self, path):
        """Loads custom CRNN model"""
        try:
            print(f"Loading CRNN from {path}")
            self.crnn_model = CRNN(num_classes=NUM_CLASSES, input_height=ModelConfig.IMG_HEIGHT)
            self.crnn_model.to(self.device)
            
            checkpoint = torch.load(path, map_location=self.device)
            state_dict = checkpoint.get('model_state_dict', checkpoint.get('model', checkpoint))
            
            self.crnn_model.load_state_dict(state_dict)
            self.crnn_model.eval()
            return True, "CRNN Loaded"
        except Exception as e:
            return False, str(e)

    def decode_predictions(self, preds):
        """CTC Decoder logic"""
        preds = preds.argmax(dim=2).permute(1, 0)
        decoded_texts = []
        for pred in preds:
            collapsed = []
            for i, p in enumerate(pred):
                if p != 0 and (i == 0 or p != pred[i-1]):
                    collapsed.append(INT_TO_CHAR.get(p.item(), ''))
            decoded_texts.append("".join(collapsed))
        return decoded_texts

    def run(self, image_path):
        if not self.yolo_model or not self.crnn_model:
            raise ValueError("Models not loaded")

        # 1. Run YOLO
        results = self.yolo_model.predict(image_path, conf=0.25, iou=0.7)
        if not results:
            return []
            
        boxes = results[0].boxes.xyxy.cpu().numpy().tolist() # [[x1,y1,x2,y2], ...]
        if not boxes:
            return []

        # 2. Prepare CRNN Batch
        main_image = Image.open(image_path).convert("RGB")
        batch_tensors = []
        valid_boxes = []

        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            # Clip to image
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(main_image.width, x2), min(main_image.height, y2)
            
            if x2 <= x1 or y2 <= y1: continue # Skip invalid

            crop = main_image.crop((x1, y1, x2, y2))
            batch_tensors.append(self.transform(crop))
            valid_boxes.append([x1, y1, x2, y2])

        if not batch_tensors:
            return []

        # 3. Run CRNN
        batch = torch.stack(batch_tensors).to(self.device)
        with torch.no_grad():
            preds = self.crnn_model(batch)
        
        texts = self.decode_predictions(preds)

        # 4. Format Output
        output_data = []
        for i, text in enumerate(texts):
            output_data.append({
                'id': i,
                'bbox': valid_boxes[i], # [x1, y1, x2, y2]
                'text': text
            })
            
        return output_data