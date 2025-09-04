# A股K线数据获取工具使用说明

## 功能介绍

这个工具可以获取A股市场从1990年1月以来所有股票的历史K线数据，包括：

- 📈 **全市场覆盖**: 沪市主板、深市主板、中小板、创业板、科创板
- 📅 **超长期历史数据**: 从1990年1月开始的35年完整K线数据
- 💾 **多种存储方式**: SQLite数据库 + CSV导出
- 🔄 **断点续传**: 支持中断后继续下载
- 📊 **进度追踪**: 实时显示下载进度和统计信息

## 快速开始

### 1. 安装依赖

```bash
pip install akshare pandas numpy
```

### 2. 运行脚本

```bash
python a_share_kline_fetcher.py
```

### 3. 数据输出

运行完成后，数据将保存在以下位置：

- **数据库文件**: `output/kline_data/a_share_klines.db`
- **CSV文件**: `output/kline_data/csv_export/` (可选)
- **进度文件**: `output/kline_data/download_progress.json`
- **日志文件**: `a_share_kline_fetcher.log`

## 数据结构

### K线数据表 (kline_data)
| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | TEXT | 股票代码 (如: 000001.SZ) |
| date | TEXT | 日期 (YYYY-MM-DD) |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 (前复权) |
| volume | INTEGER | 成交量 |
| amount | REAL | 成交额 |

### 股票信息表 (stock_info)
| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | TEXT | 股票代码 |
| name | TEXT | 股票名称 |
| market | TEXT | 所属市场 |
| last_update | TEXT | 最后更新时间 |

## 高级用法

### 1. 自定义起始日期

```python
from a_share_kline_fetcher import AShareKlineFetcher

# 从2020年开始获取数据
fetcher = AShareKlineFetcher(start_date="2020-01-01")
fetcher.download_all_stocks()
```

### 2. 查询特定股票数据

```python
# 查询平安银行的数据
df = fetcher.query_stock_data("000001.SZ", start_date="2023-01-01")
print(df.head())
```

### 3. 导出数据

```python
# 导出全部数据到一个CSV文件
fetcher.export_to_csv(split_by_symbol=False)

# 按股票分别导出CSV文件
fetcher.export_to_csv(split_by_symbol=True)
```

### 4. 调整并发设置

```python
# 调整并发线程数和批次大小
fetcher.download_all_stocks(max_workers=5, batch_size=100)
```

## 重要说明

### ⏱️ 下载时间预估
- **全市场股票数量**: 约4000-5000只
- **历史数据量**: 每只股票约2500条记录 (10年数据)
- **预计总时间**: 2-4小时 (取决于网络状况)
- **数据库大小**: 约500MB-1GB

### 🔄 断点续传
如果下载过程中断，再次运行脚本会自动从上次停止的地方继续，不会重复下载已完成的股票。

### 📊 实时监控
- 查看日志文件了解详细进度
- 查看进度文件了解完成状态
- 数据库中可以实时查询已下载的数据

### ⚠️ 注意事项
1. **网络稳定性**: 建议在网络稳定的环境下运行
2. **磁盘空间**: 确保有足够的磁盘空间（至少2GB）
3. **API限制**: 使用免费的AKShare接口，请合理控制请求频率
4. **数据准确性**: 数据来源于公开接口，仅供参考

## 故障排除

### 常见问题

**Q: 下载速度很慢怎么办？**
A: 可以适当调整 `max_workers` 参数，但不建议超过5，避免过多并发请求。

**Q: 某些股票下载失败怎么办？**
A: 脚本会自动记录失败的股票，可以查看日志了解失败原因。通常是由于股票已退市或数据源暂时不可用。

**Q: 如何更新数据？**
A: 直接重新运行脚本，会自动更新所有股票的最新数据。

**Q: 如何只获取特定市场的股票？**
A: 可以修改 `stock_ranges` 配置，只保留需要的市场配置。

## 数据用途建议

下载的数据可以用于：

- 📈 **技术分析**: 计算各种技术指标
- 🔍 **策略回测**: 验证交易策略效果
- 📊 **统计分析**: 市场相关性、波动率分析
- 🤖 **机器学习**: 价格预测模型训练
- 📋 **投资研究**: 长期趋势分析

## 联系支持

如有问题，请查看：
1. 日志文件中的错误信息
2. GitHub项目页面的文档
3. AKShare官方文档

---

**免责声明**: 本工具仅用于数据获取和学习目的，不构成投资建议。投资有风险，入市需谨慎。
