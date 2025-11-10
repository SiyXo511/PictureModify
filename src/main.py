"""
图片修改工具 - 主程序入口
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 必须在创建QApplication之前设置高DPI支持
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from src.gui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("图片修改工具")
    app.setOrganizationName("PictureModify")
    
    # 创建主窗口
    window = MainWindow()
    window.showMaximized()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

