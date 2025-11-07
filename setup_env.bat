@echo off
REM 虚拟环境设置脚本 (Windows)
echo ========================================
echo 图片修改工具 - 环境设置脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检查Python版本...
python --version
echo.

REM 创建虚拟环境
echo [2/4] 创建虚拟环境...
if exist venv (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功！
)
echo.

REM 激活虚拟环境
echo [3/4] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)
echo 虚拟环境已激活
echo.

REM 升级pip
echo [4/4] 升级pip...
python -m pip install --upgrade pip
echo.

REM 安装依赖
echo [5/5] 安装项目依赖...
echo 这可能需要几分钟时间，请耐心等待...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [警告] 部分依赖安装失败，请检查错误信息
    echo 如果PaddleOCR安装失败，可以稍后手动安装:
    echo   pip install paddlepaddle paddleocr
) else (
    echo.
    echo ========================================
    echo 环境设置完成！
    echo ========================================
    echo.
    echo 使用方法:
    echo   1. 激活虚拟环境: venv\Scripts\activate
    echo   2. 运行程序: python src\main.py
    echo   3. 退出虚拟环境: deactivate
    echo.
)

pause

