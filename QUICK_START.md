# 快速开始指南

## 第一步：理解需求

你已经有了三个核心功能需求：
1. **垂直删除拼接** - 删除垂直选中的区域并拼接剩余部分
2. **智能背景填充** - 删除选中区域并用背景填充
3. **文字识别、删除与替换** - 识别图片中的文字，删除原文字并用相同字体替换为新文字

## 第二步：选择开发方式

### 方式A：使用AI生成（推荐新手）

1. 打开 `PROJECT_GENERATION_PROMPT.md` 文件
2. 复制全部内容
3. 在Cursor、ChatGPT、Claude等AI助手中粘贴
4. AI会生成完整的项目代码
5. 按照生成的代码进行测试和调整

### 方式B：手动开发

1. 阅读 `PROJECT_REQUIREMENTS.md` 了解详细需求
2. 按照项目结构创建文件
3. 逐步实现各个功能模块

## 第三步：环境准备

```bash
# 安装Python依赖
pip install -r requirements.txt
```

## 第四步：项目结构

创建以下目录结构：
```
PictureModify/
├── src/
│   ├── main.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   └── image_canvas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── image_processor.py
│   │   ├── selection_manager.py
│   │   ├── ocr_processor.py
│   │   └── text_editor.py
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py
│       └── history_manager.py
├── requirements.txt
└── README.md
```

## 第五步：核心功能实现要点

### 1. 垂直删除拼接
```python
# 伪代码示例
def vertical_delete_and_stitch(image, y1, y2):
    # y1, y2 是选中区域的上下边界
    top_part = image.crop((0, 0, width, y1))
    bottom_part = image.crop((0, y2, width, height))
    # 垂直拼接
    new_image = Image.new('RGB', (width, y1 + (height - y2)))
    new_image.paste(top_part, (0, 0))
    new_image.paste(bottom_part, (0, y1))
    return new_image
```

### 2. 智能填充
```python
# 使用OpenCV的inpaint算法
import cv2
import numpy as np

def smart_fill(image, mask):
    # mask是选中区域的掩码
    result = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
    return result
```

### 3. 文字识别（OCR）
```python
# 使用PaddleOCR识别文字
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 支持中英文

def recognize_text(image_region):
    result = ocr.ocr(image_region, cls=True)
    # 返回识别结果：文字内容、位置、置信度
    return result
```

### 4. 文字替换
```python
# 提取字体特征并替换文字
from PIL import ImageDraw, ImageFont

def replace_text(image, old_text_bbox, new_text, font_params):
    # 1. 提取字体特征（大小、颜色等）
    font_size = calculate_font_size(old_text_bbox)
    font_color = extract_text_color(image, old_text_bbox)
    
    # 2. 匹配字体
    font_path = match_font(font_params)
    font = ImageFont.truetype(font_path, font_size)
    
    # 3. 删除原文字（使用inpaint）
    image = delete_text(image, old_text_bbox)
    
    # 4. 渲染新文字
    draw = ImageDraw.Draw(image)
    x, y = calculate_text_position(old_text_bbox, new_text, font)
    draw.text((x, y), new_text, fill=font_color, font=font)
    
    return image
```

## 第六步：测试

1. 测试图片加载
2. 测试选择功能
3. 测试垂直删除拼接
4. 测试智能填充
5. 测试OCR文字识别（中文、英文、中英文混合）
6. 测试文字删除功能
7. 测试文字替换功能（字体匹配、颜色匹配）
8. 测试撤销/重做
9. 测试保存功能

## 第七步：打包成exe

```bash
# 使用PyInstaller打包
pyinstaller --onefile --windowed --name PictureModify src/main.py

# 或者使用提供的打包脚本
python build_exe.py
```

## 常见问题

### Q: 如何选择GUI框架？
A: 
- **PyQt5**：功能强大，界面美观，推荐使用
- **tkinter**：Python内置，无需安装，但功能相对简单

### Q: 智能填充效果不好怎么办？
A: 可以尝试：
- 调整inpaint算法的参数
- 使用不同的填充模式（平均颜色、中位数等）
- 预处理图片（降噪等）

### Q: 打包后的exe文件很大？
A: 
- 使用 `--exclude-module` 排除不需要的模块
- 使用虚拟环境只安装必要的包
- 考虑使用 `--onedir` 而不是 `--onefile`

### Q: 如何处理大图片？
A: 
- 使用多线程处理，避免界面卡顿
- 显示处理进度
- 考虑限制图片最大尺寸

### Q: PaddleOCR安装或使用有问题？
A: 
- 确保网络连接正常（首次使用需要下载模型）
- 如果PaddleOCR安装失败，可以使用EasyOCR作为备选
- 模型文件较大（约100MB），首次下载需要时间
- 可以在代码中添加错误处理和提示

### Q: 文字识别准确度不高？
A: 
- 确保图片清晰，文字区域明显
- 复杂背景可能影响识别效果
- 允许用户手动编辑识别结果
- 可以尝试不同的OCR库（EasyOCR、Tesseract）

### Q: 字体匹配不准确？
A: 
- 字体自动匹配是近似匹配，可能不完全准确
- 提供手动选择字体的选项
- 可以保存常用字体配置
- 对于特殊字体，可能需要用户手动指定

## 下一步

1. 阅读 `PROJECT_REQUIREMENTS.md` 了解详细需求
2. 使用 `PROJECT_GENERATION_PROMPT.md` 生成代码
3. 测试和优化
4. 打包发布

## 获取帮助

- 查看 `PROJECT_REQUIREMENTS.md` 了解详细需求
- 使用 `PROJECT_GENERATION_PROMPT.md` 向AI助手提问
- 参考PyQt5、OpenCV官方文档

