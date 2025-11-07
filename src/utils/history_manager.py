"""
历史记录管理模块
"""
from PIL import Image
import copy


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, max_history=20):
        """
        初始化历史记录管理器
        
        Args:
            max_history: 最大历史记录数量
        """
        self.max_history = max_history
        self.history = []  # 历史记录列表
        self.current_index = -1  # 当前索引
    
    def save_state(self, image):
        """
        保存当前状态到历史记录
        
        Args:
            image: PIL.Image对象
        """
        # 如果当前不在历史记录末尾，删除后面的记录
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # 深拷贝图片
        image_copy = image.copy()
        self.history.append(image_copy)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.current_index += 1
    
    def undo(self):
        """
        撤销操作
        
        Returns:
            PIL.Image对象或None
        """
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index].copy()
        return None
    
    def redo(self):
        """
        重做操作
        
        Returns:
            PIL.Image对象或None
        """
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index].copy()
        return None
    
    def can_undo(self):
        """检查是否可以撤销"""
        return self.current_index > 0
    
    def can_redo(self):
        """检查是否可以重做"""
        return self.current_index < len(self.history) - 1
    
    def clear(self):
        """清空历史记录"""
        self.history.clear()
        self.current_index = -1
    
    def get_current_state(self):
        """
        获取当前状态
        
        Returns:
            PIL.Image对象或None
        """
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index].copy()
        return None
    
    def reset(self, image):
        """
        重置历史记录（用于加载新图片）
        
        Args:
            image: PIL.Image对象
        """
        self.clear()
        if image is not None:
            self.save_state(image)

