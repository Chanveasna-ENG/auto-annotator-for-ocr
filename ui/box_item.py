# ui/box_item.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QInputDialog, QGraphicsSceneMouseEvent
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont

class HandleItem(QGraphicsRectItem):
    """Small square handle for resizing"""
    def __init__(self, cursor_shape, parent):
        super().__init__(-3, -3, 6, 6, parent)
        self.setCursor(cursor_shape)
        self.setBrush(QBrush(QColor("yellow")))
        self.setPen(QPen(QColor("black"), 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
    def mousePressEvent(self, event):
        # Pass event to parent to start resize
        self.parentItem().start_resize(self, event.scenePos())

    def mouseMoveEvent(self, event):
        # Pass move event to parent
        self.parentItem().perform_resize(self, event.scenePos())

class BoxItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h, text, parent=None):
        super().__init__(x, y, w, h, parent)
        
        # 1. Visuals
        self.default_pen = QPen(QColor("#00FF00"), 2)
        self.selected_pen = QPen(QColor("#FF0000"), 3)
        self.setPen(self.default_pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False) # Default locked
        self.setAcceptHoverEvents(True)

        # 2. Text Label
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(QColor("yellow"))
        font = QFont("Arial", 10)
        font.setBold(True)
        self.text_item.setFont(font)
        self.update_text_pos()

        # 3. Resize Handles (Hidden by default)
        self.handles = {}
        self.create_handles()
        self.resizing = False
        self.current_handle = None
        self.start_rect = None
        self.start_mouse_pos = None

    def create_handles(self):
        # Create 4 corner handles
        self.handles['tl'] = HandleItem(Qt.CursorShape.SizeFDiagCursor, self) # Top-Left
        self.handles['tr'] = HandleItem(Qt.CursorShape.SizeBDiagCursor, self) # Top-Right
        self.handles['bl'] = HandleItem(Qt.CursorShape.SizeBDiagCursor, self) # Bottom-Left
        self.handles['br'] = HandleItem(Qt.CursorShape.SizeFDiagCursor, self) # Bottom-Right
        self.set_handles_visible(False)

    def update_handles_pos(self):
        r = self.rect()
        self.handles['tl'].setPos(r.left(), r.top())
        self.handles['tr'].setPos(r.right(), r.top())
        self.handles['bl'].setPos(r.left(), r.bottom())
        self.handles['br'].setPos(r.right(), r.bottom())
        self.update_text_pos()

    def update_text_pos(self):
        # Place text above the box
        r = self.rect()
        self.text_item.setPos(r.left(), r.top() - 20)

    def set_handles_visible(self, visible):
        for h in self.handles.values():
            h.setVisible(visible)

    def set_mode(self, mode):
        """
        VIEW: No interaction
        MOVE: Movable, No handles
        EDIT: Static position, Handles visible
        """
        if mode == 'MOVE':
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.set_handles_visible(False)
        elif mode == 'EDIT':
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.set_handles_visible(True)
        else: # VIEW
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.set_handles_visible(False)

    # --- Interaction Events ---

    def paint(self, painter, option, widget):
        if self.isSelected():
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.default_pen)
        super().paint(painter, option, widget)

    def mouseDoubleClickEvent(self, event):
        # Edit Text
        old_text = self.text_item.toPlainText()
        new_text, ok = QInputDialog.getText(None, "Edit Text", "Value:", text=old_text)
        if ok:
            self.text_item.setPlainText(new_text)

    # --- Resizing Logic ---
    
    def start_resize(self, handle, mouse_pos):
        self.resizing = True
        self.current_handle = handle
        self.start_rect = self.rect()
        self.start_mouse_pos = mouse_pos

    def perform_resize(self, handle, mouse_pos):
        if not self.resizing: return

        r = self.rect()
        # Calculate delta inside the scene
        # Note: This is a simplified logic. 
        # For precise robust resizing, we usually calculate delta from start_mouse_pos
        
        # Simple Logic: Move the specific corner to mouse pos
        # We need to map the mouse pos (which is in scene coords) to item local coords
        local_pos = self.mapFromScene(mouse_pos)
        x, y = local_pos.x(), local_pos.y()
        
        new_rect = QRectF(r)
        
        if handle == self.handles['tl']:
            new_rect.setTopLeft(local_pos)
        elif handle == self.handles['br']:
            new_rect.setBottomRight(local_pos)
        elif handle == self.handles['tr']:
            new_rect.setTopRight(local_pos)
        elif handle == self.handles['bl']:
            new_rect.setBottomLeft(local_pos)
            
        # Normalize (prevent negative width/height)
        self.setRect(new_rect.normalized())
        self.update_handles_pos()