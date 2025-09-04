#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主要指数数据获取器
获取A股、港股、美股主要指数的历史数据
"""


# 网络修复补丁
import os
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 清除代理设置
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if proxy_var in os.environ:
        del os.environ[proxy_var]

# 修补requests
original_request = requests.Session.request
def patched_request(self, *args, **kwargs):
    kwargs.setdefault('proxies', {})
    kwargs.setdefault('verify', False)
    return original_request(self, *args, **kwargs)
requests.Session.request = patched_request

import akshare as ak
import pandas as pd
import numpy as np
import sqlite3
import os
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class MajorIndexFetcher:
    def __init__(self, start_date="1990-01-01"):
        self.start_date = start_date
        self.output_dir = "output/index_data"
        self.db_path = os.path.join(self.output_dir, "major_indices.db")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 指数配置
        self.index_config = {
            # A股主要指数
            "A股指数": {
                "上证指数": {"symbol": "000001", "source": "sina", "name": "上证指数"},
                "深证成指": {"symbol": "399001", "source": "sina", "name": "深证成指"},
                "创业板指": {"symbol": "399006", "source": "sina", "name": "创业板指"},
                "科创50": {"symbol": "000688", "source": "sina", "name": "科创50"},
                "上证50": {"symbol": "000016", "source": "sina", "name": "上证50"},
                "沪深300": {"symbol": "000300", "source": "sina", "name": "沪深300"},
                "北证50": {"symbol": "899050", "source": "sina", "name": "北证50"},
            },
            # 港股指数
            "港股指数": {
                "恒生指数": {"symbol": "HSI", "source": "investing", "name": "恒生指数"},
                "国企指数": {"symbol": "HSCEI", "source": "investing", "name": "国企指数"},
                "恒生科技指数": {"symbol": "HSTECH", "source": "investing", "name": "恒生科技指数"},
            },
            # 美股指数
            "美股指数": {
                "道琼斯指数": {"symbol": "DJI", "source": "investing", "name": "道琼斯指数"},
                "纳斯达克指数": {"symbol": "IXIC", "source": "investing", "name": "纳斯达克指数"},
                "标普500指数": {"symbol": "SPX", "source": "investing", "name": "标普500指数"},
            }
        }
        
        self.downloaded_count = 0
        self.failed_count = 0
        self.failed_indices = []
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('major_index_fetcher.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建指数数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS index_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT,
                    symbol TEXT,
                    market TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    amount REAL,
                    UNIQUE(index_name, date)
                )
            ''')
            
            # 创建指数信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS index_info (
                    index_name TEXT PRIMARY KEY,
                    symbol TEXT,
                    market TEXT,
                    last_update TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_index_date ON index_data(index_name, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON index_data(date)')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ 数据库初始化完成: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 数据库初始化失败: {str(e)}")
            raise
    
    def get_a_share_index_data(self, symbol, index_name):
        """获取A股指数数据"""
        try:
            self.logger.info(f"正在获取 {index_name} ({symbol}) 数据...")
            
            # 使用不同的接口尝试获取数据，优先使用支持指定日期范围的历史数据API
            df = None
            
            # 方法1: 使用index_zh_a_hist获取指数历史数据（优先方法，支持日期范围）
            try:
                df = ak.index_zh_a_hist(
                    symbol=symbol,
                    period="daily", 
                    start_date=self.start_date.replace("-", ""),
                    end_date=datetime.now().strftime("%Y%m%d")
                )
                if df is not None and not df.empty:
                    self.logger.info(f"  方法1成功: 使用index_zh_a_hist获取到 {len(df)} 条数据")
                
            except Exception as e1:
                self.logger.warning(f"  方法1失败: {str(e1)}")
                
                # 方法2: 使用stock_zh_index_daily获取指数数据
                try:
                    if symbol.startswith('000'):  # 上交所指数
                        df = ak.stock_zh_index_daily(symbol=f"sh{symbol}")
                    elif symbol.startswith('399'):  # 深交所指数  
                        df = ak.stock_zh_index_daily(symbol=f"sz{symbol}")
                    elif symbol.startswith('899'):  # 北交所指数
                        df = ak.stock_zh_index_daily(symbol=f"bj{symbol}")
                    else:
                        df = ak.stock_zh_index_daily(symbol=symbol)
                        
                    if df is not None and not df.empty:
                        self.logger.info(f"  方法2成功: 使用stock_zh_index_daily获取到 {len(df)} 条数据")
                        
                except Exception as e2:
                    self.logger.warning(f"  方法2失败: {str(e2)}")
                    
                    # 方法3: 使用stock_zh_index_daily_em
                    try:
                        df = ak.stock_zh_index_daily_em(symbol=symbol)
                        if df is not None and not df.empty:
                            self.logger.info(f"  方法3成功: 使用stock_zh_index_daily_em获取到 {len(df)} 条数据")
                    except Exception as e3:
                        self.logger.warning(f"  方法3失败: {str(e3)}")
            
            if df is not None and not df.empty:
                # 标准化列名
                df = self.standardize_columns(df)
                
                # 筛选日期范围
                start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
                df['date'] = pd.to_datetime(df['date'])
                df = df[df['date'] >= start_date]
                
                # 按日期排序
                df = df.sort_values('date')
                
                self.logger.info(f"  ✅ {index_name}: 获取到 {len(df)} 条数据")
                return df, "A股指数"
            else:
                self.logger.error(f"  ❌ {index_name}: 未获取到数据")
                return None, None
                
        except Exception as e:
            self.logger.error(f"  ❌ {index_name}: 获取失败 - {str(e)}")
            return None, None
    
    def get_hk_index_data(self, symbol, index_name):
        """获取港股指数数据"""
        try:
            self.logger.info(f"正在获取 {index_name} ({symbol}) 数据...")
            
            df = None
            
            # 方法1: 使用index_investing_global
            try:
                # 恒生指数系列的映射
                hk_symbol_map = {
                    "HSI": "恒生指数",
                    "HSCEI": "恒生国企指数", 
                    "HSTECH": "恒生科技指数"
                }
                
                if symbol in hk_symbol_map:
                    df = ak.index_investing_global(
                        country="香港",
                        index=hk_symbol_map[symbol],
                        period="日线",
                        start_date=self.start_date,
                        end_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    
            except Exception as e1:
                self.logger.warning(f"  方法1失败: {str(e1)}")
                
                # 方法2: 使用stock_hk_index_daily_em
                try:
                    symbol_map = {
                        "HSI": "01", 
                        "HSCEI": "02",
                        "HSTECH": "03"
                    }
                    if symbol in symbol_map:
                        df = ak.stock_hk_index_daily_em(symbol=symbol_map[symbol])
                except Exception as e2:
                    self.logger.warning(f"  方法2失败: {str(e2)}")
            
            if df is not None and not df.empty:
                # 标准化列名
                df = self.standardize_columns(df)
                
                # 筛选日期范围
                start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
                df['date'] = pd.to_datetime(df['date'])
                df = df[df['date'] >= start_date]
                
                # 按日期排序
                df = df.sort_values('date')
                
                self.logger.info(f"  ✅ {index_name}: 获取到 {len(df)} 条数据")
                return df, "港股指数"
            else:
                self.logger.error(f"  ❌ {index_name}: 未获取到数据")
                return None, None
                
        except Exception as e:
            self.logger.error(f"  ❌ {index_name}: 获取失败 - {str(e)}")
            return None, None
    
    def get_us_index_data(self, symbol, index_name):
        """获取美股指数数据"""
        try:
            self.logger.info(f"正在获取 {index_name} ({symbol}) 数据...")
            
            df = None
            
            # 方法1: 使用index_investing_global
            try:
                us_symbol_map = {
                    "DJI": "道琼斯工业平均指数",
                    "IXIC": "纳斯达克综合指数",
                    "SPX": "标准普尔500指数"
                }
                
                if symbol in us_symbol_map:
                    df = ak.index_investing_global(
                        country="美国",
                        index=us_symbol_map[symbol],
                        period="日线",
                        start_date=self.start_date,
                        end_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    
            except Exception as e1:
                self.logger.warning(f"  方法1失败: {str(e1)}")
                
                # 方法2: 使用stock_us_index_daily
                try:
                    df = ak.stock_us_index_daily(symbol=symbol)
                except Exception as e2:
                    self.logger.warning(f"  方法2失败: {str(e2)}")
            
            if df is not None and not df.empty:
                # 标准化列名
                df = self.standardize_columns(df)
                
                # 筛选日期范围
                start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
                df['date'] = pd.to_datetime(df['date'])
                df = df[df['date'] >= start_date]
                
                # 按日期排序
                df = df.sort_values('date')
                
                self.logger.info(f"  ✅ {index_name}: 获取到 {len(df)} 条数据")
                return df, "美股指数"
            else:
                self.logger.error(f"  ❌ {index_name}: 未获取到数据")
                return None, None
                
        except Exception as e:
            self.logger.error(f"  ❌ {index_name}: 获取失败 - {str(e)}")
            return None, None
    
    def standardize_columns(self, df):
        """标准化数据列名"""
        # 可能的列名映射
        column_mapping = {
            # 日期列
            '日期': 'date', 'Date': 'date', 'date': 'date', '时间': 'date',
            # 开盘价列
            '开盘': 'open', '开盘价': 'open', 'Open': 'open', 'open': 'open',
            # 最高价列  
            '最高': 'high', '最高价': 'high', 'High': 'high', 'high': 'high',
            # 最低价列
            '最低': 'low', '最低价': 'low', 'Low': 'low', 'low': 'low',
            # 收盘价列
            '收盘': 'close', '收盘价': 'close', 'Close': 'close', 'close': 'close',
            # 成交量列
            '成交量': 'volume', 'Volume': 'volume', 'volume': 'volume', 'vol': 'volume',
            # 成交额列
            '成交额': 'amount', 'Amount': 'amount', 'amount': 'amount', '成交金额': 'amount'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保必需的列存在
        required_columns = ['date', 'open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                if col == 'date' and '日期' in df.columns:
                    df['date'] = df['日期']
                elif col in ['open', 'high', 'low', 'close']:
                    # 如果缺少OHLC数据，设为收盘价
                    if 'close' in df.columns:
                        df[col] = df['close']
                    else:
                        df[col] = np.nan
        
        # 设置默认值
        if 'volume' not in df.columns:
            df['volume'] = 0
        if 'amount' not in df.columns:
            df['amount'] = 0.0
            
        return df
    
    def save_to_database(self, df, index_name, symbol, market):
        """保存数据到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 准备数据
            df_copy = df.copy()
            df_copy['index_name'] = index_name
            df_copy['symbol'] = symbol
            df_copy['market'] = market
            df_copy['date'] = df_copy['date'].dt.strftime('%Y-%m-%d')
            
            # 选择需要的列
            columns = ['index_name', 'symbol', 'market', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount']
            df_save = df_copy[columns]
            
            # 插入数据，忽略重复
            df_save.to_sql('index_data', conn, if_exists='append', index=False)
            
            # 更新指数信息
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO index_info (index_name, symbol, market, last_update)
                VALUES (?, ?, ?, ?)
            ''', (index_name, symbol, market, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"  💾 {index_name}: 已保存 {len(df_save)} 条记录到数据库")
            return True
            
        except Exception as e:
            self.logger.error(f"  ❌ {index_name}: 保存数据库失败 - {str(e)}")
            return False
    
    def download_index_data(self, market_name, index_name, config):
        """下载单个指数数据"""
        symbol = config['symbol']
        
        try:
            # 根据市场类型调用不同的获取函数
            if market_name == "A股指数":
                df, market = self.get_a_share_index_data(symbol, index_name)
            elif market_name == "港股指数":
                df, market = self.get_hk_index_data(symbol, index_name)
            elif market_name == "美股指数":
                df, market = self.get_us_index_data(symbol, index_name)
            else:
                self.logger.error(f"❌ 未知市场类型: {market_name}")
                return False
            
            if df is not None and market is not None:
                # 保存到数据库
                if self.save_to_database(df, index_name, symbol, market):
                    self.downloaded_count += 1
                    return True
            
            self.failed_count += 1
            self.failed_indices.append(f"{index_name} ({symbol})")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ {index_name}: 下载失败 - {str(e)}")
            self.failed_count += 1
            self.failed_indices.append(f"{index_name} ({symbol})")
            return False
    
    def download_all_indices(self):
        """下载所有指数数据"""
        self.logger.info("🚀 开始下载主要指数数据...")
        self.logger.info("=" * 80)
        
        # 初始化数据库
        self.init_database()
        
        # 统计信息
        total_indices = sum(len(indices) for indices in self.index_config.values())
        self.logger.info(f"📊 计划下载 {total_indices} 个指数的数据")
        self.logger.info(f"📅 数据时间范围: {self.start_date} 至今")
        self.logger.info("-" * 80)
        
        # 逐个市场下载
        for market_name, indices in self.index_config.items():
            self.logger.info(f"\n📈 正在处理 {market_name} ({len(indices)}个指数)")
            self.logger.info("-" * 50)
            
            for index_name, config in indices.items():
                self.download_index_data(market_name, index_name, config)
        
        # 生成下载报告
        self.generate_download_report()
        
    def generate_download_report(self):
        """生成下载报告"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📋 下载完成统计")
        self.logger.info("=" * 80)
        
        total_indices = sum(len(indices) for indices in self.index_config.values())
        
        self.logger.info(f"✅ 成功下载: {self.downloaded_count} 个指数")
        self.logger.info(f"❌ 下载失败: {self.failed_count} 个指数")
        self.logger.info(f"📊 成功率: {(self.downloaded_count/total_indices)*100:.1f}%")
        
        if self.failed_indices:
            self.logger.info("\n❌ 失败的指数:")
            for failed in self.failed_indices:
                self.logger.info(f"  - {failed}")
        
        # 数据库统计
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总记录数
            cursor.execute("SELECT COUNT(*) FROM index_data")
            total_records = cursor.fetchone()[0]
            
            # 按指数统计
            cursor.execute("""
                SELECT index_name, COUNT(*) as record_count 
                FROM index_data 
                GROUP BY index_name 
                ORDER BY record_count DESC
            """)
            index_stats = cursor.fetchall()
            
            # 日期范围
            cursor.execute("SELECT MIN(date), MAX(date) FROM index_data")
            date_range = cursor.fetchone()
            
            conn.close()
            
            self.logger.info(f"\n💾 数据库统计:")
            self.logger.info(f"  - 总记录数: {total_records:,} 条")
            self.logger.info(f"  - 数据时间范围: {date_range[0]} 至 {date_range[1]}")
            self.logger.info(f"  - 数据库文件: {self.db_path}")
            
            if index_stats:
                self.logger.info(f"\n📊 各指数数据量:")
                for index_name, count in index_stats:
                    self.logger.info(f"  - {index_name}: {count:,} 条")
                    
        except Exception as e:
            self.logger.error(f"❌ 统计数据库信息失败: {str(e)}")
        
        # 保存报告到文件
        self.save_report_to_file()
    
    def save_report_to_file(self):
        """保存报告到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.output_dir, f"download_report_{timestamp}.txt")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("主要指数数据下载报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("📊 下载统计:\n")
                total_indices = sum(len(indices) for indices in self.index_config.values())
                f.write(f"  - 计划下载: {total_indices} 个指数\n")
                f.write(f"  - 成功下载: {self.downloaded_count} 个指数\n")
                f.write(f"  - 下载失败: {self.failed_count} 个指数\n")
                f.write(f"  - 成功率: {(self.downloaded_count/total_indices)*100:.1f}%\n\n")
                
                f.write("📈 指数列表:\n")
                for market_name, indices in self.index_config.items():
                    f.write(f"\n{market_name}:\n")
                    for index_name, config in indices.items():
                        status = "✅" if index_name not in [x.split(" (")[0] for x in self.failed_indices] else "❌"
                        f.write(f"  {status} {index_name} ({config['symbol']})\n")
                
                if self.failed_indices:
                    f.write(f"\n❌ 失败列表:\n")
                    for failed in self.failed_indices:
                        f.write(f"  - {failed}\n")
                
                f.write(f"\n💾 数据库文件: {self.db_path}\n")
                f.write(f"📅 数据时间范围: {self.start_date} 至今\n")
            
            self.logger.info(f"📄 下载报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存报告失败: {str(e)}")
    
    def export_to_csv(self, split_by_index=True):
        """导出数据为CSV格式"""
        try:
            self.logger.info("\n📤 开始导出CSV文件...")
            
            conn = sqlite3.connect(self.db_path)
            
            if split_by_index:
                # 按指数分别导出
                csv_dir = os.path.join(self.output_dir, "csv_export")
                os.makedirs(csv_dir, exist_ok=True)
                
                # 获取所有指数列表
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT index_name FROM index_data")
                indices = [row[0] for row in cursor.fetchall()]
                
                for index_name in indices:
                    df = pd.read_sql(
                        "SELECT * FROM index_data WHERE index_name = ? ORDER BY date",
                        conn, params=(index_name,)
                    )
                    
                    filename = os.path.join(csv_dir, f"{index_name}.csv")
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    self.logger.info(f"  ✅ {index_name}: {filename}")
                
                self.logger.info(f"📁 CSV文件已保存到: {csv_dir}")
                
            else:
                # 导出到单个文件
                df = pd.read_sql("SELECT * FROM index_data ORDER BY index_name, date", conn)
                filename = os.path.join(self.output_dir, "all_indices_data.csv")
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                self.logger.info(f"📁 所有数据已保存到: {filename}")
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ 导出CSV失败: {str(e)}")
    
    def query_index_data(self, index_name, start_date=None, end_date=None):
        """查询指定指数的数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            sql = "SELECT * FROM index_data WHERE index_name = ?"
            params = [index_name]
            
            if start_date:
                sql += " AND date >= ?"
                params.append(start_date)
                
            if end_date:
                sql += " AND date <= ?"
                params.append(end_date)
            
            sql += " ORDER BY date"
            
            df = pd.read_sql(sql, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 查询数据失败: {str(e)}")
            return None

def main():
    """主函数"""
    print("🚀 主要指数数据获取工具")
    print("=" * 50)
    print("支持的指数:")
    print("  A股: 上证指数、深证成指、创业板指、科创50、上证50、沪深300、北证50")
    print("  港股: 恒生指数、国企指数、恒生科技指数")
    print("  美股: 道琼斯指数、纳斯达克指数、标普500指数")
    print("=" * 50)
    
    # 获取用户配置
    start_date = input("\n📅 请输入起始日期 (格式: YYYY-MM-DD, 默认: 2015-01-01): ").strip()
    if not start_date:
        start_date = "2015-01-01"
    
    # 创建获取器
    fetcher = MajorIndexFetcher(start_date=start_date)
    
    try:
        # 下载所有指数数据
        fetcher.download_all_indices()
        
        # 询问是否导出CSV
        export_csv = input("\n📤 是否导出为CSV文件？[y/n]: ").lower().strip()
        if export_csv == 'y':
            split_files = input("是否按指数分别导出？[y/n]: ").lower().strip()
            fetcher.export_to_csv(split_by_index=(split_files == 'y'))
        
        print("\n🎉 指数数据获取完成！")
        print(f"💾 数据库文件: {fetcher.db_path}")
        print("📊 可以使用其他工具分析这些指数数据")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断下载")
        print("💾 已下载的数据已保存")
    except Exception as e:
        print(f"\n❌ 下载过程出错: {e}")

if __name__ == "__main__":
    main()
