# ui/canvas.py
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QPen, QColor
from .box_item import BoxItem

class CanvasView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        # State
        self._panning = False
        self._pan_start = None
        
        # Drawing State
        self._drawing = False
        self._draw_start = None
        self._ghost_rect = None # The visual rectangle while dragging
        
        # Mode reference (needed to know if we should draw or pan)
        self.current_mode_ref = "VIEW" 

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            zoom_factor = 1.25
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1 / zoom_factor, 1 / zoom_factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        # 1. Pan (Middle Click)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # 2. Create Box (Ctrl + Left Click)
        if event.button() == Qt.MouseButton.LeftButton and (event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            # Check if we are clicking on an existing item (optional, but good practice)
            # If strictly creating, we ignore items under cursor
            self._drawing = True
            scene_pos = self.mapToScene(event.pos())
            self._draw_start = scene_pos
            
            # Create Ghost Rect
            self._ghost_rect = QGraphicsRectItem()
            self._ghost_rect.setPen(QPen(QColor("cyan"), 2, Qt.PenStyle.DashLine))
            self._ghost_rect.setRect(QRectF(scene_pos, scene_pos))
            self.scene.addItem(self._ghost_rect)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        # Pan Logic
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        # Draw Logic
        if self._drawing:
            scene_pos = self.mapToScene(event.pos())
            # Calculate rect
            top_left = self._draw_start
            width = scene_pos.x() - top_left.x()
            height = scene_pos.y() - top_left.y()
            
            # Normalize rect (handle dragging left/up)
            rect = QRectF(top_left.x(), top_left.y(), width, height).normalized()
            self._ghost_rect.setRect(rect)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        # End Pan
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        # End Draw
        if self._drawing and event.button() == Qt.MouseButton.LeftButton:
            self._drawing = False
            rect = self._ghost_rect.rect()
            
            self.scene.removeItem(self._ghost_rect)
            self._ghost_rect = None
            
            if rect.width() > 5 and rect.height() > 5:
                new_box = BoxItem(rect.x(), rect.y(), rect.width(), rect.height(), "New Text")
                
                # APPLY CURRENT MODE TO NEW BOX
                new_box.set_mode(self.current_mode_ref) 
                
                self.scene.addItem(new_box)
            
            event.accept()
            return

        super().mouseReleaseEvent(event)