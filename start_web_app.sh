#!/bin/bash
# Web股票图表应用启动脚本

echo "🌐 启动交互式股票图表Web应用"
echo "================================"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "📦 检查依赖..."
pip show flask > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 安装 Flask..."
    pip install flask
fi

pip show plotly > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 安装 Plotly..."
    pip install plotly
fi

# 检查数据库文件
if [ ! -f "output/kline_data/a_share_klines.db" ]; then
    echo "⚠️  K线数据库不存在: output/kline_data/a_share_klines.db"
    echo "   请先运行K线数据下载脚本"
fi

if [ ! -f "output/index_data/major_indices.db" ]; then
    echo "⚠️  指数数据库不存在: output/index_data/major_indices.db"
    echo "   请先运行指数数据下载脚本"
fi

# 启动Web应用
echo "🚀 启动Web应用..."
echo "🔗 访问地址: http://127.0.0.1:5001"
echo "📊 支持多股票对比、指数对照、时间筛选"
echo "💡 按 Ctrl+C 停止应用"
echo ""

python web_chart_app.py
