# 📊 35年A股数据分析平台

一个完整的A股历史数据获取、存储和可视化分析平台，支持从1990年至今的完整股票和指数数据。

## 🎯 功能特色

### 📈 数据获取
- **K线数据获取**: 支持所有A股股票从1990年至今的历史K线数据
- **指数数据获取**: 支持主要股票指数的历史数据
- **自动重试机制**: 内置网络重试和错误恢复机制
- **进度跟踪**: 实时下载进度监控和断点续传

### 🌐 Web可视化
- **交互式图表**: 基于Plotly.js的高质量交互式股票图表
- **多股票对比**: 支持同时对比多只股票的价格走势
- **标准化分析**: 提供价格标准化对比功能
- **指数对照**: 实时显示股票与市场指数的对比
- **Mac触摸板优化**: 完美支持Mac触摸板的缩放和平移操作

### 📱 用户体验
- **响应式设计**: 适配各种屏幕尺寸
- **快速搜索**: 优化的股票搜索功能，支持模糊匹配
- **实时交互**: 鼠标悬浮显示详细数据
- **现代化界面**: 基于Bootstrap的美观界面设计

## 🚀 快速开始

### 环境要求
- Python 3.7+
- 网络连接

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/jiejieguan/35years-a-.git
cd 35years-a-
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **下载数据**（⚠️ 重要：数据文件较大，未包含在仓库中）
```bash
# 推荐：一次性下载全部数据（1990年至今）
python full_download_1990.py

# 或者分步下载：
# 下载指数数据（较快，约10分钟）
python run_index_download.py

# 下载K线数据（较慢，约2-6小时）
python run_kline_download.py
```

> 📋 **数据说明**: 由于数据库文件约2.3GB，无法上传到GitHub。请查看 [DATA_SETUP.md](DATA_SETUP.md) 了解详细的数据生成步骤。

5. **启动Web应用**
```bash
# 使用便捷脚本
./start_web_app.sh

# 或直接运行
python web_chart_app.py
```

6. **访问应用**
打开浏览器访问: http://localhost:5002

## 📂 项目结构

```
35years-a-/
├── 📄 核心模块
│   ├── a_share_kline_fetcher.py    # K线数据获取模块
│   ├── major_index_fetcher.py      # 指数数据获取模块
│   ├── web_chart_app.py           # Web图表应用
│   ├── interactive_chart_plotter.py # 交互式图表生成
│   └── kline_data_query.py        # 数据查询工具
├── 🚀 启动脚本
│   ├── run_kline_download.py      # K线数据下载
│   ├── run_index_download.py      # 指数数据下载
│   ├── full_download_1990.py      # 完整数据下载
│   ├── start_web_app.sh          # Web应用启动脚本
│   └── start_interactive_chart.sh # 交互式图表启动脚本
├── 🌐 Web前端
│   ├── templates/index.html       # 主页面模板
│   ├── static/css/style.css      # 样式文件
│   └── static/js/app.js          # 前端JavaScript
├── 💾 数据存储
│   └── output/
│       ├── kline_data/           # K线数据库和进度文件
│       └── index_data/           # 指数数据库
└── 📚 文档
    ├── Web图表应用使用说明.md
    ├── 交互式图表使用说明.md
    ├── 使用说明_K线数据获取.md
    └── 数据更新说明_1990至今.md
```

## 💡 使用示例

### 命令行数据查询
```python
from kline_data_query import KlineDataQuery

query = KlineDataQuery()
# 查询贵州茅台2023年数据
data = query.query_stock_data('600519', '2023-01-01', '2023-12-31')
print(data.head())
```

### Web界面操作
1. 在股票选择框中搜索股票（支持代码或名称）
2. 选择对比指数
3. 设置时间范围（可选）
4. 点击"生成交互式图表"
5. 使用鼠标或触摸板进行交互操作

## 🔧 配置说明

### 数据库配置
- K线数据: `output/kline_data/a_share_klines.db`
- 指数数据: `output/index_data/major_indices.db`
- 支持SQLite，无需额外配置

### 网络配置
- 自动处理代理问题
- 内置重试机制
- 支持断点续传

## 📊 数据说明

### K线数据字段
- `date`: 交易日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `amount`: 成交额

### 支持的指数
- 上证指数
- 深证成指
- 创业板指
- 科创50
- 中小板指
- 等更多指数...

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [AKShare](https://github.com/akfamily/akshare) - 优秀的金融数据接口
- [Plotly.js](https://plotly.com/javascript/) - 强大的图表库
- [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架

---

⭐ 如果这个项目对您有帮助，请给个Star支持一下！
