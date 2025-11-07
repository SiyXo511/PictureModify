"""
文字编辑和替换模块
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple, Optional
import platform
import os


class TextEditor:
    """文字编辑器"""
    
    def __init__(self):
        """初始化文字编辑器"""
        self.font_cache = {}  # 字体缓存
    
    def extract_font_features(self, image: Image.Image, text_bbox: List[List[int]]) -> Dict:
        """
        提取文字区域的字体特征
        
        Args:
            image: PIL.Image对象
            text_bbox: 文字边界框 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            
        Returns:
            字体特征字典，包含:
            - font_size: 字体大小
            - font_color: 字体颜色 (R, G, B)
            - is_bold: 是否粗体
            - char_spacing: 字符间距
        """
        if image is None or not text_bbox:
            return self._get_default_features()
        
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 计算边界框的边界
        x_coords = [point[0] for point in text_bbox]
        y_coords = [point[1] for point in text_bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)
        
        # 确保坐标在图片范围内
        height, width = img_array.shape[:2]
        x1 = max(0, min(x1, width))
        y1 = max(0, min(y1, height))
        x2 = max(0, min(x2, width))
        y2 = max(0, min(y2, height))
        
        # 提取文字区域
        text_region = img_array[y1:y2, x1:x2]
        
        if text_region.size == 0:
            return self._get_default_features()
        
        # 1. 计算字体大小（基于高度）
        font_size = max(12, int((y2 - y1) * 0.8))
        
        # 2. 提取字体颜色
        # 使用K-means找到主要颜色（文字颜色通常是较暗的颜色）
        pixels = text_region.reshape(-1, 3)
        # 过滤掉接近白色的像素（可能是背景）
        dark_pixels = pixels[np.sum(pixels, axis=1) < 600]  # RGB总和小于600
        
        if len(dark_pixels) > 0:
            # 使用中位数作为文字颜色（更稳定）
            font_color = tuple(np.median(dark_pixels, axis=0).astype(int).tolist())
        else:
            # 如果找不到暗色像素，使用平均值
            font_color = tuple(np.mean(pixels, axis=0).astype(int).tolist())
        
        # 3. 判断是否粗体（通过边缘检测）
        gray = cv2.cvtColor(text_region, cv2.COLOR_RGB2GRAY) if len(text_region.shape) == 3 else text_region
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        is_bold = edge_density > 0.1  # 阈值可调整
        
        # 4. 计算字符间距（简化处理，使用边界框宽度）
        char_spacing = max(0, int((x2 - x1) * 0.05))
        
        return {
            'font_size': font_size,
            'font_color': font_color,
            'is_bold': is_bold,
            'char_spacing': char_spacing,
            'bbox': (x1, y1, x2, y2)
        }
    
    def _get_default_features(self) -> Dict:
        """获取默认字体特征"""
        return {
            'font_size': 24,
            'font_color': (0, 0, 0),
            'is_bold': False,
            'char_spacing': 2,
            'bbox': None
        }
    
    def match_font(self, font_features: Dict, text_content: str) -> Tuple[str, int]:
        """
        根据特征匹配字体
        
        Args:
            font_features: 字体特征字典
            text_content: 文字内容
            
        Returns:
            (字体路径, 字体大小)
        """
        # 检查是否包含中文
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text_content)
        
        system_fonts = self.get_system_fonts()
        if not system_fonts:
            system_fonts = ['SimHei', 'SimSun', 'Arial', 'Times New Roman']
        
        # 字体匹配逻辑
        font_name = None
        if has_chinese:
            # 中文字体优先
            preferred_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi']
            if font_features.get('is_bold', False):
                preferred_fonts = ['SimHei', 'Microsoft YaHei', 'KaiTi'] + preferred_fonts
        else:
            # 英文字体
            preferred_fonts = ['Arial', 'Times New Roman', 'Calibri', 'Courier New']
            if font_features.get('is_bold', False):
                preferred_fonts = ['Arial Bold', 'Times New Roman Bold'] + preferred_fonts
        
        # 尝试匹配字体
        for preferred in preferred_fonts:
            if preferred in system_fonts:
                font_name = preferred
                break
        
        # 如果没找到，使用第一个可用字体
        if font_name is None and system_fonts:
            font_name = system_fonts[0]

        if font_name is None:
            return (None, font_features.get('font_size', 24))

        # 获取字体路径
        font_path = self._get_font_path(font_name)
        
        font_size = font_features.get('font_size', 24)
        
        return (font_path, font_size)
    
    def _get_font_path(self, font_name: str) -> Optional[str]:
        """
        获取字体文件路径
        
        Args:
            font_name: 字体名称
            
        Returns:
            字体文件路径或None
        """
        if font_name in self.font_cache:
            return self.font_cache[font_name]
        
        system = platform.system()
        font_dirs = []
        
        if system == 'Windows':
            font_dirs = [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')]
        elif system == 'Darwin':
            font_dirs = ['/System/Library/Fonts', '/Library/Fonts']
        else:
            font_dirs = ['/usr/share/fonts', '/usr/local/share/fonts']
        
        # 搜索字体文件
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for root, dirs, files in os.walk(font_dir):
                    for file in files:
                        if font_name.lower() in file.lower() and file.lower().endswith(('.ttf', '.otf')):
                            font_path = os.path.join(root, file)
                            self.font_cache[font_name] = font_path
                            return font_path
        
        # 如果找不到，尝试使用PIL的默认字体
        try:
            from PIL import ImageFont
            # 尝试加载默认字体
            default_font = ImageFont.load_default()
            return None  # 使用默认字体
        except:
            return None
    
    def delete_text(self, image: Image.Image, text_bboxes: List[List[List[int]]]) -> Image.Image:
        """
        删除文字区域
        
        Args:
            image: PIL.Image对象
            text_bboxes: 文字边界框列表
            
        Returns:
            处理后的PIL.Image对象
        """
        if image is None or not text_bboxes:
            return image.copy() if image else None
        
        # 转换为numpy数组
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # 创建掩码
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # 为每个文字区域创建掩码
        for bbox in text_bboxes:
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x1, x2 = max(0, min(x_coords)), min(width, max(x_coords))
            y1, y2 = max(0, min(y_coords)), min(height, max(y_coords))
            
            if x1 < x2 and y1 < y2:
                # 扩展一点区域以确保完全覆盖
                padding = 2
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(width, x2 + padding)
                y2 = min(height, y2 + padding)
                mask[y1:y2, x1:x2] = 255
        
        # 使用inpaint算法填充
        result = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)
        
        return Image.fromarray(result)
    
    def replace_text(self, image: Image.Image, old_text_bbox: List[List[int]], 
                    new_text: str, font_params: Optional[Dict] = None) -> Image.Image:
        """
        替换文字
        
        Args:
            image: PIL.Image对象
            old_text_bbox: 原文字边界框
            new_text: 新文字内容
            font_params: 字体参数（可选），包含font_path, font_size, font_color等
            
        Returns:
            处理后的PIL.Image对象
        """
        if image is None or not new_text:
            return image.copy() if image else None
        
        # 先删除原文字
        image = self.delete_text(image, [old_text_bbox])
        
        # 计算文字位置
        x_coords = [point[0] for point in old_text_bbox]
        y_coords = [point[1] for point in old_text_bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)
        
        # 获取字体参数
        if font_params is None:
            font_features = self.extract_font_features(image, old_text_bbox)
            font_path, font_size = self.match_font(font_features, new_text)
            font_color = font_features.get('font_color', (0, 0, 0))
        else:
            font_path = font_params.get('font_path')
            font_size = font_params.get('font_size', 24)
            font_color = font_params.get('font_color', (0, 0, 0))
        
        # 加载字体
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 使用默认字体
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # 计算文字位置（居中）
        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), new_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算居中位置
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        text_x = center_x - text_width // 2
        text_y = center_y - text_height // 2
        
        # 绘制文字
        draw.text((text_x, text_y), new_text, fill=font_color, font=font)
        
        return image

    def add_text(self, image: Image.Image, target_bbox: List[List[int]],
                 new_text: str, font_params: Optional[Dict] = None,
                 font_features: Optional[Dict] = None) -> Image.Image:
        """在指定区域添加新文字"""
        if image is None or not new_text:
            return image.copy() if image else None

        font_features = font_features or self._get_default_features()
        font_params = font_params or {}

        x_coords = [point[0] for point in target_bbox]
        y_coords = [point[1] for point in target_bbox]
        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        font_size = font_params.get('font_size') or font_features.get('font_size', 24)
        font_color = font_params.get('font_color') or font_features.get('font_color', (0, 0, 0))

        font_path = font_params.get('font_path')
        font_name = font_params.get('font_name')

        if not font_path and font_name:
            font_path = self._get_font_path(font_name)

        if not font_path:
            matched_path, matched_size = self.match_font(font_features, new_text)
            font_path = matched_path
            if 'font_size' not in (font_params or {}):
                font_size = matched_size

        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        image_copy = image.copy()
        draw = ImageDraw.Draw(image_copy)
        bbox = draw.textbbox((0, 0), new_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        text_x = center_x - text_width // 2
        text_y = center_y - text_height // 2

        draw.text((text_x, text_y), new_text, fill=font_color, font=font)

        return image_copy

    def get_system_fonts(self) -> List[str]:
        """获取系统可用字体列表"""
        try:
            from PIL import ImageFont

            fonts = []
            system = platform.system()

            if system == 'Windows':
                font_dirs = [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')]
            elif system == 'Darwin':
                font_dirs = [
                    '/System/Library/Fonts',
                    '/Library/Fonts',
                    os.path.expanduser('~/Library/Fonts'),
                ]
            else:
                font_dirs = [
                    '/usr/share/fonts',
                    '/usr/local/share/fonts',
                    os.path.expanduser('~/.fonts'),
                ]

            font_extensions = ['.ttf', '.otf', '.ttc']

            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for root, _, files in os.walk(font_dir):
                        for file in files:
                            if any(file.lower().endswith(ext) for ext in font_extensions):
                                font_path = os.path.join(root, file)
                                try:
                                    ImageFont.truetype(font_path, 12)
                                    font_name = os.path.splitext(file)[0]
                                    if font_name not in fonts:
                                        fonts.append(font_name)
                                except:
                                    pass

            common_fonts = [
                'SimHei', 'SimSun', 'Microsoft YaHei', 'KaiTi', 'FangSong',
                'Arial', 'Times New Roman', 'Courier New', 'Calibri'
            ]

            for font in common_fonts:
                if font not in fonts:
                    fonts.append(font)

            return sorted(fonts)
        except Exception:
            return ['SimHei', 'SimSun', 'Arial', 'Times New Roman']

    def get_default_font_features(self) -> Dict:
        """获取默认字体特征"""
        return self._get_default_features()

