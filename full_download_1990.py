#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整数据下载脚本 - 从1990年开始
集成网络修复，下载全部股票和指数数据
"""

import os
import sys
import time
from datetime import datetime

def apply_network_fix():
    """应用网络修复"""
    print("🔧 应用网络修复...")
    
    # 清除代理设置
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['NO_PROXY'] = '*'
    
    # 修补requests
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    original_request = requests.request
    def patched_request(*args, **kwargs):
        kwargs['proxies'] = {}
        kwargs['verify'] = False
        kwargs['timeout'] = kwargs.get('timeout', 30)
        return original_request(*args, **kwargs)
    
    requests.request = patched_request
    requests.get = lambda *args, **kwargs: patched_request('GET', *args, **kwargs)
    
    print("✅ 网络修复已应用")

def clear_kline_data():
    """清理K线数据"""
    print("\n🗑️ 清理K线数据...")
    
    # 清理K线数据
    kline_db = "output/kline_data/a_share_klines.db"
    kline_progress = "output/kline_data/download_progress.json"
    
    if os.path.exists(kline_db):
        os.remove(kline_db)
        print("  ✅ 已删除K线数据库")
    
    if os.path.exists(kline_progress):
        # 备份进度文件
        backup_name = f"output/kline_data/download_progress_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.rename(kline_progress, backup_name)
        print(f"  ✅ 已备份K线进度文件到: {backup_name}")
    
    print("✅ K线数据清理完成")

def download_index_data():
    """下载指数数据"""
    print("\n📊 第一步：下载指数数据...")
    print("=" * 50)
    
    from major_index_fetcher import MajorIndexFetcher
    
    # 创建指数获取器
    fetcher = MajorIndexFetcher(start_date="1990-01-01")
    
    try:
        # 开始下载所有指数
        fetcher.download_all_indices()
        print("✅ 指数数据下载完成")
        return True
    except Exception as e:
        print(f"❌ 指数数据下载失败: {e}")
        return False

def download_kline_data():
    """下载K线数据"""
    print("\n📈 第二步：下载K线数据...")
    print("=" * 50)
    
    # 重新应用网络修复（确保在导入模块前生效）
    apply_network_fix()
    
    from a_share_kline_fetcher import AShareKlineFetcher
    
    # 创建K线获取器
    fetcher = AShareKlineFetcher(start_date="1990-01-01")
    
    print("⚙️ 下载配置:")
    print("  - 起始日期: 1990-01-01")
    print("  - 并发线程: 3")
    print("  - 批次大小: 50")
    
    try:
        # 测试网络连接
        print("\n🧪 测试K线数据获取...")
        test_df = fetcher.get_kline_data_akshare('000001', '1990-01-01')
        if test_df is not None and not test_df.empty:
            print(f"✅ 网络测试成功，获取到测试数据 {len(test_df)} 条")
        else:
            print("❌ 网络测试失败，无法获取数据")
            return False
        
        # 开始下载所有股票
        fetcher.download_all_stocks(max_workers=3, batch_size=50)
        print("✅ K线数据下载完成")
        return True
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断下载")
        print("💾 进度已自动保存，可稍后继续")
        return False
    except Exception as e:
        print(f"❌ K线数据下载失败: {e}")
        return False

def verify_data():
    """验证下载的数据"""
    print("\n🔍 验证下载的数据...")
    
    import sqlite3
    import pandas as pd
    
    # 验证K线数据
    try:
        conn = sqlite3.connect("output/kline_data/a_share_klines.db")
        total = pd.read_sql_query('SELECT COUNT(*) as count FROM kline_data', conn)
        date_range = pd.read_sql_query('SELECT MIN(date) as min_date, MAX(date) as max_date FROM kline_data', conn)
        stocks = pd.read_sql_query('SELECT COUNT(DISTINCT symbol) as count FROM kline_data', conn)
        pre_2015 = pd.read_sql_query('SELECT COUNT(*) as count FROM kline_data WHERE date < "2015-01-01"', conn)
        conn.close()
        
        print(f"\n📈 K线数据:")
        print(f"  总数据: {total.iloc[0]['count']:,} 条")
        print(f"  股票数: {stocks.iloc[0]['count']} 只")
        print(f"  日期范围: {date_range.iloc[0]['min_date']} 到 {date_range.iloc[0]['max_date']}")
        print(f"  2015年前: {pre_2015.iloc[0]['count']:,} 条")
        
    except Exception as e:
        print(f"❌ K线数据验证失败: {e}")
    
    # 验证指数数据
    try:
        conn = sqlite3.connect("output/index_data/major_indices.db")
        total = pd.read_sql_query('SELECT COUNT(*) as count FROM index_data', conn)
        date_range = pd.read_sql_query('SELECT MIN(date) as min_date, MAX(date) as max_date FROM index_data', conn)
        indices = pd.read_sql_query('SELECT COUNT(DISTINCT index_name) as count FROM index_data', conn)
        pre_2015 = pd.read_sql_query('SELECT COUNT(*) as count FROM index_data WHERE date < "2015-01-01"', conn)
        conn.close()
        
        print(f"\n📊 指数数据:")
        print(f"  总数据: {total.iloc[0]['count']:,} 条")
        print(f"  指数数: {indices.iloc[0]['count']} 个")
        print(f"  日期范围: {date_range.iloc[0]['min_date']} 到 {date_range.iloc[0]['max_date']}")
        print(f"  2015年前: {pre_2015.iloc[0]['count']:,} 条")
        
    except Exception as e:
        print(f"❌ 指数数据验证失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 K线数据下载脚本 - 从1990年开始")
    print("📈 下载全部A股股票历史数据")
    print("=" * 60)
    
    print("\n⚠️ 重要提醒:")
    print("- 下载全部股票数据需要较长时间（数小时）")
    print("- 建议在网络稳定且时间充裕时运行")
    print("- 支持中断后断点续传")
    print("- 会先清理现有K线数据，重新下载完整历史数据")
    print("- 指数数据已存在，将跳过指数数据下载")
    
    confirm = input("\n✅ 确认开始K线数据下载？[y/n]: ").lower().strip()
    if confirm != 'y':
        print("取消下载")
        return
    
    start_time = datetime.now()
    
    # 应用网络修复
    apply_network_fix()
    
    # 清理K线数据
    clear_kline_data()
    
    # 跳过指数数据下载（已存在）
    print("\n📊 指数数据: ✅ 已存在，跳过下载")
    
    # 下载K线数据
    kline_success = download_kline_data()
    
    # 验证数据
    verify_data()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📋 下载完成总结:")
    print(f"  指数数据: ✅ 已存在")
    print(f"  K线数据: {'✅ 成功' if kline_success else '❌ 失败'}")
    print(f"  总耗时: {duration}")
    
    if kline_success:
        print("\n🎉 K线数据下载成功！")
        print("\n📁 数据保存位置:")
        print("  - K线数据: output/kline_data/a_share_klines.db")
        print("  - 指数数据: output/index_data/major_indices.db")
        print("\n🌐 启动Web应用查看数据: ./start_web_app.sh")
    else:
        print("\n⚠️ K线数据下载失败，请检查日志文件")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
