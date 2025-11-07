"""
图像处理核心模块
"""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional


class ImageProcessor:
    """图像处理器"""
    
    @staticmethod
    def vertical_delete_and_stitch(image: Image.Image, selection_rect: Tuple[int, int, int, int]) -> Image.Image:
        """
        垂直删除并拼接
        
        Args:
            image: PIL.Image对象
            selection_rect: 选择区域 (x1, y1, x2, y2)
            
        Returns:
            处理后的PIL.Image对象
        """
        if image is None:
            return None
        
        x1, y1, x2, y2 = selection_rect
        width, height = image.size
        
        # 确保坐标在图片范围内
        y1 = max(0, min(y1, height))
        y2 = max(0, min(y2, height))
        
        if y1 >= y2:
            return image.copy()
        
        # 提取上部（y < y1）
        if y1 > 0:
            top_part = image.crop((0, 0, width, y1))
        else:
            top_part = None
        
        # 提取下部（y >= y2）
        if y2 < height:
            bottom_part = image.crop((0, y2, width, height))
        else:
            bottom_part = None
        
        # 计算新图片高度
        new_height = (y1 if top_part else 0) + (height - y2 if bottom_part else 0)
        
        if new_height <= 0:
            return image.copy()
        
        # 创建新图片
        new_image = Image.new('RGB', (width, new_height), color=(255, 255, 255))
        
        # 拼接图片
        current_y = 0
        if top_part:
            new_image.paste(top_part, (0, current_y))
            current_y += top_part.height
        if bottom_part:
            new_image.paste(bottom_part, (0, current_y))
        
        return new_image
    
    @staticmethod
    def smart_fill(image: Image.Image, selection_rect: Tuple[int, int, int, int], 
                   fill_mode: str = 'inpaint', fill_color: Optional[Tuple[int, int, int]] = None) -> Image.Image:
        """
        智能填充选中区域
        
        Args:
            image: PIL.Image对象
            selection_rect: 选择区域 (x1, y1, x2, y2)
            fill_mode: 填充模式 ('inpaint', 'average', 'color', 'median')
            fill_color: 填充颜色（RGB），仅在fill_mode='color'时使用
            
        Returns:
            处理后的PIL.Image对象
        """
        if image is None:
            return None
        
        x1, y1, x2, y2 = selection_rect
        width, height = image.size
        
        # 确保坐标在图片范围内
        x1 = max(0, min(x1, width))
        y1 = max(0, min(y1, height))
        x2 = max(0, min(x2, width))
        y2 = max(0, min(y2, height))
        
        if x1 >= x2 or y1 >= y2:
            return image.copy()
        
        # 转换为numpy数组
        img_array = np.array(image)
        
        if fill_mode == 'inpaint':
            # 使用OpenCV的inpaint算法
            mask = np.zeros((height, width), dtype=np.uint8)
            mask[y1:y2, x1:x2] = 255
            
            # 使用TELEA算法
            result = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)
            return Image.fromarray(result)
        
        elif fill_mode == 'average':
            # 平均颜色填充
            # 获取周围像素
            border_pixels = []
            
            # 上边界
            if y1 > 0:
                border_pixels.extend(img_array[y1-1, x1:x2].tolist())
            # 下边界
            if y2 < height:
                border_pixels.extend(img_array[y2, x1:x2].tolist())
            # 左边界
            if x1 > 0:
                border_pixels.extend(img_array[y1:y2, x1-1].tolist())
            # 右边界
            if x2 < width:
                border_pixels.extend(img_array[y1:y2, x2].tolist())
            
            if border_pixels:
                avg_color = np.mean(border_pixels, axis=0).astype(np.uint8)
                img_array[y1:y2, x1:x2] = avg_color
            
            return Image.fromarray(img_array)
        
        elif fill_mode == 'color':
            # 纯色填充
            if fill_color is None:
                fill_color = (255, 255, 255)  # 默认白色
            
            img_array[y1:y2, x1:x2] = fill_color
            return Image.fromarray(img_array)
        
        elif fill_mode == 'median':
            # 中位数填充
            border_pixels = []
            
            # 获取周围像素
            if y1 > 0:
                border_pixels.extend(img_array[y1-1, x1:x2].tolist())
            if y2 < height:
                border_pixels.extend(img_array[y2, x1:x2].tolist())
            if x1 > 0:
                border_pixels.extend(img_array[y1:y2, x1-1].tolist())
            if x2 < width:
                border_pixels.extend(img_array[y1:y2, x2].tolist())
            
            if border_pixels:
                median_color = np.median(border_pixels, axis=0).astype(np.uint8)
                img_array[y1:y2, x1:x2] = median_color
            
            return Image.fromarray(img_array)
        
        else:
            return image.copy()

