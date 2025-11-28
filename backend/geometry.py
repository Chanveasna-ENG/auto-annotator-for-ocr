# backend/geometry.py

def sort_boxes_into_lines(boxes):
    """
    Sorts bounding boxes into lines.
    Args:
        boxes (list): List of dicts or lists. 
                      If dict: {'bbox': [x1, y1, x2, y2], ...}
                      If list: [x1, y1, x2, y2]
    Returns:
        list: List of lines, where each line is a list of sorted boxes.
    """
    if not boxes:
        return []

    # Standardization helper
    def get_coords(b):
        if isinstance(b, dict): return b['bbox']
        return b

    def get_center_y(b):
        c = get_coords(b)
        return (c[1] + c[3]) / 2

    def get_center_x(b):
        c = get_coords(b)
        return (c[0] + c[2]) / 2

    def get_height(b):
        c = get_coords(b)
        return c[3] - c[1]

    # 1. Sort all boxes by Y-center (Top-to-Bottom)
    # Create a shallow copy to avoid modifying original list order if needed elsewhere
    sorted_boxes = sorted(boxes, key=get_center_y)

    lines = []
    current_line = [sorted_boxes[0]]

    for box in sorted_boxes[1:]:
        prev_box = current_line[-1]
        
        cy = get_center_y(box)
        prev_cy = get_center_y(prev_box)
        prev_h = get_height(prev_box)

        # Threshold: if vertical distance is < 50% of previous height, same line
        if abs(cy - prev_cy) < prev_h * 0.5:
            current_line.append(box)
        else:
            # Finish current line, sort by X (Left-to-Right)
            current_line.sort(key=get_center_x)
            lines.append(current_line)
            current_line = [box]

    # Append final line
    current_line.sort(key=get_center_x)
    lines.append(current_line)

    return lines