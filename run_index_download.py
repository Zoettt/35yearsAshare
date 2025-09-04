#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主要指数数据下载 - 快速启动脚本
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from major_index_fetcher import MajorIndexFetcher

def print_banner():
    """打印欢迎横幅"""
    print("=" * 70)
    print("🚀 主要指数历史数据获取工具")
    print("=" * 70)
    print("📈 A股指数: 上证、深成、创业板、科创50、上证50、沪深300、北证50")
    print("🇭🇰 港股指数: 恒生、国企、恒生科技")
    print("🇺🇸 美股指数: 道琼斯、纳斯达克、标普500")
    print("💾 数据格式: SQLite数据库 + CSV导出可选")
    print("📅 时间范围: 1990年1月至今")
    print("=" * 70)

def main():
    """主函数"""
    print_banner()
    
    print("\n⚙️ 配置下载参数:")
    print("-" * 30)
    
    # 起始日期
    start_date = input("📅 起始日期 (YYYY-MM-DD, 默认: 1990-01-01): ").strip()
    if not start_date:
        start_date = "1990-01-01"
    
    # 确认开始
    print(f"\n📊 下载配置:")
    print(f"  - 起始日期: {start_date}")
    print(f"  - 指数数量: 13个")
    print(f"  - 预计时间: 5-10分钟")
    
    confirm = input(f"\n✅ 确认开始下载？[y/n]: ").lower().strip()
    if confirm != 'y':
        print("取消下载")
        return
    
    print("\n🚀 开始下载指数数据...")
    print("=" * 70)
    
    try:
        # 创建数据获取器
        fetcher = MajorIndexFetcher(start_date=start_date)
        
        # 开始下载
        fetcher.download_all_indices()
        
        print("\n🎉 指数数据下载完成！")
        print(f"📁 数据库文件: {fetcher.db_path}")
        
        # 询问是否导出CSV
        export_csv = input("\n📤 是否导出为CSV文件？[y/n]: ").lower().strip()
        if export_csv == 'y':
            split_files = input("是否按指数分别导出？[y/n]: ").lower().strip()
            print("正在导出CSV文件...")
            fetcher.export_to_csv(split_by_index=(split_files == 'y'))
            print("✅ CSV文件导出完成")
        
        print("\n📈 数据用途:")
        print("- 指数走势分析和比较")
        print("- 市场相关性研究") 
        print("- 投资组合基准分析")
        print("- 市场趋势预测模型")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断下载")
        print("💾 已下载的数据已保存到数据库")
    except Exception as e:
        print(f"\n❌ 下载过程出错: {e}")
        print("📋 请查看日志文件了解详细错误信息")

if __name__ == "__main__":
    main()
