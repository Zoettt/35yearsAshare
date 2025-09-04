#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式股票与指数图表绘制工具
支持从数据库获取股票和指数数据，绘制对比图表
"""

import pandas as pd
import numpy as np
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os
import warnings
warnings.filterwarnings('ignore')

class InteractiveChartPlotter:
    """交互式图表绘制器"""
    
    def __init__(self):
        # 数据库路径
        self.kline_db_path = "/Users/guanjie/Desktop/cursor/longbridge/output/kline_data/a_share_klines.db"
        self.index_db_path = "/Users/guanjie/Desktop/cursor/longbridge/output/index_data/major_indices.db"
        
        # 检查数据库文件
        self.check_databases()
        print("📊 使用 Plotly 交互式图表（支持hover和十字线）")
    

    def check_databases(self):
        """检查数据库文件是否存在"""
        if not os.path.exists(self.kline_db_path):
            print(f"❌ K线数据库不存在: {self.kline_db_path}")
            print("   请先运行 K线数据下载脚本")
            sys.exit(1)
        
        if not os.path.exists(self.index_db_path):
            print(f"❌ 指数数据库不存在: {self.index_db_path}")
            print("   请先运行指数数据下载脚本")
            sys.exit(1)
        
        print("✅ 数据库文件检查通过")
    
    def validate_stock_code(self, code: str) -> str:
        """验证和标准化股票代码"""
        code = code.strip()
        
        # 如果已经是数据库格式（如sh600004, sz000001），直接返回
        if (code.startswith(('sh', 'sz', 'bj')) and len(code) == 8):
            return code.lower()
        
        # 如果是标准格式（如600004.SH），转换为数据库格式
        if '.' in code:
            symbol_part, exchange = code.split('.')
            if exchange.upper() == 'SH':
                return f"sh{symbol_part}"
            elif exchange.upper() == 'SZ':
                return f"sz{symbol_part}"
            elif exchange.upper() == 'BJ':
                return f"bj{symbol_part}"
        
        # 如果是6位数字，自动添加前缀
        if len(code) == 6 and code.isdigit():
            if code.startswith(('000', '001', '002', '003', '300')):
                return f"sz{code}"
            elif code.startswith(('600', '601', '603', '605', '688')):
                return f"sh{code}"
            elif code.startswith(('430', '831', '832', '833', '834', '835', '836', '837', '838', '839')):
                return f"bj{code}"
        
        return code.lower()
    
    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """从K线数据库获取股票数据"""
        try:
            conn = sqlite3.connect(self.kline_db_path)
            
            query = """
            SELECT symbol, date, open, high, low, close, volume, amount
            FROM kline_data 
            WHERE symbol = ?
            ORDER BY date
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                print(f"⚠️ 未找到股票 {symbol} 的数据")
                return pd.DataFrame()
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            
            # 获取股票名称
            stock_name = self.get_stock_name(symbol)
            df['name'] = stock_name
            
            print(f"✅ 获取股票 {symbol} ({stock_name}) 数据: {len(df)} 条")
            return df
            
        except Exception as e:
            print(f"❌ 获取股票数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_name(self, symbol: str) -> str:
        """从K线数据库获取股票名称"""
        try:
            conn = sqlite3.connect(self.kline_db_path)
            
            query = "SELECT name FROM stock_info WHERE symbol = ?"
            result = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if not result.empty:
                return result.iloc[0]['name']
            else:
                return symbol
                
        except Exception:
            return symbol
    
    def get_index_data(self, index_name: str = "上证指数") -> pd.DataFrame:
        """从指数数据库获取指数数据"""
        try:
            conn = sqlite3.connect(self.index_db_path)
            
            query = """
            SELECT index_name, date, open, high, low, close, volume, amount
            FROM index_data 
            WHERE index_name = ?
            ORDER BY date
            """
            
            df = pd.read_sql_query(query, conn, params=(index_name,))
            conn.close()
            
            if df.empty:
                print(f"⚠️ 未找到指数 {index_name} 的数据")
                return pd.DataFrame()
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            
            print(f"✅ 获取指数 {index_name} 数据: {len(df)} 条")
            return df
            
        except Exception as e:
            print(f"❌ 获取指数数据失败: {e}")
            return pd.DataFrame()
    
    def list_available_stocks(self) -> pd.DataFrame:
        """列出数据库中可用的股票"""
        try:
            conn = sqlite3.connect(self.kline_db_path)
            
            query = """
            SELECT s.symbol, s.name, s.market, COUNT(k.date) as data_count
            FROM stock_info s
            LEFT JOIN kline_data k ON s.symbol = k.symbol
            GROUP BY s.symbol, s.name, s.market
            HAVING data_count > 0
            ORDER BY s.symbol
            LIMIT 20
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def list_available_indices(self) -> pd.DataFrame:
        """列出数据库中可用的指数"""
        try:
            conn = sqlite3.connect(self.index_db_path)
            
            query = """
            SELECT index_name, COUNT(date) as data_count
            FROM index_data
            GROUP BY index_name
            ORDER BY index_name
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"❌ 获取指数列表失败: {e}")
            return pd.DataFrame()
    
    def normalize_data_for_comparison(self, datasets: list, base_date: str = None) -> list:
        """标准化数据用于对比（以指定日期或第一个有效日期为基准=100）"""
        if not datasets:
            return []
        
        normalized_datasets = []
        
        for df in datasets:
            if df.empty:
                continue
            
            df_copy = df.copy()
            
            # 确定基准日期
            if base_date:
                try:
                    base_date_dt = pd.to_datetime(base_date)
                    base_data = df_copy[df_copy['date'] >= base_date_dt]
                    if not base_data.empty:
                        base_price = base_data.iloc[0]['close']
                    else:
                        base_price = df_copy.iloc[0]['close']
                except:
                    base_price = df_copy.iloc[0]['close']
            else:
                base_price = df_copy.iloc[0]['close']
            
            # 计算标准化价格
            df_copy['normalized_price'] = (df_copy['close'] / base_price) * 100
            normalized_datasets.append(df_copy)
        
        return normalized_datasets
    
    def create_chart(self, stock_datasets: list, index_data: pd.DataFrame, 
                    normalize: bool = False, start_date: str = None, end_date: str = None):
        """创建交互式图表（支持hover和十字线）"""
        
        # 如果需要标准化
        if normalize:
            all_datasets = stock_datasets + ([index_data] if not index_data.empty else [])
            normalized_datasets = self.normalize_data_for_comparison(all_datasets, start_date)
            
            if normalized_datasets:
                stock_datasets = normalized_datasets[:-1] if not index_data.empty else normalized_datasets
                index_data = normalized_datasets[-1] if not index_data.empty and len(normalized_datasets) > len(stock_datasets) else pd.DataFrame()
        
        # 创建plotly图形，开启十字线功能
        fig = go.Figure()
        
        # 颜色列表
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        # 绘制股票数据
        for i, stock_df in enumerate(stock_datasets):
            if stock_df.empty:
                continue
            
            # 筛选日期范围
            plot_df = stock_df.copy()
            if start_date:
                plot_df = plot_df[plot_df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                plot_df = plot_df[plot_df['date'] <= pd.to_datetime(end_date)]
            
            if plot_df.empty:
                continue
            
            color = colors[i % len(colors)]
            
            y_data = plot_df['normalized_price'] if normalize else plot_df['close']
            
            # 计算点的大小基于成交量，归一化到合适范围
            volumes = plot_df['volume']
            if volumes.max() > volumes.min():
                normalized_volume = 5 + (volumes - volumes.min()) / (volumes.max() - volumes.min()) * 25
            else:
                normalized_volume = 15  # 如果成交量都相同，使用固定大小
            
            # 准备hover信息
            hover_text = []
            for _, row in plot_df.iterrows():
                date_str = row['date'].strftime('%Y-%m-%d')
                volume_str = f"{row['volume']:,}"
                amount_str = f"{row['amount']:,.0f}" if 'amount' in row and pd.notna(row['amount']) else "N/A"
                
                if normalize:
                    price_info = f"标准化价格: {row['normalized_price']:.2f}"
                    orig_price_info = f"<br>原始价格: {row['close']:.2f}"
                else:
                    price_info = f"收盘价: {row['close']:.2f}"
                    orig_price_info = f"<br>开盘价: {row['open']:.2f}<br>最高价: {row['high']:.2f}<br>最低价: {row['low']:.2f}"
                
                hover_text.append(
                    f"<b>{row['name']} ({row['symbol']})</b><br>"
                    f"日期: {date_str}<br>"
                    f"{price_info}{orig_price_info}<br>"
                    f"成交量: {volume_str}<br>"
                    f"成交额: {amount_str}元"
                )
            
            # 添加散点图（点大小代表成交量）
            fig.add_trace(go.Scatter(
                x=plot_df['date'],
                y=y_data,
                mode='markers+lines',
                marker=dict(
                    size=normalized_volume,
                    color=color,
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                line=dict(color=color, width=2),
                name=f"{stock_df.iloc[0]['name']} ({plot_df['symbol'].iloc[0]})",
                hovertemplate='<extra></extra>%{text}',
                text=hover_text,
                showlegend=True
            ))
        
        # 绘制指数数据
        if not index_data.empty:
            plot_index = index_data.copy()
            if start_date:
                plot_index = plot_index[plot_index['date'] >= pd.to_datetime(start_date)]
            if end_date:
                plot_index = plot_index[plot_index['date'] <= pd.to_datetime(end_date)]
            
            if not plot_index.empty:
                y_data = plot_index['normalized_price'] if normalize else plot_index['close']
                
                # 准备指数hover信息
                hover_text_index = []
                for _, row in plot_index.iterrows():
                    date_str = row['date'].strftime('%Y-%m-%d')
                    
                    if normalize:
                        price_info = f"标准化点位: {row['normalized_price']:.2f}"
                        orig_price_info = f"<br>原始点位: {row['close']:.2f}"
                    else:
                        price_info = f"收盘点位: {row['close']:.2f}"
                        orig_price_info = f"<br>开盘点位: {row['open']:.2f}<br>最高点位: {row['high']:.2f}<br>最低点位: {row['low']:.2f}"
                    
                    hover_text_index.append(
                        f"<b>{row['index_name']}</b><br>"
                        f"日期: {date_str}<br>"
                        f"{price_info}{orig_price_info}"
                    )
                
                # 添加指数线（虚线）
                fig.add_trace(go.Scatter(
                    x=plot_index['date'],
                    y=y_data,
                    mode='lines',
                    line=dict(color='red', width=3, dash='dash'),
                    name=f"{plot_index.iloc[0]['index_name']}",
                    hovertemplate='<extra></extra>%{text}',
                    text=hover_text_index,
                    showlegend=True
                ))
        
        # 添加基准线（如果标准化）
        if normalize:
            fig.add_hline(y=100, line_dash="dot", line_color="gray", 
                         annotation_text="基准线(100)", annotation_position="bottom right")
        
        # 设置图表布局，开启十字线功能
        title = '股票价格标准化对比图（基期=100，点大小=成交量）' if normalize else '股票价格走势图（点大小=成交量）'
        y_title = '标准化价格' if normalize else '价格 (元)'
        
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, family="Microsoft YaHei, Arial, sans-serif"),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='日期',
                title_font=dict(size=14, family="Microsoft YaHei, Arial, sans-serif"),
                tickformat='%Y-%m',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                showspikes=True,  # 开启X轴延伸线
                spikethickness=1,
                spikecolor="rgba(0,0,0,0.5)",
                spikemode="across"
            ),
            yaxis=dict(
                title=y_title,
                title_font=dict(size=14, family="Microsoft YaHei, Arial, sans-serif"),
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                showspikes=True,  # 开启Y轴延伸线
                spikethickness=1,
                spikecolor="rgba(0,0,0,0.5)",
                spikemode="across"
            ),
            hovermode='closest',  # 只显示鼠标最近的一个数据点
            dragmode='zoom',  # 默认为缩放模式，支持Mac触摸板
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1,
                font=dict(family="Microsoft YaHei, Arial, sans-serif")
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            width=1200,
            height=700,
            margin=dict(l=60, r=120, t=80, b=60),
            font=dict(family="Microsoft YaHei, Arial, sans-serif")  # 全局字体设置
        )
        
        # 保存为HTML文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_name = "标准化对比" if normalize else "价格走势"
        html_filename = f"/Users/guanjie/Desktop/cursor/longbridge/output/{chart_name}交互图_{timestamp}.html"
        
        try:
            fig.write_html(html_filename, config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
            })
            print(f"💾 交互式图表已保存: {html_filename}")
            print(f"🌐 双击HTML文件在浏览器中打开查看交互效果")
            print(f"✨ 鼠标悬浮可查看详细数据，自动显示十字线")
        except Exception as e:
            print(f"⚠️ 保存HTML文件失败: {e}")
        
        # 显示图表
        fig.show()
    
    def get_user_input(self):
        """获取用户输入"""
        print("\n" + "="*60)
        print("📈 交互式股票与指数图表绘制工具")
        print("="*60)
        
        # 显示可用数据示例
        print("\n📊 数据库中的数据示例:")
        
        # 显示部分股票列表
        stocks_sample = self.list_available_stocks()
        if not stocks_sample.empty:
            print("\n可用股票 (显示前10个):")
            print(stocks_sample.head(10)[['symbol', 'name', 'market']].to_string(index=False))
        
        # 显示指数列表
        indices_sample = self.list_available_indices()
        if not indices_sample.empty:
            print(f"\n可用指数:")
            print(indices_sample.to_string(index=False))
        
        # 获取股票代码输入
        print(f"\n" + "-"*50)
        stock_input = input("📈 请输入股票代码 (多个用逗号分隔，默认: 600519): ").strip()
        
        if not stock_input:
            stock_codes = ["600519"]  # 默认茅台
        else:
            stock_codes = [code.strip() for code in stock_input.split(',')]
        
        # 验证和标准化股票代码
        validated_codes = []
        for code in stock_codes:
            validated_code = self.validate_stock_code(code)
            validated_codes.append(validated_code)
        
        # 选择指数
        index_input = input(f"📊 请输入指数名称 (默认: 上证指数): ").strip()
        index_name = index_input if index_input else "上证指数"
        
        # 固定为价格走势图，点大小代表成交量
        chart_type = "price"
        
        # 是否标准化对比
        normalize_choice = input("是否标准化对比 (y/n, 默认n): ").strip().lower()
        normalize = normalize_choice in ['y', 'yes', '是']
        
        # 时间范围
        print(f"\n时间范围 (可选):")
        start_date = input("开始日期 (YYYY-MM-DD, 回车跳过): ").strip()
        end_date = input("结束日期 (YYYY-MM-DD, 回车跳过): ").strip()
        
        start_date = start_date if start_date else None
        end_date = end_date if end_date else None
        
        return validated_codes, index_name, normalize, start_date, end_date
    
    def run(self):
        """运行交互式图表生成"""
        try:
            # 获取用户输入
            stock_codes, index_name, normalize, start_date, end_date = self.get_user_input()
            
            print(f"\n" + "="*60)
            print("🔄 正在获取数据并生成图表...")
            print("="*60)
            
            # 获取股票数据
            stock_datasets = []
            for code in stock_codes:
                stock_data = self.get_stock_data(code)
                if not stock_data.empty:
                    stock_datasets.append(stock_data)
            
            if not stock_datasets:
                print("❌ 未获取到任何股票数据")
                return
            
            # 获取指数数据
            index_data = self.get_index_data(index_name)
            
            # 生成图表
            self.create_chart(stock_datasets, index_data, normalize, start_date, end_date)
            
        except KeyboardInterrupt:
            print("\n\n👋 用户中断操作")
        except Exception as e:
            print(f"\n❌ 程序运行出错: {e}")

def main():
    """主函数"""
    plotter = InteractiveChartPlotter()
    
    while True:
        try:
            plotter.run()
            
            # 询问是否继续
            continue_choice = input(f"\n🔄 是否继续绘制其他图表? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 程序出错: {e}")
            break
    
    print("👋 感谢使用交互式图表绘制工具！")

if __name__ == "__main__":
    main()
