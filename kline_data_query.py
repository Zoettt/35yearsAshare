#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线数据查询工具
用于查询和分析已下载的A股K线数据
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class KlineDataQuery:
    """K线数据查询工具"""
    
    def __init__(self, db_path: str = "output/kline_data/a_share_klines.db"):
        self.db_path = db_path
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取所有股票列表"""
        query = """
        SELECT s.symbol, s.name, s.market, 
               COUNT(k.date) as data_count,
               MIN(k.date) as start_date,
               MAX(k.date) as end_date
        FROM stock_info s
        LEFT JOIN kline_data k ON s.symbol = k.symbol
        GROUP BY s.symbol, s.name, s.market
        ORDER BY s.symbol
        """
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def query_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """查询指定股票的K线数据"""
        query = "SELECT * FROM kline_data WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            
        return df
    
    def get_market_summary(self) -> pd.DataFrame:
        """获取市场汇总统计"""
        query = """
        SELECT s.market,
               COUNT(DISTINCT s.symbol) as stock_count,
               COUNT(k.date) as total_records,
               MIN(k.date) as earliest_date,
               MAX(k.date) as latest_date
        FROM stock_info s
        LEFT JOIN kline_data k ON s.symbol = k.symbol
        GROUP BY s.market
        ORDER BY stock_count DESC
        """
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def search_stocks(self, keyword: str) -> pd.DataFrame:
        """搜索股票（按名称或代码）"""
        query = """
        SELECT s.symbol, s.name, s.market,
               COUNT(k.date) as data_count
        FROM stock_info s
        LEFT JOIN kline_data k ON s.symbol = k.symbol
        WHERE s.symbol LIKE ? OR s.name LIKE ?
        GROUP BY s.symbol, s.name, s.market
        ORDER BY s.symbol
        """
        
        keyword_pattern = f"%{keyword}%"
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=[keyword_pattern, keyword_pattern])
        conn.close()
        
        return df
    
    def get_stock_statistics(self, symbol: str) -> dict:
        """获取股票统计信息"""
        df = self.query_stock_data(symbol)
        
        if df.empty:
            return {}
        
        stats = {
            '股票代码': symbol,
            '数据记录数': len(df),
            '数据日期范围': f"{df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}",
            '最新价格': df['close'].iloc[-1],
            '最高价格': df['high'].max(),
            '最低价格': df['low'].min(),
            '平均价格': df['close'].mean(),
            '价格标准差': df['close'].std(),
            '总成交量': df['volume'].sum(),
            '平均成交量': df['volume'].mean(),
            '最大单日成交量': df['volume'].max(),
            '总成交额': df['amount'].sum(),
        }
        
        # 计算收益率
        if len(df) > 1:
            total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            stats['总收益率(%)'] = total_return
            
            # 年化收益率
            days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
            if days > 0:
                annual_return = (df['close'].iloc[-1] / df['close'].iloc[0]) ** (365/days) - 1
                stats['年化收益率(%)'] = annual_return * 100
        
        return stats
    
    def plot_price_chart(self, symbol: str, start_date: str = None, end_date: str = None, 
                        save_path: str = None):
        """绘制价格走势图"""
        df = self.query_stock_data(symbol, start_date, end_date)
        
        if df.empty:
            print(f"没有找到 {symbol} 的数据")
            return
        
        # 获取股票名称
        stock_list = self.search_stocks(symbol)
        stock_name = stock_list['name'].iloc[0] if not stock_list.empty else symbol
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[3, 1])
        
        # 价格走势图
        ax1.plot(df['date'], df['close'], label='收盘价', linewidth=1)
        ax1.fill_between(df['date'], df['low'], df['high'], alpha=0.3, label='日内波动范围')
        
        ax1.set_title(f'{symbol} - {stock_name} 价格走势图', fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格 (元)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 成交量图
        ax2.bar(df['date'], df['volume'], alpha=0.6, color='orange', label='成交量')
        ax2.set_ylabel('成交量', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        
        plt.show()
    
    def compare_stocks(self, symbols: List[str], start_date: str = None, end_date: str = None):
        """比较多只股票的表现"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        for symbol in symbols:
            df = self.query_stock_data(symbol, start_date, end_date)
            
            if df.empty:
                print(f"警告: {symbol} 没有数据")
                continue
            
            # 计算归一化价格（以第一天为基准）
            normalized_price = df['close'] / df['close'].iloc[0] * 100
            
            # 获取股票名称
            stock_list = self.search_stocks(symbol)
            stock_name = stock_list['name'].iloc[0] if not stock_list.empty else symbol
            
            ax.plot(df['date'], normalized_price, label=f'{symbol} - {stock_name}', linewidth=2)
        
        ax.set_title('股票表现对比（归一化）', fontsize=14, fontweight='bold')
        ax.set_ylabel('相对表现 (%)', fontsize=12)
        ax.set_xlabel('日期', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def export_stock_data(self, symbol: str, start_date: str = None, end_date: str = None,
                         output_path: str = None):
        """导出股票数据到CSV"""
        df = self.query_stock_data(symbol, start_date, end_date)
        
        if df.empty:
            print(f"没有找到 {symbol} 的数据")
            return None
        
        if output_path is None:
            safe_symbol = symbol.replace('.', '_')
            output_path = f"output/{safe_symbol}_kline_data.csv"
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"数据已导出到: {output_path}")
        
        return output_path

