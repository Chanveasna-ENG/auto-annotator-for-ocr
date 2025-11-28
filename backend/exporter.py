# backend/exporter.py
import os
import xml.etree.ElementTree as ET
from .geometry import sort_boxes_into_lines

def save_to_yolo(boxes, image_width, image_height, output_path):
    """
    Saves annotations to YOLO .txt format.
    boxes: List of dicts {'bbox': [x1, y1, x2, y2], 'text': str}
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for box_data in boxes:
            x1, y1, x2, y2 = box_data['bbox']
            
            # Normalize to YOLO format (class x_center y_center w h)
            # Assuming class is always 0 for text
            w = x2 - x1
            h = y2 - y1
            x_center = x1 + (w / 2)
            y_center = y1 + (h / 2)

            x_norm = x_center / image_width
            y_norm = y_center / image_height
            w_norm = w / image_width
            h_norm = h / image_height

            f.write(f"0 {x_norm:.6f} {y_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n")

def save_to_voc_xml(boxes, image_filename, image_size, output_path):
    """
    Saves annotations to PascalVOC XML format with Line grouping.
    boxes: List of dicts {'bbox': [x1, y1, x2, y2], 'text': str}
    """
    # 1. Re-sort boxes into lines based on current positions
    # (User might have moved them in UI)
    lines = sort_boxes_into_lines(boxes)
    
    root = ET.Element("metadata")
    ET.SubElement(root, "image").text = image_filename
    ET.SubElement(root, "width").text = str(image_size[0])
    ET.SubElement(root, "height").text = str(image_size[1])
    
    paragraph = ET.SubElement(root, "paragraph")
    
    for line_id, line_boxes in enumerate(lines, 1):
        line_elem = ET.SubElement(paragraph, "line", id=str(line_id))
        
        for box_data in line_boxes:
            word_elem = ET.SubElement(line_elem, "word")
            ET.SubElement(word_elem, "text").text = box_data.get('text', '')
            
            x1, y1, x2, y2 = box_data['bbox']
            bbox_elem = ET.SubElement(word_elem, "bbox")
            bbox_elem.set("x1", str(int(x1)))
            bbox_elem.set("y1", str(int(y1)))
            bbox_elem.set("x2", str(int(x2)))
            bbox_elem.set("y2", str(int(y2)))
            
    ET.indent(root, space="  ")
    xml_str = ET.tostring(root, encoding='utf-8', method='xml').decode()
    final_xml = f"<?xml version='1.0' encoding='utf-8'?>\n{xml_str}"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_xml)