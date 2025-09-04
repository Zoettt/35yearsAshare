#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票图表Web应用
基于Flask的交互式股票图表网页应用
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import sys

class WebChartApp:
    """Web图表应用类"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'your-secret-key-here'
        
        # 数据库路径
        self.kline_db_path = "/Users/guanjie/Desktop/cursor/longbridge/output/kline_data/a_share_klines.db"
        self.index_db_path = "/Users/guanjie/Desktop/cursor/longbridge/output/index_data/major_indices.db"
        
        # 检查数据库
        self.check_databases()
        
        # 设置路由
        self.setup_routes()
    
    def check_databases(self):
        """检查数据库文件"""
        if not os.path.exists(self.kline_db_path):
            print(f"❌ K线数据库不存在: {self.kline_db_path}")
        if not os.path.exists(self.index_db_path):
            print(f"❌ 指数数据库不存在: {self.index_db_path}")
        print("✅ 数据库检查完成")
    
    def setup_routes(self):
        """设置Flask路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        @self.app.route('/api/stocks')
        def get_stocks():
            """获取可用股票列表（优化版）"""
            try:
                # 获取查询参数
                search = request.args.get('search', '').strip()
                limit = int(request.args.get('limit', 100))  # 默认限制100条
                
                conn = sqlite3.connect(self.kline_db_path)
                
                if search:
                    # 搜索模式 - 优化的搜索查询
                    query = """
                    SELECT si.symbol, si.name 
                    FROM stock_info si
                    WHERE si.name IS NOT NULL 
                    AND (si.symbol LIKE ? OR si.name LIKE ?)
                    ORDER BY 
                        CASE WHEN si.symbol = ? THEN 1 ELSE 2 END,
                        CASE WHEN si.name = ? THEN 1 ELSE 2 END,
                        CASE 
                            WHEN si.symbol LIKE 'sh60%' THEN 1
                            WHEN si.symbol LIKE 'sz00%' THEN 2
                            WHEN si.symbol LIKE 'sz30%' THEN 3
                            WHEN si.symbol LIKE 'bj%' THEN 4
                            ELSE 5
                        END, si.symbol
                    LIMIT ?
                    """
                    search_pattern = f"%{search}%"
                    df = pd.read_sql_query(query, conn, params=[
                        search_pattern, search_pattern, search, search, limit
                    ])
                else:
                    # 默认模式 - 返回热门股票
                    query = """
                    SELECT si.symbol, si.name 
                    FROM stock_info si
                    WHERE si.name IS NOT NULL 
                    AND si.symbol IN (
                        '000001', '000002', '600000', '600036', '600519', '000858',
                        '300015', '002415', '000651', '600887', '002594', '300750'
                    )
                    ORDER BY CASE 
                        WHEN si.symbol LIKE 'sh60%' THEN 1
                        WHEN si.symbol LIKE 'sz00%' THEN 2
                        WHEN si.symbol LIKE 'sz30%' THEN 3
                        WHEN si.symbol LIKE 'bj%' THEN 4
                        ELSE 5
                    END, si.symbol
                    """
                    df = pd.read_sql_query(query, conn)
                
                conn.close()
                
                stocks = df.to_dict('records')
                return jsonify({
                    'success': True, 
                    'data': stocks,
                    'count': len(stocks),
                    'search': search
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/stocks/search')
        def search_stocks():
            """快速股票搜索API"""
            try:
                search = request.args.get('q', '').strip()
                limit = int(request.args.get('limit', 20))  # 搜索默认20条
                
                if not search:
                    return jsonify({'success': True, 'data': []})
                
                conn = sqlite3.connect(self.kline_db_path)
                
                # 优化的搜索查询 - 精确匹配优先
                query = """
                SELECT si.symbol, si.name,
                       CASE 
                           WHEN si.symbol = ? THEN 1
                           WHEN si.symbol LIKE ? THEN 2
                           WHEN si.name = ? THEN 3
                           WHEN si.name LIKE ? THEN 4
                           ELSE 5
                       END as priority
                FROM stock_info si
                WHERE si.name IS NOT NULL 
                AND (si.symbol LIKE ? OR si.name LIKE ?)
                ORDER BY priority, si.symbol
                LIMIT ?
                """
                
                search_pattern = f"%{search}%"
                search_start = f"{search}%"
                
                df = pd.read_sql_query(query, conn, params=[
                    search, search_start, search, search_start, 
                    search_pattern, search_pattern, limit
                ])
                
                conn.close()
                
                # 移除priority列
                if 'priority' in df.columns:
                    df = df.drop('priority', axis=1)
                
                stocks = df.to_dict('records')
                return jsonify({
                    'success': True, 
                    'data': stocks,
                    'count': len(stocks)
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/indices')
        def get_indices():
            """获取可用指数列表"""
            try:
                conn = sqlite3.connect(self.index_db_path)
                query = "SELECT DISTINCT index_name FROM index_data ORDER BY index_name"
                df = pd.read_sql_query(query, conn)
                conn.close()
                
                indices = df['index_name'].tolist()
                return jsonify({'success': True, 'data': indices})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/chart', methods=['POST'])
        def generate_chart():
            """生成图表"""
            try:
                data = request.get_json()
                stocks = data.get('stocks', ['sh600519'])
                index_name = data.get('index', '上证指数')
                normalize = data.get('normalize', False)
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                
                # 获取股票数据
                stock_datasets = []
                for stock_code in stocks:
                    stock_data = self.get_stock_data(stock_code)
                    if not stock_data.empty:
                        stock_datasets.append(stock_data)
                
                # 获取指数数据
                index_data = self.get_index_data(index_name)
                
                # 生成图表
                chart_json = self.create_chart_json(
                    stock_datasets, index_data, normalize, start_date, end_date
                )
                
                return jsonify({
                    'success': True, 
                    'chart': chart_json,
                    'stock_count': len(stock_datasets),
                    'index_name': index_name
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """获取股票数据"""
        try:
            conn = sqlite3.connect(self.kline_db_path)
            
            # 标准化股票代码
            symbol = self.validate_stock_code(symbol)
            
            query = """
            SELECT kd.date, kd.symbol, si.name, kd.open, kd.high, kd.low, kd.close, kd.volume, kd.amount
            FROM kline_data kd
            LEFT JOIN stock_info si ON kd.symbol = si.symbol
            WHERE kd.symbol = ?
            ORDER BY kd.date
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                # 如果没有股票名称，使用symbol作为name
                if df['name'].isna().all():
                    df['name'] = symbol
            
            return df
            
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return pd.DataFrame()
    
    def get_index_data(self, index_name: str) -> pd.DataFrame:
        """获取指数数据"""
        try:
            conn = sqlite3.connect(self.index_db_path)
            
            query = """
            SELECT date, index_name, open, high, low, close, volume
            FROM index_data 
            WHERE index_name = ?
            ORDER BY date
            """
            
            df = pd.read_sql_query(query, conn, params=(index_name,))
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            print(f"获取指数数据失败: {e}")
            return pd.DataFrame()
    
    def validate_stock_code(self, code: str) -> str:
        """验证和标准化股票代码"""
        code = code.strip()
        
        # 如果已经是数据库格式
        if code.startswith(('sh', 'sz', 'bj')) and len(code) == 8:
            return code.lower()
        
        # 如果是标准格式
        if '.' in code:
            symbol_part, exchange = code.split('.')
            if exchange.upper() == 'SH':
                return f"sh{symbol_part}"
            elif exchange.upper() == 'SZ':
                return f"sz{symbol_part}"
        
        # 如果是6位数字
        if len(code) == 6 and code.isdigit():
            if code.startswith(('000', '001', '002', '003', '300')):
                return f"sz{code}"
            elif code.startswith(('600', '601', '603', '605', '688')):
                return f"sh{code}"
            elif code.startswith(('430', '831', '833', '836', '838')):
                return f"bj{code}"
        
        return code.lower()
    
    def normalize_data_for_comparison(self, datasets: list, base_date: str = None) -> list:
        """标准化数据用于对比"""
        if not datasets or len(datasets) == 0:
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
                    # 找到最接近基准日期的数据点
                    base_row = df_copy[df_copy['date'] >= base_date_dt].iloc[0:1]
                except:
                    base_row = df_copy.iloc[0:1]
            else:
                base_row = df_copy.iloc[0:1]
            
            if base_row.empty:
                continue
            
            base_price = base_row['close'].iloc[0]
            
            # 计算标准化价格（基期=100）
            df_copy['normalized_price'] = (df_copy['close'] / base_price) * 100
            
            normalized_datasets.append(df_copy)
        
        return normalized_datasets
    
    def create_chart_json(self, stock_datasets: list, index_data: pd.DataFrame, 
                         normalize: bool = False, start_date: str = None, end_date: str = None):
        """创建图表JSON数据"""
        
        # 如果需要标准化
        if normalize:
            all_datasets = stock_datasets + ([index_data] if not index_data.empty else [])
            normalized_datasets = self.normalize_data_for_comparison(all_datasets, start_date)
            
            if normalized_datasets:
                stock_datasets = normalized_datasets[:-1] if not index_data.empty else normalized_datasets
                index_data = normalized_datasets[-1] if not index_data.empty and len(normalized_datasets) > len(stock_datasets) else pd.DataFrame()
        
        # 创建plotly图形
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
            
            # 计算点的大小基于成交量
            volumes = plot_df['volume']
            if volumes.max() > volumes.min():
                normalized_volume = 5 + (volumes - volumes.min()) / (volumes.max() - volumes.min()) * 25
            else:
                normalized_volume = 15
            
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
            
            # 添加散点图（确保数据为Python原生类型）
            fig.add_trace(go.Scatter(
                x=plot_df['date'].tolist(),  # 转换为Python列表
                y=y_data.tolist(),  # 转换为Python列表
                mode='markers+lines',
                marker=dict(
                    size=normalized_volume.tolist() if hasattr(normalized_volume, 'tolist') else normalized_volume,
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
                
                # 添加指数线（标准化模式使用左轴，非标准化模式使用右轴）
                trace_config = {
                    'x': plot_index['date'].tolist(),
                    'y': y_data.tolist(),
                    'mode': 'lines',
                    'line': dict(color='red', width=3, dash='dash'),
                    'name': f"{plot_index.iloc[0]['index_name']}",
                    'hovertemplate': '<extra></extra>%{text}',
                    'text': hover_text_index,
                    'showlegend': True
                }
                
                # 标准化模式下使用左轴，非标准化模式使用右轴
                if not normalize:
                    trace_config['yaxis'] = 'y2'
                
                fig.add_trace(go.Scatter(**trace_config))
        
        # 添加基准线
        if normalize:
            fig.add_hline(y=100, line_dash="dot", line_color="gray", 
                         annotation_text="基准线(100)", annotation_position="bottom right")
        
        # 设置图表布局
        if normalize:
            title = '股票价格标准化对比图（基期=100，点大小=成交量）'
            y_title = '标准化价格'
        else:
            title = '股票价格走势图（左轴=股票价格，右轴=指数点位，点大小=成交量）'
            y_title = '股票价格 (元)'
        
        # 基础布局配置
        layout_config = {
            'title': dict(
                text=title,
                font=dict(size=18, family="Microsoft YaHei, Arial, sans-serif"),
                x=0.5,
                xanchor='center'
            ),
            'xaxis': dict(
                title='日期',
                title_font=dict(size=14, family="Microsoft YaHei, Arial, sans-serif"),
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                showspikes=True,
                spikethickness=1,
                spikecolor="rgba(0,0,0,0.5)",
                spikemode="across"
            ),
            'yaxis': dict(
                title=y_title,
                title_font=dict(size=14, family="Microsoft YaHei, Arial, sans-serif"),
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                showspikes=True,
                spikethickness=1,
                spikecolor="rgba(0,0,0,0.5)",
                spikemode="across",
                side='left'
            )
        }
        
        # 非标准化模式才添加第二个Y轴
        if not normalize:
            layout_config['yaxis2'] = dict(
                title='指数点位',
                title_font=dict(size=14, family="Microsoft YaHei, Arial, sans-serif", color='red'),
                showgrid=False,  # 右侧Y轴不显示网格，避免重叠
                showspikes=True,
                spikethickness=1,
                spikecolor="rgba(255,0,0,0.5)",
                spikemode="across",
                overlaying='y',
                side='right',
                tickfont=dict(color='red')
            )
        
        fig.update_layout(
            **layout_config,
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
            height=600,
            margin=dict(l=80, r=150, t=80, b=60),  # 增加左右边距以容纳双Y轴
            font=dict(family="Microsoft YaHei, Arial, sans-serif")
        )
        
        # 返回JSON数据
        return fig.to_json()
    
    def run(self, host='127.0.0.1', port=5002, debug=True):
        """运行Flask应用"""
        print(f"🌐 启动Web图表应用...")
        print(f"🔗 访问地址: http://{host}:{port}")
        print(f"📊 支持交互式股票图表绘制")
        self.app.run(host=host, port=port, debug=debug)

# 创建应用实例
app_instance = WebChartApp()

if __name__ == '__main__':
    app_instance.run()