def main():
    """主函数 - 提供交互式查询界面"""
    print("📊 A股K线数据查询工具")
    print("=" * 50)
    
    try:
        query_tool = KlineDataQuery()
        
        while True:
            print("\n🔍 查询选项:")
            print("1. 查看数据库统计")
            print("2. 搜索股票")
            print("3. 查询股票数据")
            print("4. 绘制价格走势图")
            print("5. 股票表现对比")
            print("6. 导出股票数据")
            print("0. 退出")
            
            choice = input("\n请选择 [0-6]: ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            
            elif choice == "1":
                print("\n📈 数据库统计信息:")
                market_summary = query_tool.get_market_summary()
                print(market_summary.to_string(index=False))
                
                # 总计
                total_stocks = market_summary['stock_count'].sum()
                total_records = market_summary['total_records'].sum()
                print(f"\n📊 总计: {total_stocks} 只股票, {total_records:,} 条记录")
            
            elif choice == "2":
                keyword = input("\n请输入搜索关键词 (股票代码或名称): ").strip()
                if keyword:
                    results = query_tool.search_stocks(keyword)
                    if not results.empty:
                        print(f"\n🔍 搜索结果 (共{len(results)}个):")
                        print(results.to_string(index=False))
                    else:
                        print("❌ 没有找到匹配的股票")
            
            elif choice == "3":
                symbol = input("\n请输入股票代码 (如: 000001.SZ): ").strip().upper()
                if symbol:
                    stats = query_tool.get_stock_statistics(symbol)
                    if stats:
                        print(f"\n📊 {symbol} 统计信息:")
                        for key, value in stats.items():
                            if isinstance(value, float):
                                print(f"  {key}: {value:.2f}")
                            else:
                                print(f"  {key}: {value}")
                    else:
                        print("❌ 没有找到该股票的数据")
            
            elif choice == "4":
                symbol = input("\n请输入股票代码 (如: 000001.SZ): ").strip().upper()
                start_date = input("请输入开始日期 (YYYY-MM-DD, 回车跳过): ").strip()
                end_date = input("请输入结束日期 (YYYY-MM-DD, 回车跳过): ").strip()
                
                if symbol:
                    query_tool.plot_price_chart(
                        symbol, 
                        start_date if start_date else None,
                        end_date if end_date else None
                    )
            
            elif choice == "5":
                symbols_input = input("\n请输入股票代码 (用逗号分隔, 如: 000001.SZ,000002.SZ): ").strip()
                if symbols_input:
                    symbols = [s.strip().upper() for s in symbols_input.split(',')]
                    start_date = input("请输入开始日期 (YYYY-MM-DD, 回车跳过): ").strip()
                    end_date = input("请输入结束日期 (YYYY-MM-DD, 回车跳过): ").strip()
                    
                    query_tool.compare_stocks(
                        symbols,
                        start_date if start_date else None,
                        end_date if end_date else None
                    )
            
            elif choice == "6":
                symbol = input("\n请输入股票代码 (如: 000001.SZ): ").strip().upper()
                start_date = input("请输入开始日期 (YYYY-MM-DD, 回车跳过): ").strip()
                end_date = input("请输入结束日期 (YYYY-MM-DD, 回车跳过): ").strip()
                
                if symbol:
                    query_tool.export_stock_data(
                        symbol,
                        start_date if start_date else None,
                        end_date if end_date else None
                    )
            
            else:
                print("❌ 无效选择，请重新输入")
    
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 请先运行数据下载脚本获取K线数据")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")

if __name__ == "__main__":
    main()
