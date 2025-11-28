# ui/box_item.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QInputDialog
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont

class HandleItem(QGraphicsRectItem):
    """Small square handle for resizing"""
    def __init__(self, cursor_shape, parent):
        # 8x8 pixel handle, centered relative to its pos
        super().__init__(-4, -4, 8, 8, parent)
        self.setCursor(cursor_shape)
        self.setBrush(QBrush(QColor("yellow")))
        self.setPen(QPen(QColor("black"), 1))
        
        # CRITICAL: High Z-Value ensures it floats on top of the box and text
        self.setZValue(999) 
        self.setAcceptHoverEvents(True) 

    def mousePressEvent(self, event):
        # Trigger parent resize
        self.parentItem().start_resize(self, event.scenePos())

    def mouseMoveEvent(self, event):
        # Pass move event to parent
        self.parentItem().perform_resize(self, event.scenePos())

    def mouseReleaseEvent(self, event):
        self.parentItem().end_resize()

class BoxItem(QGraphicsRectItem):
    MIN_SIZE = 10.0 # Minimum width/height in pixels

    def __init__(self, x, y, w, h, text, parent=None):
        # Initialize the rect at the specific coordinates
        super().__init__(x, y, w, h, parent)
        
        # 1. Visual Setup
        self.default_pen = QPen(QColor("#00FF00"), 2)
        self.selected_pen = QPen(QColor("#FF0000"), 3)
        self.setPen(self.default_pen)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        # 2. Text Label
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(QColor("yellow"))
        font = QFont("Arial", 12)
        font.setBold(True)
        self.text_item.setFont(font)
        self.text_item.setZValue(1) 

        # 3. Resize Handles
        self.handles = {}
        self.create_handles()
        
        # 4. State Management
        self.resizing = False
        self.current_handle = None
        self.current_mode = "VIEW" 
        
        # CRITICAL FIX: Ensure handles are positioned correctly immediately
        self.update_handles_pos()
        self.update_text_pos()

    def create_handles(self):
        # Top-Left, Top-Right, Bottom-Left, Bottom-Right
        self.handles['tl'] = HandleItem(Qt.CursorShape.SizeFDiagCursor, self)
        self.handles['tr'] = HandleItem(Qt.CursorShape.SizeBDiagCursor, self)
        self.handles['bl'] = HandleItem(Qt.CursorShape.SizeBDiagCursor, self)
        self.handles['br'] = HandleItem(Qt.CursorShape.SizeFDiagCursor, self)
        self.set_handles_visible(False)

    def update_handles_pos(self):
        """Moves handles to the current corners of the rect"""
        r = self.rect()
        self.handles['tl'].setPos(r.topLeft())
        self.handles['tr'].setPos(r.topRight())
        self.handles['bl'].setPos(r.bottomLeft())
        self.handles['br'].setPos(r.bottomRight())

    def update_text_pos(self):
        r = self.rect()
        self.text_item.setPos(r.left(), r.top() - 25)

    def set_handles_visible(self, visible):
        for h in self.handles.values():
            h.setVisible(visible)

    def set_mode(self, mode):
        self.current_mode = mode
        
        if mode == 'MOVE':
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.set_handles_visible(False)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            
        elif mode == 'RESIZE':
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.set_handles_visible(True) # Force show handles
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Ensure handles are in the right place when switching modes
            self.update_handles_pos() 
            
        elif mode == 'TEXT':
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.set_handles_visible(False)
            self.setCursor(Qt.CursorShape.IBeamCursor)
            
        else: # VIEW
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.set_handles_visible(False)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def paint(self, painter, option, widget):
        # Custom paint to handle selection color
        if self.isSelected():
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.default_pen)
        super().paint(painter, option, widget)

    def mouseDoubleClickEvent(self, event):
        if self.current_mode == 'TEXT':
            old_text = self.text_item.toPlainText()
            new_text, ok = QInputDialog.getText(None, "Edit Text", "Value:", text=old_text)
            if ok:
                self.text_item.setPlainText(new_text)
        else:
            super().mouseDoubleClickEvent(event)

    # --- Resizing Logic ---
    
    def start_resize(self, handle, mouse_pos):
        self.resizing = True
        self.current_handle = handle

    def perform_resize(self, handle, mouse_pos):
        if not self.resizing: return
        
        # Convert mouse scene position to local item position
        local_pos = self.mapFromScene(mouse_pos)
        x, y = local_pos.x(), local_pos.y()
        
        r = self.rect()
        left, top, right, bottom = r.left(), r.top(), r.right(), r.bottom()
        
        # Modify specific coordinate based on handle
        if handle == self.handles['tl']:
            left, top = x, y
        elif handle == self.handles['tr']:
            right, top = x, y
        elif handle == self.handles['bl']:
            left, bottom = x, y
        elif handle == self.handles['br']:
            right, bottom = x, y
            
        # --- FIX: Prevent Zero Size / Negative Size ---
        # Ensure Left is always smaller than Right by MIN_SIZE
        if left > right - self.MIN_SIZE:
            if handle in [self.handles['tl'], self.handles['bl']]:
                left = right - self.MIN_SIZE
            else:
                right = left + self.MIN_SIZE
                
        # Ensure Top is always smaller than Bottom by MIN_SIZE
        if top > bottom - self.MIN_SIZE:
            if handle in [self.handles['tl'], self.handles['tr']]:
                top = bottom - self.MIN_SIZE
            else:
                bottom = top + self.MIN_SIZE

        # Update Rect
        self.setRect(QRectF(left, top, right - left, bottom - top))
        
        # Important: Update visuals
        self.update_handles_pos()
        self.update_text_pos()

    def end_resize(self):
        self.resizing = False
        self.current_handle = None