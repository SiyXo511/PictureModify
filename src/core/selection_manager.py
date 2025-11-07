"""
选择区域管理模块
"""
from typing import Optional, Tuple


class SelectionManager:
    """选择区域管理器"""
    
    def __init__(self):
        """初始化选择管理器"""
        self.selection_rect = None  # (x1, y1, x2, y2)
        self.is_selecting = False
        self.start_point = None
    
    def start_selection(self, x, y):
        """
        开始选择
        
        Args:
            x, y: 起始点坐标
        """
        self.is_selecting = True
        self.start_point = (x, y)
        self.selection_rect = None
    
    def update_selection(self, x, y):
        """
        更新选择区域
        
        Args:
            x, y: 当前点坐标
        """
        if self.is_selecting and self.start_point:
            x1, y1 = self.start_point
            # 确保坐标顺序正确
            self.selection_rect = (
                min(x1, x),
                min(y1, y),
                max(x1, x),
                max(y1, y)
            )
    
    def end_selection(self, x, y):
        """
        结束选择
        
        Args:
            x, y: 结束点坐标
        """
        if self.is_selecting:
            self.update_selection(x, y)
            self.is_selecting = False
    
    def get_selection(self) -> Optional[Tuple[int, int, int, int]]:
        """
        获取选择区域
        
        Returns:
            (x1, y1, x2, y2) 或 None
        """
        return self.selection_rect
    
    def clear_selection(self):
        """清除选择"""
        self.selection_rect = None
        self.is_selecting = False
        self.start_point = None
    
    def has_selection(self) -> bool:
        """检查是否有选择区域"""
        if self.selection_rect is None:
            return False
        x1, y1, x2, y2 = self.selection_rect
        # 检查选择区域是否有效（宽度和高度都大于0）
        return abs(x2 - x1) > 5 and abs(y2 - y1) > 5
    
    def get_selection_size(self) -> Tuple[int, int]:
        """
        获取选择区域尺寸
        
        Returns:
            (width, height)
        """
        if not self.has_selection():
            return (0, 0)
        x1, y1, x2, y2 = self.selection_rect
        return (abs(x2 - x1), abs(y2 - y1))
    
    def normalize_selection(self, image_width, image_height):
        """
        规范化选择区域到图片坐标范围内
        
        Args:
            image_width: 图片宽度
            image_height: 图片高度
        """
        if not self.selection_rect:
            return
        
        x1, y1, x2, y2 = self.selection_rect
        x1 = max(0, min(x1, image_width))
        y1 = max(0, min(y1, image_height))
        x2 = max(0, min(x2, image_width))
        y2 = max(0, min(y2, image_height))
        
        self.selection_rect = (x1, y1, x2, y2)

