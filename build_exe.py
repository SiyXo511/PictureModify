"""
打包脚本 - 使用PyInstaller将程序打包成exe
"""
import os
import sys
import subprocess


def build_exe():
    """打包exe文件"""
    print("开始打包...")
    
    # PyInstaller命令
    cmd = [
        "pyinstaller",
        "--onefile",  # 单文件
        "--windowed",  # 隐藏控制台窗口
        "--name=PictureModify",  # 可执行文件名
        "--icon=NONE",  # 图标（如果有的话）
        "--add-data=src;src",  # 包含src目录
        "--hidden-import=PIL._tkinter_finder",  # 隐藏导入
        "--hidden-import=paddleocr",  # 隐藏导入
        "--hidden-import=paddle",  # 隐藏导入
        "--collect-all=paddleocr",  # 收集paddleocr的所有数据
        "--collect-all=paddle",  # 收集paddle的所有数据
        "src/main.py"  # 主程序入口
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n打包完成！")
        print("可执行文件位于: dist/PictureModify.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n错误: 未找到PyInstaller")
        print("请先安装: pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()

