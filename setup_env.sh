#!/bin/bash
# 虚拟环境设置脚本 (Linux/macOS)

echo "========================================"
echo "图片修改工具 - 环境设置脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8或更高版本"
    exit 1
fi

echo "[1/4] 检查Python版本..."
python3 --version
echo ""

# 创建虚拟环境
echo "[2/4] 创建虚拟环境..."
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        exit 1
    fi
    echo "虚拟环境创建成功！"
fi
echo ""

# 激活虚拟环境
echo "[3/4] 激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[错误] 激活虚拟环境失败"
    exit 1
fi
echo "虚拟环境已激活"
echo ""

# 升级pip
echo "[4/4] 升级pip..."
python -m pip install --upgrade pip
echo ""

# 安装依赖
echo "[5/5] 安装项目依赖..."
echo "这可能需要几分钟时间，请耐心等待..."
echo ""
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "[警告] 部分依赖安装失败，请检查错误信息"
    echo "如果PaddleOCR安装失败，可以稍后手动安装:"
    echo "  pip install paddlepaddle paddleocr"
else
    echo ""
    echo "========================================"
    echo "环境设置完成！"
    echo "========================================"
    echo ""
    echo "使用方法:"
    echo "  1. 激活虚拟环境: source venv/bin/activate"
    echo "  2. 运行程序: python src/main.py"
    echo "  3. 退出虚拟环境: deactivate"
    echo ""
fi

