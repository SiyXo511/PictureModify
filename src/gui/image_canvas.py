"""
图片显示画布模块
"""
from typing import Tuple
from PyQt5.QtWidgets import QWidget, QScrollArea
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QPixmap, QImage, QColor, QCursor
from PIL import Image
import numpy as np


class ImageCanvas(QWidget):
    """图片显示画布"""
    
    # 信号
    selection_changed = pyqtSignal(object)  # 选择区域改变
    
    def __init__(self, parent=None):
        """初始化画布"""
        super().__init__(parent)
        self.image = None  # PIL.Image对象
        self.pixmap = None  # QPixmap对象
        self.scale_factor = 1.0  # 缩放因子
        self.selection_rect = None  # 选择区域 (x1, y1, x2, y2)
        self.is_selecting = False
        self.start_point = None
        self.is_panning = False  # 是否正在平移
        self.pan_start_pos = None  # 平移起始位置
        self.image_offset = QPoint(0, 0)  # 图片偏移
        
        # 设置背景
        self.setStyleSheet("background-color: #2b2b2b;")
        self.setMinimumSize(400, 300)
    
    def set_image(self, image: Image.Image, reset_view: bool = True):
        """
        设置图片
        
        Args:
            image: PIL.Image对象
            reset_view: 是否重置视图（缩放和平移）
        """
        if image is None:
            self.image = None
            self.pixmap = None
            self.update()
            return
        
        self.image = image.copy()
        self._update_pixmap()
        
        if reset_view:
            self.image_offset = QPoint(0, 0)
            self._fit_to_window()
        
        self.update()
    
    def update_image(self, image: Image.Image):
        """仅更新图片内容，不改变视图"""
        self.set_image(image, reset_view=False)
    
    def _update_pixmap(self):
        """更新QPixmap"""
        if self.image is None:
            return
        
        # 转换为QImage
        img_array = np.array(self.image)
        height, width, channel = img_array.shape
        bytes_per_line = 3 * width
        q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # 转换为QPixmap
        self.pixmap = QPixmap.fromImage(q_image)
    
    def _fit_to_window(self):
        """适应窗口大小"""
        if self.pixmap is None:
            return
        
        widget_size = self.size()
        pixmap_size = self.pixmap.size()
        
        scale_x = widget_size.width() / pixmap_size.width()
        scale_y = widget_size.height() / pixmap_size.height()
        self.scale_factor = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
        self.image_offset = QPoint(0, 0)  # 重置偏移
        
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.pixmap is None:
            painter.fillRect(self.rect(), QColor(43, 43, 43))
            return
        
        # 计算绘制位置（居中）
        scaled_size = self.pixmap.size() * self.scale_factor
        x = (self.width() - scaled_size.width()) // 2 + self.image_offset.x()
        y = (self.height() - scaled_size.height()) // 2 + self.image_offset.y()
        
        # 绘制图片
        painter.drawPixmap(x, y, scaled_size.width(), scaled_size.height(), self.pixmap)
        
        # 绘制选择框
        if self.selection_rect:
            x1, y1, x2, y2 = self.selection_rect
            # 转换到画布坐标
            canvas_x1 = x + x1 * self.scale_factor
            canvas_y1 = y + y1 * self.scale_factor
            canvas_x2 = x + x2 * self.scale_factor
            canvas_y2 = y + y2 * self.scale_factor
            
            # 绘制选择框
            pen = QPen(QColor(255, 0, 0), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(QRect(
                int(canvas_x1),
                int(canvas_y1),
                int(canvas_x2 - canvas_x1),
                int(canvas_y2 - canvas_y1)
            ))
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton and self.image is not None:
            # 转换到图片坐标
            img_x, img_y = self._canvas_to_image(event.pos())
            if img_x is not None and img_y is not None:
                self.is_selecting = True
                self.start_point = (img_x, img_y)
                self.selection_rect = None
                self.update()
        elif event.button() == Qt.RightButton and self.image is not None:
            self.is_panning = True
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting and self.start_point and self.image is not None:
            img_x, img_y = self._canvas_to_image(event.pos())
            if img_x is not None and img_y is not None:
                x1, y1 = self.start_point
                self.selection_rect = (
                    min(x1, img_x),
                    min(y1, img_y),
                    max(x1, img_x),
                    max(y1, img_y)
                )
                self.update()
                self.selection_changed.emit(self.selection_rect)
        elif self.is_panning:
            delta = event.pos() - self.pan_start_pos
            self.image_offset += delta
            self.pan_start_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            if self.selection_rect:
                self.selection_changed.emit(self.selection_rect)
        elif event.button() == Qt.RightButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
    
    def _canvas_to_image(self, canvas_pos):
        """
        将画布坐标转换为图片坐标
        
        Args:
            canvas_pos: QPoint画布坐标
            
        Returns:
            (x, y)图片坐标或(None, None)
        """
        if self.pixmap is None:
            return None, None
        
        # 计算图片在画布上的位置（居中）
        scaled_size = self.pixmap.size() * self.scale_factor
        x_offset = (self.width() - scaled_size.width()) // 2 + self.image_offset.x()
        y_offset = (self.height() - scaled_size.height()) // 2 + self.image_offset.y()
        
        # 转换坐标
        img_x = (canvas_pos.x() - x_offset) / self.scale_factor
        img_y = (canvas_pos.y() - y_offset) / self.scale_factor
        
        # 检查是否在图片范围内
        if 0 <= img_x < self.image.width and 0 <= img_y < self.image.height:
            return int(img_x), int(img_y)
        
        return None, None
    
    def get_selection(self):
        """获取选择区域"""
        return self.selection_rect
    
    def set_selection(self, rect: Tuple[int, int, int, int]):
        """
        设置选择区域
        
        Args:
            rect: (x1, y1, x2, y2) 形式的矩形，使用图片坐标
        """
        if self.image is None:
            return
        
        # 保证坐标顺序正确
        x1, y1, x2, y2 = rect
        self.selection_rect = (
            min(x1, x2),
            min(y1, y2),
            max(x1, x2),
            max(y1, y2)
        )
        self.update()
        self.selection_changed.emit(self.selection_rect)

    def clear_selection(self):
        """清除选择"""
        self.selection_rect = None
        self.is_selecting = False
        self.start_point = None
        self.update()
        self.selection_changed.emit(None)
    
    def wheelEvent(self, event):
        """鼠标滚轮事件（缩放）"""
        if self.pixmap is None:
            return
        
        # 获取缩放因子
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor *= 0.9
        
        # 限制缩放范围
        self.scale_factor = max(0.1, min(5.0, self.scale_factor))
        
        self.update()
    
    def fit_to_window(self):
        """适应窗口"""
        self._fit_to_window()
    
    def zoom_in(self):
        """放大"""
        if self.pixmap is not None:
            self.scale_factor *= 1.2
            self.scale_factor = min(5.0, self.scale_factor)
            self.update()
    
    def zoom_out(self):
        """缩小"""
        if self.pixmap is not None:
            self.scale_factor *= 0.8
            self.scale_factor = max(0.1, self.scale_factor)
            self.update()
    
    def reset_zoom(self):
        """重置缩放"""
        if self.pixmap is not None:
            self.scale_factor = 1.0
            self.image_offset = QPoint(0, 0)
            self.update()

