"""
文件操作工具模块
"""
import os
from PIL import Image


class FileHandler:
    """文件处理类"""
    
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif']
    
    @staticmethod
    def open_image(file_path):
        """
        打开图片文件
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            PIL.Image对象，如果失败返回None
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            if not FileHandler.is_supported_format(file_path):
                raise ValueError(f"不支持的图片格式: {os.path.splitext(file_path)[1]}")
            
            image = Image.open(file_path)
            # 转换为RGB模式（处理RGBA等模式）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
        except Exception as e:
            print(f"打开图片失败: {e}")
            return None
    
    @staticmethod
    def save_image(image, file_path, quality=95):
        """
        保存图片文件
        
        Args:
            image: PIL.Image对象
            file_path: 保存路径
            quality: JPEG质量（1-100）
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            
            # 根据文件扩展名选择保存格式
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                image.save(file_path, 'JPEG', quality=quality)
            elif ext == '.png':
                image.save(file_path, 'PNG')
            elif ext == '.bmp':
                image.save(file_path, 'BMP')
            elif ext == '.gif':
                image.save(file_path, 'GIF')
            elif ext == '.webp':
                image.save(file_path, 'WEBP', quality=quality)
            else:
                # 默认保存为PNG
                if not ext:
                    file_path += '.png'
                image.save(file_path, 'PNG')
            
            return True
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False
    
    @staticmethod
    def is_supported_format(file_path):
        """
        检查文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in FileHandler.SUPPORTED_FORMATS
    
    @staticmethod
    def get_image_info(image):
        """
        获取图片信息
        
        Args:
            image: PIL.Image对象
            
        Returns:
            dict: 包含尺寸、模式等信息
        """
        if image is None:
            return {}
        
        return {
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'size': image.size,
            'format': getattr(image, 'format', 'Unknown')
        }

