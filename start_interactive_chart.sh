#!/bin/bash
# 交互式图表启动脚本

echo "🚀 启动交互式股票图表工具"
echo "================================"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查plotly是否安装
echo "📦 检查依赖..."
pip show plotly > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 安装 Plotly..."
    pip install plotly
fi

# 检查数据库文件
if [ ! -f "output/kline_data/a_share_klines.db" ]; then
    echo "⚠️  K线数据库不存在，请先运行数据下载脚本"
fi

if [ ! -f "output/index_data/major_indices.db" ]; then
    echo "⚠️  指数数据库不存在，请先运行指数下载脚本"
fi

# 启动交互式图表工具
echo "🎯 启动交互式图表工具..."
python interactive_chart_plotter.py
