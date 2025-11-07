"""
主窗口模块
"""
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMenuBar, QToolBar, QStatusBar, QAction, QFileDialog,
                             QMessageBox, QDialog, QLabel, QPushButton, QComboBox,
                             QSpinBox, QColorDialog, QCheckBox, QLineEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QDialogButtonBox, QProgressDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QKeySequence, QColor

from src.gui.image_canvas import ImageCanvas
from src.utils.file_handler import FileHandler
from src.utils.history_manager import HistoryManager
from src.core.selection_manager import SelectionManager
from src.core.image_processor import ImageProcessor
from src.core.ocr_processor import OCRProcessor
from src.core.text_editor import TextEditor
from PIL import Image


class OCRThread(QThread):
    """OCR识别线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, image_region):
        super().__init__()
        self.image_region = image_region
    
    def run(self):
        try:
            ocr_processor = OCRProcessor()
            if not ocr_processor.is_available():
                self.error.emit("OCR未初始化，请检查PaddleOCR是否安装")
                return
            
            results = ocr_processor.recognize_text(self.image_region)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(f"OCR识别失败: {str(e)}")


class TextRecognitionDialog(QDialog):
    """文字识别结果对话框"""
    def __init__(self, recognition_results, parent=None):
        super().__init__(parent)
        self.recognition_results = recognition_results
        self.selected_indices = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("文字识别结果")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # 表格显示识别结果
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["选择", "文字内容", "位置", "置信度"])
        self.table.horizontalHeader().setStretchLastSection(True)
        
        for i, result in enumerate(self.recognition_results):
            self.table.insertRow(i)
            
            # 复选框
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.table.setCellWidget(i, 0, checkbox)
            
            # 文字内容
            self.table.setItem(i, 1, QTableWidgetItem(result['text']))
            
            # 位置
            bbox = result['bbox']
            pos_str = f"({bbox[0][0]},{bbox[0][1]}) - ({bbox[2][0]},{bbox[2][1]})"
            self.table.setItem(i, 2, QTableWidgetItem(pos_str))
            
            # 置信度
            confidence = result['confidence']
            self.table.setItem(i, 3, QTableWidgetItem(f"{confidence:.2%}"))
        
        layout.addWidget(self.table)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.delete_btn = QPushButton("删除选中文字")
        self.replace_btn = QPushButton("替换选中文字")
        self.cancel_btn = QPushButton("取消")
        
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.replace_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 连接信号
        self.delete_btn.clicked.connect(self.accept_delete)
        self.replace_btn.clicked.connect(self.accept_replace)
        self.cancel_btn.clicked.connect(self.reject)
    
    def get_selected_results(self):
        """获取选中的识别结果"""
        selected = []
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if checkbox.isChecked():
                selected.append(self.recognition_results[i])
        return selected
    
    def accept_delete(self):
        self.done(1)  # 返回1表示删除
    
    def accept_replace(self):
        self.done(2)  # 返回2表示替换


class TextReplaceDialog(QDialog):
    """文字替换对话框"""
    def __init__(self, old_text, font_features, system_fonts, parent=None):
        super().__init__(parent)
        self.old_text = old_text
        self.font_features = font_features
        self.system_fonts = system_fonts
        self.font_params = {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("替换文字")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 原文字
        layout.addWidget(QLabel("原文字:"))
        old_text_label = QLabel(self.old_text)
        old_text_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        layout.addWidget(old_text_label)
        
        # 新文字
        layout.addWidget(QLabel("新文字:"))
        self.new_text_input = QLineEdit()
        layout.addWidget(self.new_text_input)
        
        # 字体选择
        layout.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.system_fonts)
        # 尝试选择匹配的字体
        if self.font_features.get('is_bold'):
            for i, font in enumerate(self.system_fonts):
                if 'Hei' in font or 'Bold' in font:
                    self.font_combo.setCurrentIndex(i)
                    break
        layout.addWidget(self.font_combo)
        
        # 字体大小
        layout.addWidget(QLabel("字体大小:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.setValue(self.font_features.get('font_size', 24))
        layout.addWidget(self.font_size_spin)
        
        # 字体颜色
        layout.addWidget(QLabel("字体颜色:"))
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        font_color = self.font_features.get('font_color', (0, 0, 0))
        self.current_color = QColor(*font_color)
        self.update_color_button()
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def update_color_button(self):
        """更新颜色按钮"""
        self.color_btn.setStyleSheet(
            f"background-color: rgb({self.current_color.red()}, "
            f"{self.current_color.green()}, {self.current_color.blue()});"
            f"min-width: 100px; min-height: 30px;"
        )
    
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.update_color_button()
    
    def get_font_params(self):
        """获取字体参数"""
        return {
            'font_name': self.font_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'font_color': (self.current_color.red(), self.current_color.green(), self.current_color.blue())
        }
    
    def get_new_text(self):
        """获取新文字"""
        return self.new_text_input.text()


class FillModeDialog(QDialog):
    """填充模式选择对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fill_mode = 'inpaint'
        self.fill_color = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("选择填充模式")
        self.setMinimumSize(300, 200)
        
        layout = QVBoxLayout()
        
        # 填充模式选项
        self.inpaint_radio = QPushButton("智能填充 (推荐)")
        self.inpaint_radio.setCheckable(True)
        self.inpaint_radio.setChecked(True)
        self.inpaint_radio.clicked.connect(lambda: self.set_fill_mode('inpaint'))
        
        self.average_radio = QPushButton("平均颜色填充")
        self.average_radio.setCheckable(True)
        self.average_radio.clicked.connect(lambda: self.set_fill_mode('average'))
        
        self.median_radio = QPushButton("中位数填充")
        self.median_radio.setCheckable(True)
        self.median_radio.clicked.connect(lambda: self.set_fill_mode('median'))
        
        self.color_radio = QPushButton("纯色填充")
        self.color_radio.setCheckable(True)
        self.color_radio.clicked.connect(lambda: self.set_fill_mode('color'))
        
        layout.addWidget(self.inpaint_radio)
        layout.addWidget(self.average_radio)
        layout.addWidget(self.median_radio)
        layout.addWidget(self.color_radio)
        
        # 颜色选择（仅纯色填充时显示）
        self.color_btn = QPushButton("选择颜色")
        self.color_btn.setVisible(False)
        self.current_color = QColor(255, 255, 255)
        self.update_color_button()
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)
        
        layout.addStretch()
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def set_fill_mode(self, mode):
        """设置填充模式"""
        self.fill_mode = mode
        self.inpaint_radio.setChecked(mode == 'inpaint')
        self.average_radio.setChecked(mode == 'average')
        self.median_radio.setChecked(mode == 'median')
        self.color_radio.setChecked(mode == 'color')
        self.color_btn.setVisible(mode == 'color')
    
    def update_color_button(self):
        """更新颜色按钮"""
        self.color_btn.setStyleSheet(
            f"background-color: rgb({self.current_color.red()}, "
            f"{self.current_color.green()}, {self.current_color.blue()});"
            f"min-width: 100px; min-height: 30px;"
        )
    
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.update_color_button()
            self.fill_color = (color.red(), color.green(), color.blue())


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.current_image = None  # 当前图片（PIL.Image）
        self.original_image = None  # 原始图片
        self.current_file_path = None
        
        # 初始化管理器
        self.history_manager = HistoryManager(max_history=20)
        self.selection_manager = SelectionManager()
        self.image_processor = ImageProcessor()
        self.ocr_processor = OCRProcessor()
        self.text_editor = TextEditor()
        
        # OCR识别结果
        self.ocr_results = []
        
        self.init_ui()
        self.update_ui_state()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("图片修改工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 应用样式表
        self.apply_stylesheet()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 创建图片画布
        self.canvas = ImageCanvas()
        self.canvas.selection_changed.connect(self.on_selection_changed)
        layout.addWidget(self.canvas)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.create_status_bar()
    
    def apply_stylesheet(self):
        """应用样式表"""
        stylesheet = """
        /* 菜单栏样式 */
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-bottom: 1px solid #3d3d3d;
            padding: 4px;
            font-size: 13px;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
            margin: 2px;
        }
        
        QMenuBar::item:selected {
            background-color: #3d3d3d;
        }
        
        QMenuBar::item:pressed {
            background-color: #4a4a4a;
        }
        
        /* 菜单样式 */
        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 4px;
        }
        
        QMenu::item {
            padding: 6px 30px 6px 30px;
            border-radius: 3px;
            margin: 2px;
        }
        
        QMenu::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        QMenu::item:disabled {
            color: #666666;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #3d3d3d;
            margin: 4px 8px;
        }
        
        /* 工具栏样式 */
        QToolBar {
            background-color: #2b2b2b;
            border: none;
            border-bottom: 1px solid #3d3d3d;
            spacing: 4px;
            padding: 4px;
        }
        
        QToolBar::separator {
            background-color: #3d3d3d;
            width: 1px;
            margin: 4px 2px;
        }
        
        QToolButton {
            background-color: transparent;
            color: #ffffff;
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 6px 12px;
            margin: 2px;
        }
        
        QToolButton:hover {
            background-color: #3d3d3d;
            border: 1px solid #4a4a4a;
        }
        
        QToolButton:pressed {
            background-color: #4a4a4a;
        }
        
        QToolButton:disabled {
            color: #666666;
        }
        
        /* 状态栏样式 */
        QStatusBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-top: 1px solid #3d3d3d;
        }
        
        /* 主窗口背景 */
        QMainWindow {
            background-color: #1e1e1e;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("📁 文件(&F)")
        
        open_action = QAction("📂 打开(&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("打开图片文件")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("💾 保存(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("保存当前图片")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("💾 另存为(&A)", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.setStatusTip("将图片另存为新文件")
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ 退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("退出程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("✏️ 编辑(&E)")
        
        undo_action = QAction("↶ 撤销(&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setStatusTip("撤销上一步操作")
        undo_action.triggered.connect(self.undo)
        self.undo_action = undo_action
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("↷ 重做(&R)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.setStatusTip("重做上一步操作")
        redo_action.triggered.connect(self.redo)
        self.redo_action = redo_action
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        reset_action = QAction("🔄 重置(&R)", self)
        reset_action.setStatusTip("重置到原始图片")
        reset_action.triggered.connect(self.reset_image)
        edit_menu.addAction(reset_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("🔧 工具(&T)")
        
        vertical_delete_action = QAction("✂️ 垂直删除拼接(&V)", self)
        vertical_delete_action.setStatusTip("删除垂直选中区域并拼接剩余部分")
        vertical_delete_action.triggered.connect(self.vertical_delete_stitch)
        tools_menu.addAction(vertical_delete_action)
        
        smart_fill_action = QAction("🎨 智能填充(&F)", self)
        smart_fill_action.setStatusTip("使用智能算法填充选中区域")
        smart_fill_action.triggered.connect(self.smart_fill)
        tools_menu.addAction(smart_fill_action)
        
        tools_menu.addSeparator()
        
        ocr_action = QAction("🔍 文字识别(&O)", self)
        ocr_action.setStatusTip("识别图片中的文字")
        ocr_action.triggered.connect(self.recognize_text)
        tools_menu.addAction(ocr_action)
        
        tools_menu.addSeparator()
        
        delete_text_action = QAction("🗑️ 删除选中文字(&D)", self)
        delete_text_action.setStatusTip("删除已识别的选中文字")
        delete_text_action.triggered.connect(self.delete_selected_text_from_menu)
        self.delete_text_action = delete_text_action
        tools_menu.addAction(delete_text_action)
        
        replace_text_action = QAction("✏️ 替换选中文字(&R)", self)
        replace_text_action.setStatusTip("替换已识别的选中文字")
        replace_text_action.triggered.connect(self.replace_selected_text_from_menu)
        self.replace_text_action = replace_text_action
        tools_menu.addAction(replace_text_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("👁️ 视图(&V)")
        
        fit_window_action = QAction("📐 适应窗口(&F)", self)
        fit_window_action.setStatusTip("自动缩放图片以适应窗口")
        fit_window_action.triggered.connect(self.canvas.fit_to_window)
        view_menu.addAction(fit_window_action)
        
        zoom_in_action = QAction("🔍+ 放大(&I)", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.setStatusTip("放大图片")
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔍- 缩小(&O)", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.setStatusTip("缩小图片")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("🔍 重置缩放(&R)", self)
        reset_zoom_action.setStatusTip("重置图片缩放为原始大小")
        reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        view_menu.addAction(reset_zoom_action)
    
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        # 打开文件
        open_btn = QAction("📂 打开", self)
        open_btn.setStatusTip("打开图片文件")
        open_btn.triggered.connect(self.open_file)
        toolbar.addAction(open_btn)
        
        toolbar.addSeparator()
        
        # 垂直删除拼接
        vertical_delete_btn = QAction("✂️ 垂直删除", self)
        vertical_delete_btn.setStatusTip("删除垂直选中区域并拼接")
        vertical_delete_btn.triggered.connect(self.vertical_delete_stitch)
        toolbar.addAction(vertical_delete_btn)
        
        # 智能填充
        smart_fill_btn = QAction("🎨 智能填充", self)
        smart_fill_btn.setStatusTip("智能填充选中区域")
        smart_fill_btn.triggered.connect(self.smart_fill)
        toolbar.addAction(smart_fill_btn)
        
        toolbar.addSeparator()
        
        # 文字识别
        ocr_btn = QAction("🔍 文字识别", self)
        ocr_btn.setStatusTip("识别图片中的文字")
        ocr_btn.triggered.connect(self.recognize_text)
        toolbar.addAction(ocr_btn)
        
        toolbar.addSeparator()
        
        # 撤销
        self.undo_btn = QAction("↶ 撤销", self)
        self.undo_btn.setStatusTip("撤销上一步操作")
        self.undo_btn.triggered.connect(self.undo)
        toolbar.addAction(self.undo_btn)
        
        # 重做
        self.redo_btn = QAction("↷ 重做", self)
        self.redo_btn.setStatusTip("重做上一步操作")
        self.redo_btn.triggered.connect(self.redo)
        toolbar.addAction(self.redo_btn)
        
        toolbar.addSeparator()
        
        # 保存
        save_btn = QAction("💾 保存", self)
        save_btn.setStatusTip("保存当前图片")
        save_btn.triggered.connect(self.save_file)
        toolbar.addAction(save_btn)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
    
    def update_ui_state(self):
        """更新UI状态"""
        has_image = self.current_image is not None
        has_selection = self.canvas.get_selection() is not None
        has_ocr_results = len(self.ocr_results) > 0
        
        # 更新撤销/重做按钮
        self.undo_action.setEnabled(self.history_manager.can_undo())
        self.redo_action.setEnabled(self.history_manager.can_redo())
        self.undo_btn.setEnabled(self.history_manager.can_undo())
        self.redo_btn.setEnabled(self.history_manager.can_redo())
        
        # 更新文字删除/替换按钮（需要OCR结果）
        if hasattr(self, 'delete_text_action'):
            self.delete_text_action.setEnabled(has_image and has_ocr_results)
        if hasattr(self, 'replace_text_action'):
            self.replace_text_action.setEnabled(has_image and has_ocr_results)
        
        # 更新状态栏
        if has_image:
            info = self.history_manager.get_current_state()
            if info:
                ocr_info = f" | 已识别文字: {len(self.ocr_results)}个" if has_ocr_results else ""
                self.status_bar.showMessage(
                    f"图片尺寸: {info.width}x{info.height} | "
                    f"选择区域: {self.canvas.get_selection() if has_selection else '无'}"
                    f"{ocr_info}"
                )
        else:
            self.status_bar.showMessage("就绪")
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp);;所有文件 (*.*)"
        )
        
        if file_path:
            image = FileHandler.open_image(file_path)
            if image:
                self.current_image = image
                self.original_image = image.copy()
                self.current_file_path = file_path
                self.canvas.set_image(image)
                self.history_manager.reset(image)
                self.canvas.clear_selection()
                self.update_ui_state()
                self.status_bar.showMessage(f"已打开: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "错误", "无法打开图片文件")
    
    def save_file(self):
        """保存文件"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "没有可保存的图片")
            return
        
        if self.current_file_path:
            if FileHandler.save_image(self.current_image, self.current_file_path):
                self.status_bar.showMessage(f"已保存: {os.path.basename(self.current_file_path)}")
                QMessageBox.information(self, "成功", "图片已保存")
            else:
                QMessageBox.warning(self, "错误", "保存失败")
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """另存为"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "没有可保存的图片")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存图片",
            "",
            "PNG文件 (*.png);;JPEG文件 (*.jpg);;BMP文件 (*.bmp);;所有文件 (*.*)"
        )
        
        if file_path:
            if FileHandler.save_image(self.current_image, file_path):
                self.current_file_path = file_path
                self.status_bar.showMessage(f"已保存: {os.path.basename(file_path)}")
                QMessageBox.information(self, "成功", "图片已保存")
            else:
                QMessageBox.warning(self, "错误", "保存失败")
    
    def undo(self):
        """撤销"""
        image = self.history_manager.undo()
        if image:
            self.current_image = image
            self.canvas.set_image(image)
            self.update_ui_state()
    
    def redo(self):
        """重做"""
        image = self.history_manager.redo()
        if image:
            self.current_image = image
            self.canvas.set_image(image)
            self.update_ui_state()
    
    def reset_image(self):
        """重置图片"""
        if self.original_image:
            reply = QMessageBox.question(
                self,
                "确认",
                "确定要重置到原始图片吗？这将丢失所有修改。",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.current_image = self.original_image.copy()
                self.canvas.set_image(self.current_image)
                self.history_manager.reset(self.current_image)
                self.canvas.clear_selection()
                self.update_ui_state()
    
    def on_selection_changed(self, selection_rect):
        """选择区域改变"""
        self.update_ui_state()
    
    def vertical_delete_stitch(self):
        """垂直删除拼接"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return
        
        selection = self.canvas.get_selection()
        if not selection:
            QMessageBox.warning(self, "警告", "请先选择要删除的区域")
            return
        
        # 保存当前状态
        self.history_manager.save_state(self.current_image)
        
        # 执行垂直删除拼接
        result = self.image_processor.vertical_delete_and_stitch(self.current_image, selection)
        if result:
            self.current_image = result
            self.canvas.set_image(result)
            self.canvas.clear_selection()
            self.update_ui_state()
            self.status_bar.showMessage("垂直删除拼接完成")
    
    def smart_fill(self):
        """智能填充"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return
        
        selection = self.canvas.get_selection()
        if not selection:
            QMessageBox.warning(self, "警告", "请先选择要填充的区域")
            return
        
        # 显示填充模式选择对话框
        dialog = FillModeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 保存当前状态
            self.history_manager.save_state(self.current_image)
            
            # 执行填充
            fill_mode = dialog.fill_mode
            fill_color = dialog.fill_color if fill_mode == 'color' else None
            result = self.image_processor.smart_fill(
                self.current_image, selection, fill_mode, fill_color
            )
            
            if result:
                self.current_image = result
                self.canvas.set_image(result)
                self.canvas.clear_selection()
                self.update_ui_state()
                self.status_bar.showMessage(f"智能填充完成 ({fill_mode})")
    
    def recognize_text(self):
        """文字识别"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return
        
        if not self.ocr_processor.is_available():
            QMessageBox.warning(
                self,
                "错误",
                "OCR功能不可用。\n请确保已安装PaddleOCR:\npip install paddlepaddle paddleocr"
            )
            return
        
        selection = self.canvas.get_selection()
        if not selection:
            QMessageBox.warning(self, "警告", "请先选择包含文字的区域")
            return
        
        # 提取选中区域
        x1, y1, x2, y2 = selection
        region = self.current_image.crop((x1, y1, x2, y2))
        
        # 显示进度对话框
        progress = QProgressDialog("正在识别文字...", "取消", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        # 在后台线程中执行OCR
        self.ocr_thread = OCRThread(region)
        self.ocr_thread.finished.connect(
            lambda results: self.on_ocr_finished(results, progress)
        )
        self.ocr_thread.error.connect(
            lambda error: self.on_ocr_error(error, progress)
        )
        self.ocr_thread.start()
    
    def on_ocr_finished(self, results, progress):
        """OCR识别完成"""
        progress.close()
        
        if not results:
            QMessageBox.information(self, "提示", "未识别到文字")
            return
        
        # 保存识别结果
        self.ocr_results = results
        
        # 更新UI状态（启用文字删除/替换菜单）
        self.update_ui_state()
        
        # 显示识别结果对话框
        dialog = TextRecognitionDialog(results, self)
        result = dialog.exec_()
        
        if result == 1:  # 删除
            self.delete_selected_texts(dialog.get_selected_results())
        elif result == 2:  # 替换
            selected = dialog.get_selected_results()
            if selected:
                # 暂时只处理第一个选中的文字
                self.replace_text(selected[0])
    
    def on_ocr_error(self, error, progress):
        """OCR识别错误"""
        progress.close()
        QMessageBox.warning(self, "错误", error)
    
    def delete_selected_texts(self, selected_results):
        """删除选中的文字"""
        if not selected_results:
            return
        
        # 保存当前状态
        self.history_manager.save_state(self.current_image)
        
        # 获取所有文字边界框
        bboxes = [result['bbox'] for result in selected_results]
        
        # 删除文字
        processed_image = self.text_editor.delete_text(self.current_image, bboxes)
        if processed_image:
            self.current_image = processed_image
            self.canvas.set_image(processed_image)
            self.canvas.clear_selection()
            # 从OCR结果中移除已删除的文字
            deleted_bboxes = set(tuple(map(tuple, r['bbox'])) for r in selected_results)
            self.ocr_results = [
                r for r in self.ocr_results 
                if tuple(map(tuple, r['bbox'])) not in deleted_bboxes
            ]
            self.update_ui_state()
            self.status_bar.showMessage(f"已删除 {len(selected_results)} 个文字")
    
    def replace_text(self, ocr_result):
        """替换文字"""
        old_text = ocr_result['text']
        bbox = ocr_result['bbox']
        
        # 提取字体特征
        font_features = self.text_editor.extract_font_features(self.current_image, bbox)
        
        # 获取系统字体
        system_fonts = self.ocr_processor.get_system_fonts()
        
        # 显示替换对话框
        dialog = TextReplaceDialog(old_text, font_features, system_fonts, self)
        if dialog.exec_() == QDialog.Accepted:
            new_text = dialog.get_new_text()
            if not new_text:
                QMessageBox.warning(self, "警告", "新文字不能为空")
                return
            
            # 保存当前状态
            self.history_manager.save_state(self.current_image)
            
            # 获取字体参数
            font_params = dialog.get_font_params()
            # 获取字体路径
            font_path, _ = self.text_editor.match_font(font_features, new_text)
            font_params['font_path'] = font_path
            
            # 替换文字
            result = self.text_editor.replace_text(
                self.current_image, bbox, new_text, font_params
            )
            
            if result:
                self.current_image = result
                self.canvas.set_image(result)
                self.canvas.clear_selection()
                # 更新OCR结果（替换后的文字位置可能变化，暂时移除旧结果）
                # 如果需要继续编辑，可以重新识别
                self.ocr_results = []
                self.update_ui_state()
                self.status_bar.showMessage(f"文字已替换: {old_text} -> {new_text}")
    
    def delete_selected_text_from_menu(self):
        """从菜单栏删除选中文字"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return
        
        # 检查是否有OCR识别结果
        if not self.ocr_results:
            QMessageBox.warning(
                self,
                "提示",
                "没有可删除的文字。\n请先使用"文字识别"功能识别图片中的文字。"
            )
            return
        
        # 检查是否有选中的区域
        selection = self.canvas.get_selection()
        if not selection:
            # 如果没有选中区域，显示所有识别结果供选择
            dialog = TextRecognitionDialog(self.ocr_results, self)
            result = dialog.exec_()
            if result == 1:  # 删除
                self.delete_selected_texts(dialog.get_selected_results())
            return
        
        # 如果有选中区域，查找该区域内的文字
        x1, y1, x2, y2 = selection
        selected_texts = []
        for ocr_result in self.ocr_results:
            bbox = ocr_result['bbox']
            # 检查文字是否在选择区域内
            text_x1 = min(point[0] for point in bbox)
            text_y1 = min(point[1] for point in bbox)
            text_x2 = max(point[0] for point in bbox)
            text_y2 = max(point[1] for point in bbox)
            
            # 判断文字是否在选择区域内（至少50%重叠）
            if (text_x1 >= x1 and text_y1 >= y1 and text_x2 <= x2 and text_y2 <= y2):
                selected_texts.append(ocr_result)
        
        if not selected_texts:
            QMessageBox.information(self, "提示", "选中区域内没有识别到的文字")
            return
        
        # 删除选中的文字
        self.delete_selected_texts(selected_texts)
    
    def replace_selected_text_from_menu(self):
        """从菜单栏替换选中文字"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return
        
        # 检查是否有OCR识别结果
        if not self.ocr_results:
            QMessageBox.warning(
                self,
                "提示",
                "没有可替换的文字。\n请先使用"文字识别"功能识别图片中的文字。"
            )
            return
        
        # 检查是否有选中的区域
        selection = self.canvas.get_selection()
        if not selection:
            # 如果没有选中区域，显示所有识别结果供选择
            dialog = TextRecognitionDialog(self.ocr_results, self)
            result = dialog.exec_()
            if result == 2:  # 替换
                selected = dialog.get_selected_results()
                if selected:
                    # 只处理第一个选中的文字
                    self.replace_text(selected[0])
            return
        
        # 如果有选中区域，查找该区域内的文字
        x1, y1, x2, y2 = selection
        selected_texts = []
        for ocr_result in self.ocr_results:
            bbox = ocr_result['bbox']
            # 检查文字是否在选择区域内
            text_x1 = min(point[0] for point in bbox)
            text_y1 = min(point[1] for point in bbox)
            text_x2 = max(point[0] for point in bbox)
            text_y2 = max(point[1] for point in bbox)
            
            # 判断文字是否在选择区域内（至少50%重叠）
            if (text_x1 >= x1 and text_y1 >= y1 and text_x2 <= x2 and text_y2 <= y2):
                selected_texts.append(ocr_result)
        
        if not selected_texts:
            QMessageBox.information(self, "提示", "选中区域内没有识别到的文字")
            return
        
        # 只处理第一个匹配的文字
        self.replace_text(selected_texts[0])

