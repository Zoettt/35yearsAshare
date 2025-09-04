# 📊 数据文件设置说明

## 🚨 重要说明

由于数据库文件过大（约2.3GB），无法直接上传到GitHub。您需要在本地生成数据文件。

## 📂 数据文件结构

```
output/
├── kline_data/
│   ├── a_share_klines.db          # K线数据库（~2.3GB）
│   └── download_progress.json     # 下载进度文件
└── index_data/
    └── major_indices.db           # 指数数据库（~6MB）
```

## 🚀 数据生成步骤

### 方式一：完整数据下载（推荐）
```bash
# 下载从1990年至今的所有数据
python full_download_1990.py
```

### 方式二：分步下载
```bash
# 1. 下载指数数据（较快，约10分钟）
python run_index_download.py

# 2. 下载K线数据（较慢，可能需要几小时）
python run_kline_download.py
```

## ⏱️ 预计下载时间

- **指数数据**: 约10-20分钟
- **K线数据**: 2-6小时（取决于网络和股票数量）
- **总数据量**: 约2.3GB

## 🔧 下载前准备

1. **激活虚拟环境**：
   ```bash
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **确保网络稳定**：下载过程较长，建议使用稳定网络

## 📋 数据覆盖范围

- **时间范围**: 1990年至今（35年完整数据）
- **股票范围**: 所有A股股票（约5000+只）
- **指数范围**: 主要股票指数（上证、深证、创业板等）
- **更新频率**: 可定期重新运行脚本更新数据

## 🛠️ 故障排除

### 下载中断
- 脚本支持断点续传，重新运行即可继续
- 进度保存在 `download_progress.json` 中

### 网络问题
- 脚本内置网络重试机制
- 如遇代理问题，脚本会自动处理

### 数据验证
下载完成后可以检查：
```bash
# 检查数据库文件
ls -lh output/kline_data/a_share_klines.db
ls -lh output/index_data/major_indices.db

# 简单数据查询测试
python -c "
from kline_data_query import KlineDataQuery
query = KlineDataQuery()
print('数据库连接正常:', query.check_database())
"
```

## 💡 提示

- 首次运行建议选择夜间进行，避免影响日常使用
- 下载完成后即可正常使用Web界面和所有功能
- 数据文件生成后会自动被Git忽略，不会意外上传
