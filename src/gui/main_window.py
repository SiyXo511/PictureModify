"""
主窗口模块
"""
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMenuBar, QToolBar, QStatusBar, QAction, QFileDialog,
                             QMessageBox, QDialog, QLabel, QPushButton, QComboBox,
                             QSpinBox, QColorDialog, QLineEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QColor

from src.gui.image_canvas import ImageCanvas
from src.utils.file_handler import FileHandler
from src.utils.history_manager import HistoryManager
from src.core.selection_manager import SelectionManager
from src.core.image_processor import ImageProcessor
from src.core.text_editor import TextEditor


class TextInputDialog(QDialog):
    """文字输入与样式调整对话框"""

    def __init__(self, font_features, system_fonts, parent=None, title="添加文字",
                 default_text="", preset_features=None, initial_params=None):
        super().__init__(parent)
        self.font_features = font_features or {}
        self.system_fonts = system_fonts or []
        self.preset_features = preset_features or None
        self.initial_params = initial_params or {}
        initial_color = (self.initial_params.get('font_color') or
                         self.font_features.get('font_color') or (0, 0, 0))
        self.current_color = QColor(*initial_color)
        self.default_text = default_text
        self.setWindowTitle(title)
        self.setMinimumSize(400, 280)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("新文字:"))
        self.new_text_input = QLineEdit()
        self.new_text_input.setText(self.default_text)
        layout.addWidget(self.new_text_input)

        layout.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.system_fonts)
        layout.addWidget(self.font_combo)

        layout.addWidget(QLabel("字体大小:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        layout.addWidget(self.font_size_spin)

        layout.addWidget(QLabel("字体颜色:"))
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self._update_color_button()
        self.color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        if self.preset_features:
            preset_layout = QHBoxLayout()
            preset_btn = QPushButton("应用采样样式")
            preset_btn.clicked.connect(self._apply_preset_features)
            preset_layout.addWidget(preset_btn)
            preset_layout.addStretch()
            layout.addLayout(preset_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        self._apply_features(self.font_features)
        if self.initial_params:
            self._apply_features(self.initial_params)

    def _update_color_button(self):
        self.color_btn.setStyleSheet(
            f"background-color: rgb({self.current_color.red()}, {self.current_color.green()}, {self.current_color.blue()});"
            f"min-width: 100px; min-height: 30px;"
        )

    def _choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self._update_color_button()

    def _apply_preset_features(self):
        if self.preset_features:
            self._apply_features(self.preset_features)

    def _apply_features(self, features):
        if not features:
            return

        font_size = features.get('font_size')
        if font_size is not None:
            self.font_size_spin.setValue(int(font_size))

        font_color = features.get('font_color')
        if font_color:
            self.current_color = QColor(*font_color)
            self._update_color_button()

        preferred_font = (features.get('preferred_font') or
                          features.get('font_name'))
        if preferred_font and preferred_font in self.system_fonts:
            index = self.font_combo.findText(preferred_font)
            if index >= 0:
                self.font_combo.setCurrentIndex(index)

    def get_text(self):
        return self.new_text_input.text().strip()

    def get_font_params(self):
        return {
            'font_name': self.font_combo.currentText() if self.font_combo.count() > 0 else None,
            'font_size': self.font_size_spin.value(),
            'font_color': (
                self.current_color.red(),
                self.current_color.green(),
                self.current_color.blue()
            )
        }

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
        self.text_editor = TextEditor()
        self.sampled_font_features = None
        self.last_text_edit = None
        
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
        
        sample_text_action = QAction("🎯 采样文字样式(&S)", self)
        sample_text_action.setStatusTip("提取选区文字的字体样式供复用")
        sample_text_action.triggered.connect(self.sample_text_style)
        self.sample_text_action = sample_text_action
        tools_menu.addAction(sample_text_action)

        tools_menu.addSeparator()

        delete_text_action = QAction("🗑️ 删除选区文字(&D)", self)
        delete_text_action.setStatusTip("使用智能填充删除选区内的文字")
        delete_text_action.triggered.connect(self.delete_text_in_selection)
        self.delete_text_action = delete_text_action
        tools_menu.addAction(delete_text_action)
        
        add_text_action = QAction("✏️ 添加文字(&A)", self)
        add_text_action.setStatusTip("在选区内添加新的文字")
        add_text_action.triggered.connect(self.add_text_in_selection)
        self.add_text_action = add_text_action
        tools_menu.addAction(add_text_action)

        edit_text_action = QAction("🛠️ 编辑文字(&E)", self)
        edit_text_action.setStatusTip("调整最近添加的文字样式或位置")
        edit_text_action.triggered.connect(self.edit_text_in_selection)
        self.edit_text_action = edit_text_action
        tools_menu.addAction(edit_text_action)
        
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

        # 删除/添加文字
        self.sample_text_btn = QAction("🎯 采样样式", self)
        self.sample_text_btn.setStatusTip("采样选区中文字的样式")
        self.sample_text_btn.triggered.connect(self.sample_text_style)
        toolbar.addAction(self.sample_text_btn)

        self.delete_text_btn = QAction("🗑️ 删除文字", self)
        self.delete_text_btn.setStatusTip("删除选区中的文字")
        self.delete_text_btn.triggered.connect(self.delete_text_in_selection)
        toolbar.addAction(self.delete_text_btn)
        
        self.add_text_btn = QAction("✏️ 添加文字", self)
        self.add_text_btn.setStatusTip("在选区内添加新的文字")
        self.add_text_btn.triggered.connect(self.add_text_in_selection)
        toolbar.addAction(self.add_text_btn)

        self.edit_text_btn = QAction("🛠️ 编辑文字", self)
        self.edit_text_btn.setStatusTip("调整最近添加文字的样式或位置")
        self.edit_text_btn.triggered.connect(self.edit_text_in_selection)
        toolbar.addAction(self.edit_text_btn)

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
        # 更新撤销/重做按钮
        self.undo_action.setEnabled(self.history_manager.can_undo())
        self.redo_action.setEnabled(self.history_manager.can_redo())
        self.undo_btn.setEnabled(self.history_manager.can_undo())
        self.redo_btn.setEnabled(self.history_manager.can_redo())
        
        can_sample = has_image and has_selection
        can_modify = has_image and has_selection
        can_edit_text = has_image and self.last_text_edit is not None

        if hasattr(self, 'sample_text_action'):
            self.sample_text_action.setEnabled(can_sample)
        if hasattr(self, 'delete_text_action'):
            self.delete_text_action.setEnabled(can_modify)
        if hasattr(self, 'add_text_action'):
            self.add_text_action.setEnabled(can_modify)
        if hasattr(self, 'edit_text_action'):
            self.edit_text_action.setEnabled(can_edit_text)

        if hasattr(self, 'sample_text_btn'):
            self.sample_text_btn.setEnabled(can_sample)
        if hasattr(self, 'delete_text_btn'):
            self.delete_text_btn.setEnabled(can_modify)
        if hasattr(self, 'add_text_btn'):
            self.add_text_btn.setEnabled(can_modify)
        if hasattr(self, 'edit_text_btn'):
            self.edit_text_btn.setEnabled(can_edit_text)
        
        # 更新状态栏
        if has_image:
            info = self.history_manager.get_current_state()
            if info:
                self.status_bar.showMessage(
                    f"图片尺寸: {info.width}x{info.height} | "
                    f"选择区域: {self.canvas.get_selection() if has_selection else '无'}"
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
                self.sampled_font_features = None
                self.last_text_edit = None
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
                self.sampled_font_features = None
                self.last_text_edit = None
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
    
    def sample_text_style(self):
        """采样当前选区的文字样式"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return

        selection = self.canvas.get_selection()
        if not selection:
            QMessageBox.warning(self, "警告", "请先选择要采样的文字区域")
            return

        bbox = self._selection_to_bbox(selection)
        if bbox is None:
            QMessageBox.warning(self, "警告", "选区无效，无法采样")
            return

        features = self.text_editor.extract_font_features(self.current_image, bbox)
        font_path, _ = self.text_editor.match_font(features, "sample")
        if font_path:
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            features['preferred_font'] = font_name

        self.sampled_font_features = features
        self.status_bar.showMessage("已采样选区文字样式，可在添加文字时应用")

    def delete_text_in_selection(self):
        """删除选区内的文字"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return

        selection = self.canvas.get_selection()
        if not selection:
            QMessageBox.warning(self, "警告", "请先选择要删除文字的区域")
            return

        bbox = self._selection_to_bbox(selection)
        if bbox is None:
            QMessageBox.warning(self, "警告", "选区无效")
            return

        self.history_manager.save_state(self.current_image)

        processed_image = self.text_editor.delete_text(self.current_image, [bbox])
        if processed_image:
            self.current_image = processed_image
            self.canvas.set_image(processed_image)
            self.canvas.clear_selection()
            self.last_text_edit = None
            self.update_ui_state()
            self.status_bar.showMessage("选区文字已删除")

    def add_text_in_selection(self):
        """在选区内添加文字"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return

        selection = self.canvas.get_selection()
        if not selection:
            QMessageBox.warning(self, "警告", "请先选择要添加文字的区域")
            return

        bbox = self._selection_to_bbox(selection)
        if bbox is None:
            QMessageBox.warning(self, "警告", "选区无效")
            return

        selection_rect = self._bbox_to_rect(bbox)
        area_snapshot = self.current_image.crop(selection_rect)

        font_features = self._get_font_features_from_selection(selection)
        system_fonts = self.text_editor.get_system_fonts()

        dialog = TextInputDialog(
            font_features,
            system_fonts,
            self,
            title="添加文字",
            preset_features=self.sampled_font_features,
            initial_params=self.sampled_font_features
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        new_text = dialog.get_text()
        if not new_text:
            QMessageBox.warning(self, "警告", "文字内容不能为空")
            return

        font_params = dialog.get_font_params()

        self.history_manager.save_state(self.current_image)

        result = self.text_editor.add_text(
            self.current_image,
            bbox,
            new_text,
            font_params,
            font_features
        )

        if result:
            self.current_image = result
            self.canvas.set_image(result)
            self.canvas.clear_selection()
            stored_features = dict(font_features or {})
            stored_features['font_color'] = font_params.get('font_color')
            stored_features['font_size'] = font_params.get('font_size')
            if font_params.get('font_name'):
                stored_features['preferred_font'] = font_params.get('font_name')
            self.last_text_edit = {
                'bbox': [list(point) for point in bbox],
                'selection_rect': selection_rect,
                'snapshot': area_snapshot,
                'text': new_text,
                'font_params': dict(font_params),
                'font_features': stored_features
            }
            self.update_ui_state()
            self.status_bar.showMessage(f"已添加文字: {new_text}")

    def edit_text_in_selection(self):
        """编辑最近添加的文字"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先打开图片")
            return

        if not self.last_text_edit:
            QMessageBox.information(self, "提示", "暂无可编辑的文字，请先添加文字")
            return

        selection = self.canvas.get_selection()
        if selection:
            bbox = self._selection_to_bbox(selection)
            if bbox is None:
                QMessageBox.warning(self, "警告", "选区无效")
                return
            selection_rect = self._bbox_to_rect(bbox)
        else:
            bbox = self.last_text_edit['bbox']
            selection_rect = self.last_text_edit.get('selection_rect')

        if selection_rect is None:
            QMessageBox.warning(self, "警告", "缺少文字位置，请重新选择区域")
            return

        last_info = self.last_text_edit

        working_image = self.current_image.copy()
        previous_rect = last_info.get('selection_rect')
        snapshot = last_info.get('snapshot')
        if snapshot and previous_rect:
            working_image.paste(snapshot, (previous_rect[0], previous_rect[1]))

        area_snapshot = working_image.crop(selection_rect)

        base_features = self.text_editor.extract_font_features(working_image, bbox)
        if not base_features or base_features.get('font_color') is None:
            base_features = dict(last_info.get('font_features') or {})

        preset_features = self.sampled_font_features or last_info.get('font_features')
        system_fonts = self.text_editor.get_system_fonts()

        dialog = TextInputDialog(
            base_features,
            system_fonts,
            self,
            title="编辑文字",
            default_text=last_info.get('text', ""),
            preset_features=preset_features,
            initial_params=last_info.get('font_params')
        )

        if dialog.exec_() != QDialog.Accepted:
            self.update_ui_state()
            return

        new_text = dialog.get_text()
        if not new_text:
            QMessageBox.warning(self, "警告", "文字内容不能为空")
            return

        font_params = dialog.get_font_params()

        self.history_manager.save_state(self.current_image)

        updated_image = self.text_editor.add_text(
            working_image,
            bbox,
            new_text,
            font_params,
            base_features
        )

        if updated_image:
            self.current_image = updated_image
            self.canvas.set_image(updated_image)
            self.canvas.clear_selection()
            stored_features = dict(base_features or {})
            stored_features['font_color'] = font_params.get('font_color')
            stored_features['font_size'] = font_params.get('font_size')
            if font_params.get('font_name'):
                stored_features['preferred_font'] = font_params.get('font_name')
            self.last_text_edit = {
                'bbox': [list(point) for point in bbox],
                'selection_rect': selection_rect,
                'snapshot': area_snapshot,
                'text': new_text,
                'font_params': dict(font_params),
                'font_features': stored_features
            }
            self.update_ui_state()
            self.status_bar.showMessage("文字样式已更新")

    def _selection_to_bbox(self, selection):
        if not selection:
            return None

        x1, y1, x2, y2 = selection
        if x1 == x2 or y1 == y2:
            return None

        return [
            [int(x1), int(y1)],
            [int(x2), int(y1)],
            [int(x2), int(y2)],
            [int(x1), int(y2)],
        ]

    def _bbox_to_rect(self, bbox):
        if not bbox:
            return None
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        return (
            int(min(x_coords)),
            int(min(y_coords)),
            int(max(x_coords)),
            int(max(y_coords))
        )

    def _get_font_features_from_selection(self, selection):
        bbox = self._selection_to_bbox(selection)
        if bbox is None:
            return self.text_editor.get_default_font_features()

        features = self.text_editor.extract_font_features(self.current_image, bbox)

        # 提供一个可用于优先显示的字体名称
        font_path, _ = self.text_editor.match_font(features, "sample")
        if font_path:
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            features['preferred_font'] = font_name
        return features

