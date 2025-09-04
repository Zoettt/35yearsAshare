#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股历史K线数据获取工具
从2015年1月开始获取所有A股股票的K线数据
支持多种数据源和批量下载
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import LONGBRIDGE_CONFIG

# 完整网络修复补丁
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 清除代理设置
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

# 修补requests - 更彻底的方式
import requests
original_request = requests.request
def patched_request(*args, **kwargs):
    kwargs['proxies'] = {}
    kwargs['verify'] = False
    kwargs['timeout'] = kwargs.get('timeout', 30)
    return original_request(*args, **kwargs)

requests.request = patched_request
requests.get = lambda *args, **kwargs: patched_request('GET', *args, **kwargs)
requests.post = lambda *args, **kwargs: patched_request('POST', *args, **kwargs)

try:
    import akshare as ak
except ImportError:
    print("请先安装 akshare: pip install akshare")
    sys.exit(1)

try:
    import longbridge as lb
    from longbridge.openapi import QuoteContext, Config
    LONGBRIDGE_AVAILABLE = True
except ImportError:
    print("警告: Longbridge SDK 未安装，将仅使用 AKShare 数据源")
    LONGBRIDGE_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('a_share_kline_fetcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AShareKlineFetcher:
    """A股K线数据获取器"""
    
    def __init__(self, start_date="2015-01-01", data_source="akshare"):
        """
        初始化
        Args:
            start_date: 数据开始日期，格式: YYYY-MM-DD
            data_source: 数据源，"akshare" 或 "longbridge" 或 "both"
        """
        self.start_date = start_date
        self.data_source = data_source
        self.quote_ctx = None
        
        # 数据存储目录
        self.data_dir = "output/kline_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 创建SQLite数据库
        self.db_path = os.path.join(self.data_dir, "a_share_klines.db")
        self.init_database()
        
        # 进度追踪
        self.progress_file = os.path.join(self.data_dir, "download_progress.json")
        self.progress = self.load_progress()
        
        # 如果选择longbridge数据源，初始化API
        if data_source in ["longbridge", "both"] and LONGBRIDGE_AVAILABLE:
            self.init_longbridge_api()
        
        # A股股票代码生成规则
        self.stock_ranges = {
            "沪市主板": {
                "patterns": [
                    {"prefix": "600", "start": 600000, "end": 604000, "suffix": ".SH"},
                    {"prefix": "601", "start": 601000, "end": 602000, "suffix": ".SH"},
                    {"prefix": "603", "start": 603000, "end": 604000, "suffix": ".SH"},
                    {"prefix": "605", "start": 605000, "end": 606000, "suffix": ".SH"},
                ]
            },
            "科创板": {
                "patterns": [
                    {"prefix": "688", "start": 688000, "end": 689000, "suffix": ".SH"}
                ]
            },
            "深市主板": {
                "patterns": [
                    {"prefix": "000", "start": 1, "end": 3000, "suffix": ".SZ"}
                ]
            },
            "中小板": {
                "patterns": [
                    {"prefix": "002", "start": 1, "end": 1000, "suffix": ".SZ"}
                ]
            },
            "创业板": {
                "patterns": [
                    {"prefix": "300", "start": 300001, "end": 301000, "suffix": ".SZ"}
                ]
            }
        }
    
    def init_database(self):
        """初始化SQLite数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建股票信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_info (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    market TEXT,
                    list_date TEXT,
                    last_update TEXT
                )
            """)
            
            # 创建K线数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kline_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    amount REAL,
                    UNIQUE(symbol, date)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol_date ON kline_data(symbol, date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON kline_data(date)")
            
            conn.commit()
            conn.close()
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    def init_longbridge_api(self):
        """初始化长桥API连接"""
        try:
            config = Config(
                app_key=LONGBRIDGE_CONFIG["app_key"],
                app_secret=LONGBRIDGE_CONFIG["app_secret"],
                access_token=LONGBRIDGE_CONFIG["access_token"]
            )
            self.quote_ctx = QuoteContext(config)
            logger.info("长桥API连接成功")
            return True
        except Exception as e:
            logger.error(f"长桥API连接失败: {e}")
            return False
    
    def load_progress(self) -> Dict:
        """加载下载进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"downloaded_symbols": [], "failed_symbols": [], "last_update": ""}
    
    def save_progress(self):
        """保存下载进度"""
        try:
            self.progress["last_update"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
    
    def generate_stock_symbols(self) -> List[str]:
        """生成所有可能的A股股票代码"""
        symbols = []
        
        for market_name, market_config in self.stock_ranges.items():
            for pattern in market_config["patterns"]:
                prefix = pattern["prefix"]
                start = pattern["start"]
                end = pattern["end"]
                suffix = pattern["suffix"]
                
                if prefix == "000":  # 深市主板特殊处理
                    for i in range(start, end):
                        symbols.append(f"{i:06d}{suffix}")
                elif prefix == "002":  # 中小板特殊处理
                    for i in range(start, end):
                        symbols.append(f"00{i:04d}{suffix}")
                else:
                    for i in range(start, end):
                        symbols.append(f"{i:06d}{suffix}")
        
        logger.info(f"生成了 {len(symbols)} 个潜在股票代码")
        return symbols
    
    def get_valid_stocks_akshare(self) -> List[Dict[str, str]]:
        """使用AKShare获取有效股票列表"""
        try:
            logger.info("正在从AKShare获取A股股票列表...")
            
            # 获取A股股票实时数据
            stock_list = ak.stock_zh_a_spot()
            
            if stock_list is None or stock_list.empty:
                logger.error("未能获取到股票列表")
                return []
            
            valid_stocks = []
            for _, row in stock_list.iterrows():
                symbol = row.get('代码', '')
                name = row.get('名称', '')
                
                if symbol and name:
                    # 标准化股票代码格式
                    if len(symbol) == 6 and symbol.isdigit():
                        if symbol.startswith(('000', '001', '002', '003', '300')):
                            symbol += '.SZ'
                        elif symbol.startswith(('600', '601', '603', '605', '688')):
                            symbol += '.SH'
                    
                    valid_stocks.append({
                        'symbol': symbol,
                        'name': name,
                        'market': self.get_market_type(symbol)
                    })
            
            logger.info(f"获取到 {len(valid_stocks)} 只有效股票")
            return valid_stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_market_type(self, symbol: str) -> str:
        """判断股票所属市场"""
        code = symbol[:6]
        if symbol.endswith('.SH'):
            if code.startswith(('600', '601', '603', '605')):
                return '沪市主板'
            elif code.startswith('688'):
                return '科创板'
            else:
                return '沪市其他'
        elif symbol.endswith('.SZ'):
            if code.startswith('000'):
                return '深市主板'
            elif code.startswith('002'):
                return '中小板'
            elif code.startswith('300'):
                return '创业板'
            else:
                return '深市其他'
        return '未知市场'
    
    def get_kline_data_akshare(self, symbol: str, start_date: str = None) -> Optional[pd.DataFrame]:
        """使用AKShare获取单只股票的K线数据"""
        try:
            if start_date is None:
                start_date = self.start_date
            
            # 为AKShare添加市场前缀，处理股票代码格式
            stock_code = symbol.split('.')[0]  # 去掉后缀
            
            if symbol.startswith('bj'):
                # 北交所股票，使用原代码
                ak_symbol = stock_code
            elif symbol.startswith('sh'):
                # 已带sh前缀的上海股票
                ak_symbol = stock_code
            elif symbol.startswith('sz'):
                # 已带sz前缀的深圳股票
                ak_symbol = stock_code
            elif stock_code.startswith('6'):
                # 上海股票（6开头）
                ak_symbol = 'sh' + stock_code
            else:
                # 深圳股票（0、3开头等）
                ak_symbol = 'sz' + stock_code
            
            # 转换日期格式
            start_str = start_date.replace('-', '')
            end_str = datetime.now().strftime('%Y%m%d')
            
            logger.debug(f"正在获取 {symbol} (akshare: {ak_symbol}) 从 {start_date} 的K线数据...")
            
            # 使用AKShare获取历史数据 - 使用stock_zh_a_daily（稳定可用）
            df = ak.stock_zh_a_daily(
                symbol=ak_symbol,
                start_date=start_str,
                end_date=end_str,
                adjust="qfq"  # 前复权
            )
            
            if df is None or df.empty:
                return None
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high', 
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            # 添加股票代码列
            df['symbol'] = symbol
            
            # 确保日期格式
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            # 过滤指定日期之后的数据
            df = df[df['date'] >= start_date]
            
            logger.debug(f"成功获取 {symbol} 数据 {len(df)} 条")
            return df
            
        except Exception as e:
            logger.debug(f"获取 {symbol} K线数据失败: {e}")
            return None
    
    def save_kline_to_db(self, df: pd.DataFrame):
        """保存K线数据到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 使用INSERT OR REPLACE避免重复数据
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO kline_data 
                    (symbol, date, open, high, low, close, volume, amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['symbol'], row['date'], row['open'], row['high'],
                    row['low'], row['close'], row['volume'], row['amount']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {e}")
    
    def save_stock_info_to_db(self, stocks_info: List[Dict[str, str]]):
        """保存股票信息到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            for stock in stocks_info:
                conn.execute("""
                    INSERT OR REPLACE INTO stock_info 
                    (symbol, name, market, last_update)
                    VALUES (?, ?, ?, ?)
                """, (
                    stock['symbol'], stock['name'], stock['market'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存股票信息失败: {e}")
    
    def download_single_stock(self, stock_info: Dict[str, str]) -> bool:
        """下载单只股票的K线数据"""
        symbol = stock_info['symbol']
        
        # 检查是否已经下载过
        if symbol in self.progress.get('downloaded_symbols', []):
            logger.debug(f"{symbol} 已下载，跳过")
            return True
        
        try:
            # 获取K线数据，传递正确的起始日期
            df = self.get_kline_data_akshare(symbol, self.start_date)
            
            if df is not None and not df.empty:
                # 保存到数据库
                self.save_kline_to_db(df)
                
                # 更新进度
                if 'downloaded_symbols' not in self.progress:
                    self.progress['downloaded_symbols'] = []
                self.progress['downloaded_symbols'].append(symbol)
                
                logger.info(f"✅ {symbol} ({stock_info['name']}) 下载完成，共 {len(df)} 条数据")
                return True
            else:
                logger.warning(f"❌ {symbol} ({stock_info['name']}) 无数据")
                if 'failed_symbols' not in self.progress:
                    self.progress['failed_symbols'] = []
                self.progress['failed_symbols'].append(symbol)
                return False
                
        except Exception as e:
            logger.error(f"❌ {symbol} ({stock_info['name']}) 下载失败: {e}")
            if 'failed_symbols' not in self.progress:
                self.progress['failed_symbols'] = []
            self.progress['failed_symbols'].append(symbol)
            return False
    
    def download_all_stocks(self, max_workers: int = 5, batch_size: int = 50):
        """下载所有股票的K线数据"""
        logger.info(f"开始下载A股K线数据，从 {self.start_date} 开始...")
        
        # 获取有效股票列表
        valid_stocks = self.get_valid_stocks_akshare()
        if not valid_stocks:
            logger.error("未能获取有效股票列表，退出")
            return
        
        # 保存股票信息到数据库
        self.save_stock_info_to_db(valid_stocks)
        
        total_stocks = len(valid_stocks)
        logger.info(f"共需下载 {total_stocks} 只股票的数据")
        
        # 按批次处理
        for i in range(0, total_stocks, batch_size):
            batch_stocks = valid_stocks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_stocks + batch_size - 1) // batch_size
            
            logger.info(f"处理第 {batch_num}/{total_batches} 批，股票数: {len(batch_stocks)}")
            
            # 使用线程池下载
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.download_single_stock, stock) 
                          for stock in batch_stocks]
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    if completed % 10 == 0:
                        logger.info(f"  批次进度: {completed}/{len(batch_stocks)}")
            
            # 每批次后保存进度
            self.save_progress()
            
            # 添加延迟，避免过于频繁的请求
            time.sleep(2)
        
        logger.info("所有股票数据下载完成！")
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """生成下载汇总报告"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 统计数据
            cursor = conn.cursor()
            
            # 股票数量统计
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM kline_data")
            total_stocks = cursor.fetchone()[0]
            
            # 总记录数
            cursor.execute("SELECT COUNT(*) FROM kline_data") 
            total_records = cursor.fetchone()[0]
            
            # 日期范围
            cursor.execute("SELECT MIN(date), MAX(date) FROM kline_data")
            date_range = cursor.fetchone()
            
            # 按市场统计
            cursor.execute("""
                SELECT s.market, COUNT(DISTINCT k.symbol) 
                FROM stock_info s 
                JOIN kline_data k ON s.symbol = k.symbol 
                GROUP BY s.market
            """)
            market_stats = cursor.fetchall()
            
            conn.close()
            
            # 生成报告
            report = f"""
=== A股K线数据下载汇总报告 ===
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 数据统计:
  - 股票总数: {total_stocks} 只
  - 数据记录总数: {total_records:,} 条
  - 数据日期范围: {date_range[0]} 至 {date_range[1]}
  - 平均每只股票: {total_records//max(total_stocks,1):,} 条记录

📈 市场分布:
"""
            for market, count in market_stats:
                report += f"  - {market}: {count} 只股票\n"
            
            report += f"""
💾 数据存储:
  - 数据库文件: {self.db_path}
  - 文件大小: {os.path.getsize(self.db_path)/1024/1024:.2f} MB

✅ 下载成功: {len(self.progress.get('downloaded_symbols', []))} 只
❌ 下载失败: {len(self.progress.get('failed_symbols', []))} 只

=== 报告结束 ===
"""
            
            # 保存报告
            report_file = os.path.join(self.data_dir, f"download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(report)
            logger.info(f"汇总报告已保存到: {report_file}")
            
        except Exception as e:
            logger.error(f"生成汇总报告失败: {e}")
    
    def export_to_csv(self, output_dir: str = None, split_by_symbol: bool = False):
        """导出数据到CSV文件"""
        if output_dir is None:
            output_dir = os.path.join(self.data_dir, "csv_export")
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            if split_by_symbol:
                # 按股票分别导出
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT symbol FROM kline_data ORDER BY symbol")
                symbols = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"开始导出 {len(symbols)} 只股票的CSV文件...")
                
                for i, symbol in enumerate(symbols):
                    if i % 100 == 0:
                        logger.info(f"导出进度: {i}/{len(symbols)}")
                    
                    df = pd.read_sql_query(
                        "SELECT * FROM kline_data WHERE symbol = ? ORDER BY date",
                        conn, params=(symbol,)
                    )
                    
                    # 清理文件名中的特殊字符
                    safe_symbol = symbol.replace('.', '_')
                    filename = os.path.join(output_dir, f"{safe_symbol}.csv")
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                logger.info(f"CSV文件导出完成，保存在: {output_dir}")
            else:
                # 导出全部数据到单个文件
                logger.info("导出全部数据到单个CSV文件...")
                df = pd.read_sql_query(
                    "SELECT * FROM kline_data ORDER BY symbol, date",
                    conn
                )
                
                filename = os.path.join(output_dir, f"all_a_share_klines_{datetime.now().strftime('%Y%m%d')}.csv")
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                logger.info(f"CSV文件已保存到: {filename}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"导出CSV文件失败: {e}")
    
    def query_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """查询指定股票的K线数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM kline_data WHERE symbol = ?"
            params = [symbol]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " ORDER BY date"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"查询股票数据失败: {e}")
            return pd.DataFrame()

def main():
    """主函数"""
    print("🚀 A股历史K线数据获取工具")
    print("=" * 50)
    
    # 配置参数
    start_date = "2015-01-01"  # 起始日期
    max_workers = 3  # 并发下载线程数
    batch_size = 50  # 批次大小
    
    print(f"📅 数据起始日期: {start_date}")
    print(f"🔄 并发线程数: {max_workers}")
    print(f"📦 批次大小: {batch_size}")
    print("=" * 50)
    
    # 创建数据获取器
    fetcher = AShareKlineFetcher(start_date=start_date)
    
    # 开始下载
    try:
        fetcher.download_all_stocks(max_workers=max_workers, batch_size=batch_size)
        
        print("\n🎉 数据下载完成！")
        print(f"📁 数据库文件: {fetcher.db_path}")
        
        # 询问是否导出CSV
        export_choice = input("\n是否导出为CSV文件？(y/n): ").lower().strip()
        if export_choice == 'y':
            split_choice = input("是否按股票分别导出？(y/n): ").lower().strip()
            fetcher.export_to_csv(split_by_symbol=(split_choice == 'y'))
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断下载")
        fetcher.save_progress()
        print("进度已保存，可以稍后继续")
    except Exception as e:
        logger.error(f"下载过程出错: {e}")
        fetcher.save_progress()

if __name__ == "__main__":
    main()
