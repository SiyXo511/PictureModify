"""
OCR文字识别处理模块
"""
import numpy as np
from PIL import Image
from typing import List, Dict, Optional
import platform
import os


class OCRProcessor:
    """OCR处理器"""
    
    def __init__(self):
        """初始化OCR处理器"""
        self.ocr = None
        self._init_ocr()
    
    def _get_model_paths(self):
        """
        获取模型文件路径
        
        Returns:
            dict: 包含det_model_dir, rec_model_dir, cls_model_dir的字典，如果本地模型不存在则返回None
        """
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # 优先检查项目根目录下的.paddlex目录（用户手动放置的）
        paddlex_dir = os.path.join(project_root, '.paddlex')
        
        # 其次检查models/paddleocr目录（标准位置）
        models_dir = os.path.join(project_root, 'models', 'paddleocr')
        
        # 检查.paddlex目录中的模型
        if os.path.exists(paddlex_dir):
            # 在.paddlex目录中查找模型文件
            det_model_dir, rec_model_dir, cls_model_dir = self._find_models_in_dir(paddlex_dir)
            if det_model_dir and rec_model_dir:
                paths = {
                    'det_model_dir': det_model_dir,
                    'rec_model_dir': rec_model_dir
                }
                if cls_model_dir:
                    paths['cls_model_dir'] = cls_model_dir
                return paths
        
        # 检查models/paddleocr目录中的模型
        det_model_dir = os.path.join(models_dir, 'det')
        rec_model_dir = os.path.join(models_dir, 'rec')
        cls_model_dir = os.path.join(models_dir, 'cls')
        
        # 检查关键模型文件是否存在
        det_exists = (
            os.path.exists(det_model_dir) and 
            any(f.endswith('.pdiparams') for f in os.listdir(det_model_dir) if os.path.isfile(os.path.join(det_model_dir, f)))
        )
        rec_exists = (
            os.path.exists(rec_model_dir) and 
            any(f.endswith('.pdiparams') for f in os.listdir(rec_model_dir) if os.path.isfile(os.path.join(rec_model_dir, f)))
        )
        cls_exists = (
            os.path.exists(cls_model_dir) and 
            any(f.endswith('.pdiparams') for f in os.listdir(cls_model_dir) if os.path.isfile(os.path.join(cls_model_dir, f)))
        )
        
        if det_exists and rec_exists:
            paths = {
                'det_model_dir': det_model_dir,
                'rec_model_dir': rec_model_dir
            }
            if cls_exists:
                paths['cls_model_dir'] = cls_model_dir
            return paths
        return None
    
    def _find_models_in_dir(self, base_dir):
        """
        在指定目录中查找模型文件
        
        Args:
            base_dir: 基础目录路径
            
        Returns:
            (det_model_dir, rec_model_dir, cls_model_dir) 或 (None, None, None)
        """
        det_dir = None
        rec_dir = None
        cls_dir = None
        
        if not os.path.exists(base_dir):
            return (None, None, None)
        
        # 递归查找包含模型文件的目录
        for root, dirs, files in os.walk(base_dir):
            # 检查目录中是否包含模型文件
            has_model = any(f.endswith('.pdiparams') or f.endswith('.pdmodel') for f in files)
            if has_model:
                dir_name = os.path.basename(root).lower()
                parent_name = os.path.basename(os.path.dirname(root)).lower()
                
                # 根据目录名判断模型类型
                if 'det' in dir_name or 'detection' in dir_name or 'det' in parent_name:
                    if det_dir is None:
                        det_dir = root
                elif 'rec' in dir_name or 'recognition' in dir_name or 'rec' in parent_name:
                    if rec_dir is None:
                        rec_dir = root
                elif 'cls' in dir_name or 'classify' in dir_name or 'angle' in dir_name or 'cls' in parent_name:
                    if cls_dir is None:
                        cls_dir = root
                else:
                    # 如果无法从名称判断，检查父目录
                    if 'det' in parent_name and det_dir is None:
                        det_dir = root
                    elif 'rec' in parent_name and rec_dir is None:
                        rec_dir = root
                    elif 'cls' in parent_name and cls_dir is None:
                        cls_dir = root
        
        return (det_dir, rec_dir, cls_dir)
    
    def _init_ocr(self):
        """初始化OCR引擎"""
        try:
            from paddleocr import PaddleOCR
            
            # 首先尝试使用本地模型
            local_models = self._get_model_paths()
            
            if local_models:
                print("检测到本地模型文件，使用本地模型...")
                try:
                    # 使用本地模型路径初始化
                    init_params = {
                        'lang': 'ch',
                        'use_angle_cls': True,
                        **local_models
                    }
                    self.ocr = PaddleOCR(**init_params)
                    print("PaddleOCR初始化成功（使用本地模型）")
                    return
                except Exception as e:
                    print(f"使用本地模型失败: {e}，尝试使用在线模型...")
            
            # 如果本地模型不存在或失败，尝试使用项目根目录下的.paddlex
            # 检查项目根目录下的.paddlex目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            paddlex_dir = os.path.join(project_root, '.paddlex')
            
            if os.path.exists(paddlex_dir):
                print(f"检测到.paddlex目录: {paddlex_dir}")
                # 尝试从.paddlex目录中查找模型
                paddlex_models = self._find_models_in_dir(paddlex_dir)
                if paddlex_models[0] and paddlex_models[1]:  # det和rec都存在
                    print("在.paddlex目录中找到模型文件，尝试使用本地模型...")
                    try:
                        # 使用找到的模型路径
                        init_params = {
                            'lang': 'ch',
                            'use_angle_cls': True if paddlex_models[2] else False,
                            'det_model_dir': paddlex_models[0],
                            'rec_model_dir': paddlex_models[1]
                        }
                        if paddlex_models[2]:
                            init_params['cls_model_dir'] = paddlex_models[2]
                        
                        self.ocr = PaddleOCR(**init_params)
                        print("PaddleOCR初始化成功（使用.paddlex目录中的本地模型）")
                        return
                    except Exception as e:
                        print(f"从.paddlex目录加载模型失败: {e}")
                        print("尝试使用PaddleOCR默认行为（可能会下载模型）...")
            
            # 如果本地模型都不存在，提示用户并阻止下载
            print("=" * 60)
            print("警告: 未找到本地模型文件")
            print("为避免自动下载，程序将不会初始化OCR功能")
            print()
            print("请将模型文件放置在以下位置之一：")
            print(f"  1. {os.path.join(project_root, '.paddlex')}")
            print(f"  2. {os.path.join(project_root, 'models', 'paddleocr')}")
            print()
            print("模型目录结构示例：")
            print("  .paddlex/")
            print("    ├── det/  (检测模型)")
            print("    │   ├── inference.pdiparams")
            print("    │   └── inference.pdmodel")
            print("    ├── rec/  (识别模型)")
            print("    │   ├── inference.pdiparams")
            print("    │   └── inference.pdmodel")
            print("    └── cls/  (方向分类模型，可选)")
            print("        ├── inference.pdiparams")
            print("        └── inference.pdmodel")
            print("=" * 60)
            
            # 不尝试下载，直接返回None
            self.ocr = None
            return
            
        except ImportError:
            print("警告: PaddleOCR未安装，文字识别功能将不可用")
            print("请运行: pip install paddlepaddle paddleocr")
            self.ocr = None
        except Exception as e:
            print(f"OCR初始化失败: {e}")
            self.ocr = None
    
    def recognize_text(self, image_region: Image.Image) -> List[Dict]:
        """
        识别图片中的文字
        
        Args:
            image_region: PIL.Image对象，要识别的图片区域
            
        Returns:
            识别结果列表，每个结果包含:
            - text: 文字内容
            - bbox: 边界框坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            - confidence: 置信度
        """
        if self.ocr is None:
            return []
        
        if image_region is None:
            return []
        
        try:
            # 转换为numpy数组
            img_array = np.array(image_region)
            
            # 执行OCR识别
            result = self.ocr.ocr(img_array, cls=True)
            
            # 解析结果
            recognition_results = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        bbox, (text, confidence) = line
                        recognition_results.append({
                            'text': text,
                            'bbox': bbox,
                            'confidence': confidence
                        })
            
            return recognition_results
        except Exception as e:
            print(f"OCR识别失败: {e}")
            return []
    
    def get_system_fonts(self) -> List[str]:
        """
        获取系统可用字体列表
        
        Returns:
            字体名称列表
        """
        try:
            from PIL import ImageFont
            import os
            
            fonts = []
            system = platform.system()
            
            if system == 'Windows':
                # Windows字体路径
                font_dirs = [
                    os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
                ]
            elif system == 'Darwin':  # macOS
                font_dirs = [
                    '/System/Library/Fonts',
                    '/Library/Fonts',
                    os.path.expanduser('~/Library/Fonts'),
                ]
            else:  # Linux
                font_dirs = [
                    '/usr/share/fonts',
                    '/usr/local/share/fonts',
                    os.path.expanduser('~/.fonts'),
                ]
            
            # 支持的字体文件扩展名
            font_extensions = ['.ttf', '.otf', '.ttc']
            
            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for root, dirs, files in os.walk(font_dir):
                        for file in files:
                            if any(file.lower().endswith(ext) for ext in font_extensions):
                                font_path = os.path.join(root, file)
                                try:
                                    # 尝试加载字体以验证
                                    font = ImageFont.truetype(font_path, 12)
                                    font_name = os.path.splitext(file)[0]
                                    if font_name not in fonts:
                                        fonts.append(font_name)
                                except:
                                    pass
            
            # 添加一些常用字体（如果系统中有）
            common_fonts = [
                'SimHei', 'SimSun', 'Microsoft YaHei', 'KaiTi', 'FangSong',
                'Arial', 'Times New Roman', 'Courier New', 'Calibri'
            ]
            
            for font in common_fonts:
                if font not in fonts:
                    fonts.append(font)
            
            return sorted(fonts)
        except Exception as e:
            print(f"获取系统字体失败: {e}")
            # 返回默认字体列表
            return ['SimHei', 'SimSun', 'Arial', 'Times New Roman']
    
    def is_available(self) -> bool:
        """检查OCR是否可用"""
        return self.ocr is not None

