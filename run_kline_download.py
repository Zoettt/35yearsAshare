#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股K线数据下载 - 快速启动脚本
提供简单的交互式界面来配置和启动数据下载
"""

import sys
import os
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

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from a_share_kline_fetcher import AShareKlineFetcher

def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("🚀 A股历史K线数据获取工具")
    print("=" * 60)
    print("📈 支持全市场股票: 沪深主板、中小板、创业板、科创板")
    print("📅 历史数据: 从1990年1月开始")
    print("💾 数据格式: SQLite数据库 + CSV导出")
    print("🔄 断点续传: 支持中断后继续下载")
    print("=" * 60)

def get_user_config():
    """获取用户配置"""
    config = {}
    
    print("\n⚙️  配置下载参数:")
    print("-" * 30)
    
    # 起始日期配置
    print("\n📅 数据起始日期选择:")
    print("1. 1990-01-01 (推荐，完整35年历史数据)")
    print("2. 2015-01-01 (近10年数据)")
    print("3. 2020-01-01 (近5年数据)")
    print("4. 2023-01-01 (近2年数据)")
    print("5. 自定义日期")
    
    while True:
        choice = input("\n请选择 [1-5]: ").strip()
        if choice == "1":
            config['start_date'] = "1990-01-01"
            break
        elif choice == "2":
            config['start_date'] = "2015-01-01"
            break
        elif choice == "3":
            config['start_date'] = "2020-01-01"
            break
        elif choice == "4":
            config['start_date'] = "2023-01-01"
            break
        elif choice == "5":
            date_input = input("请输入起始日期 (格式: YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(date_input, "%Y-%m-%d")
                config['start_date'] = date_input
                break
            except ValueError:
                print("❌ 日期格式错误，请重新输入")
        else:
            print("❌ 无效选择，请重新输入")
    
    # 并发配置
    print("\n🔄 下载并发设置:")
    print("1. 保守模式 (2线程，适合网络不稳定)")
    print("2. 平衡模式 (3线程，推荐)")
    print("3. 激进模式 (5线程，适合网络稳定)")
    
    while True:
        choice = input("\n请选择 [1-3]: ").strip()
        if choice == "1":
            config['max_workers'] = 2
            config['batch_size'] = 30
            break
        elif choice == "2":
            config['max_workers'] = 3
            config['batch_size'] = 50
            break
        elif choice == "3":
            config['max_workers'] = 5
            config['batch_size'] = 100
            break
        else:
            print("❌ 无效选择，请重新输入")
    
    return config

def estimate_download_time(start_date, max_workers):
    """估算下载时间"""
    start_year = int(start_date.split('-')[0])
    current_year = datetime.now().year
    years = current_year - start_year + 1
    
    # 估算参数
    avg_stocks = 4500  # 平均股票数量
    avg_records_per_year = 250  # 每年交易日数
    total_records = avg_stocks * years * avg_records_per_year
    
    # 根据并发数估算时间
    records_per_second = max_workers * 2  # 每秒处理记录数
    estimated_seconds = total_records / records_per_second
    
    hours = estimated_seconds / 3600
    
    return {
        'stocks': avg_stocks,
        'records': total_records,
        'hours': hours,
        'years': years
    }

def show_download_info(config):
    """显示下载信息"""
    print(f"\n📊 下载配置信息:")
    print("-" * 30)
    print(f"  起始日期: {config['start_date']}")
    print(f"  并发线程: {config['max_workers']}")
    print(f"  批次大小: {config['batch_size']}")
    
    # 估算信息
    estimate = estimate_download_time(config['start_date'], config['max_workers'])
    print(f"\n⏱️  预估信息:")
    print(f"  股票数量: ~{estimate['stocks']:,} 只")
    print(f"  数据年份: {estimate['years']} 年")
    print(f"  数据记录: ~{estimate['records']:,} 条")
    print(f"  预计耗时: {estimate['hours']:.1f} 小时")
    print(f"  数据库大小: ~{estimate['records']/1000000:.0f}GB")

def confirm_and_start(config):
    """确认并开始下载"""
    print(f"\n⚠️  重要提醒:")
    print("- 下载过程较长，建议在网络稳定时运行")
    print("- 可以随时按 Ctrl+C 中断，支持断点续传")
    print("- 数据将保存在 output/kline_data/ 目录")
    print("- 建议确保有足够的磁盘空间")
    
    while True:
        confirm = input(f"\n✅ 确认开始下载？[y/n]: ").lower().strip()
        if confirm == 'y':
            return True
        elif confirm == 'n':
            print("取消下载")
            return False
        else:
            print("请输入 y 或 n")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    try:
        import akshare
        print("✅ AKShare 已安装")
    except ImportError:
        print("❌ AKShare 未安装，请先运行: pip install akshare")
        return
    
    # 获取用户配置
    config = get_user_config()
    
    # 显示下载信息
    show_download_info(config)
    
    # 确认并开始
    if not confirm_and_start(config):
        return
    
    print("\n🚀 开始下载A股K线数据...")
    print("=" * 60)
    
    try:
        # 创建数据获取器
        fetcher = AShareKlineFetcher(start_date=config['start_date'])
        
        # 开始下载
        fetcher.download_all_stocks(
            max_workers=config['max_workers'],
            batch_size=config['batch_size']
        )
        
        print("\n🎉 数据下载完成！")
        print(f"📁 数据库文件: {fetcher.db_path}")
        
        # 询问是否导出CSV
        export_csv = input("\n是否导出为CSV文件？[y/n]: ").lower().strip()
        if export_csv == 'y':
            split_files = input("是否按股票分别导出？[y/n]: ").lower().strip()
            print("正在导出CSV文件...")
            fetcher.export_to_csv(split_by_symbol=(split_files == 'y'))
            print("✅ CSV文件导出完成")
        
        print("\n📈 数据可用于:")
        print("- 技术分析和策略回测")
        print("- 统计分析和相关性研究") 
        print("- 机器学习模型训练")
        print("- 投资组合优化分析")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断下载")
        print("💾 进度已自动保存，可稍后继续")
    except Exception as e:
        print(f"\n❌ 下载过程出错: {e}")
        print("📋 请查看日志文件了解详细错误信息")

if __name__ == "__main__":
    main()
