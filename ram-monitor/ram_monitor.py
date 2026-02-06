#!/usr/bin/env python3
"""
内存条价格监控脚本
监控京东商城内存条价格，支持定时检查和降价提醒
"""

import json, time, os, sys
import urllib.request
from datetime import datetime
from urllib.parse import urlparse

# ============ 配置 ============
CONFIG_FILE = "config.json"

# 京东内存条商品ID列表（示例）
DEFAULT_PRODUCTS = {
    "金士顿DDR4 3200 16GB": "100026643164",  # 替换为实际商品ID
    "金士顿DDR5 5600 32GB": "100028908789",
    "芝奇DDR4 3600 16GB": "100026643165",
    "威刚DDR4 3200 16GB": "100026643166",
}

# ============ 功能函数 ============

def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"products": DEFAULT_PRODUCTS}

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_jd_price(sku_id):
    """
    获取京东商品价格
    使用京东价格API接口
    """
    try:
        # 方法1: 使用京东比价API
        url = f"https://p.3.cn/prices/mgets?skuIds=J_{sku_id}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Referer', 'https://www.jd.com/')
        
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        
        if data and len(data) > 0:
            price = data[0].get('p', 0)
            return float(price)
    except Exception as e:
        print(f"⚠️ API方式失败: {e}")
    
    try:
        # 方法2: 备用接口
        url = f"https://api.m.jd.com/?functionId=getCatalogProduct&skuId={sku_id}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        
        # 解析返回数据
        if 'price' in str(data):
            price_match = str(data).split('"p":"')[1].split('"')[0] if '"p":"' in str(data) else 0
            return float(price_match)
    except Exception as e:
        print(f"⚠️ 备用API失败: {e}")
    
    return None

def format_price(price):
    """格式化价格显示"""
    if price:
        return f"¥{price:.2f}"
    return "N/A"

def monitor_price(products, interval=300, max_history=100):
    """
    监控商品价格
    
    Args:
        products: 商品字典 {商品名: SKU_ID}
        interval: 检查间隔（秒），默认5分钟
        max_history: 每个商品保留的历史记录数
    """
    print("=" * 60)
    print("🖥️  内存条价格监控器")
    print("=" * 60)
    print(f"📦 监控商品数: {len(products)}")
    print(f"⏰ 检查间隔: {interval}秒")
    print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # 加载历史数据
    history_file = "price_history.json"
    price_history = {}
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                price_history = json.load(f)
        except:
            pass
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] 🔍 检查价格...")
        
        changes = []
        for name, sku_id in products.items():
            print(f"  📦 {name}...", end=" ", flush=True)
            
            # 获取当前价格
            current_price = get_jd_price(sku_id)
            
            if current_price:
                old_price = price_history.get(sku_id, {}).get('current')
                
                # 记录价格
                if sku_id not in price_history:
                    price_history[sku_id] = {'name': name, 'history': [], 'current': None}
                
                # 添加到历史
                price_history[sku_id]['history'].append({
                    'time': timestamp,
                    'price': current_price
                })
                
                # 保持历史记录数量
                if len(price_history[sku_id]['history']) > max_history:
                    price_history[sku_id]['history'] = price_history[sku_id]['history'][-max_history:]
                
                # 更新当前价格
                price_history[sku_id]['current'] = current_price
                
                # 检测价格变化
                if old_price and old_price != current_price:
                    change = current_price - old_price
                    change_pct = (change / old_price) * 100
                    sign = "📈" if change > 0 else "📉"
                    print(f"{sign} {format_price(old_price)} → {format_price(current_price)} ({change_pct:+.2f}%)")
                    changes.append((name, old_price, current_price, change_pct))
                else:
                    print(f"💰 {format_price(current_price)}")
            else:
                print("❌ 获取失败")
        
        # 保存历史数据
        with open(history_file, 'w') as f:
            json.dump(price_history, f, ensure_ascii=False, indent=2)
        
        # 打印价格变化汇总
        if changes:
            print("\n" + "=" * 60)
            print("📊 价格变化汇总:")
            print("=" * 60)
            for name, old_price, new_price, change_pct in changes:
                print(f"  {name}: {format_price(old_price)} → {format_price(new_price)} ({change_pct:+.2f}%)")
        
        print(f"\n💤 等待 {interval} 秒后再次检查...")
        time.sleep(interval)

def check_price_once(products):
    """只检查一次价格"""
    print("=" * 60)
    print("🖥️  内存条价格查询")
    print("=" * 60)
    
    for name, sku_id in products.items():
        price = get_jd_price(sku_id)
        print(f"  📦 {name}: {format_price(price)}")
        time.sleep(0.5)  # 避免请求过快

def add_product(config, name, sku_id):
    """添加监控商品"""
    if 'products' not in config:
        config['products'] = {}
    config['products'][name] = sku_id
    save_config(config)
    print(f"✅ 已添加: {name} (SKU: {sku_id})")

def list_products(config):
    """列出所有监控商品"""
    if not config.get('products'):
        print("📦 未配置任何商品")
        return
    
    print("\n📦 监控商品列表:")
    print("-" * 40)
    for i, (name, sku_id) in enumerate(config['products'].items(), 1):
        print(f"  {i}. {name} (SKU: {sku_id})")

def show_history(product_name=None, sku_id=None):
    """显示价格历史"""
    history_file = "price_history.json"
    if not os.path.exists(history_file):
        print("❌ 没有价格历史记录")
        return
    
    with open(history_file, 'r') as f:
        price_history = json.load(f)
    
    if not price_history:
        print("❌ 没有价格历史记录")
        return
    
    print("\n📈 价格历史:")
    print("-" * 60)
    
    for pid, data in price_history.items():
        if sku_id and pid != sku_id:
            continue
        if product_name and data.get('name') != product_name:
            continue
        
        print(f"\n📦 {data['name']} (SKU: {pid})")
        print("-" * 40)
        
        for record in data['history'][-10:]:  # 最近10条
            print(f"  {record['time']}: ¥{record['price']:.2f}")
        
        if len(data['history']) > 10:
            print(f"  ... 共 {len(data['history'])} 条记录")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
🖥️  内存条价格监控器

用法:
  python3 ram_monitor.py <命令> [参数]

命令:
  monitor          启动持续监控（默认5分钟间隔）
  check            检查一次价格
  add <名称> <SKU> 添加监控商品
  list             列出所有监控商品
  history          显示价格历史
  history <SKU>    显示指定商品历史
  init             初始化配置文件

示例:
  python3 ram_monitor.py monitor          # 启动监控
  python3 ram_monitor.py check           # 检查一次价格
  python3 ram_monitor.py add "金士顿 16GB" 100026643164  # 添加商品
  python3 ram_monitor.py history          # 查看历史价格

注意事项:
  - 需要安装 Python 3.6+
  - 无需额外依赖
  - 京东可能需要代理才能访问
""")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    # 加载配置
    config = load_config()
    
    if command == "monitor":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        monitor_price(config.get('products', {}), interval)
    
    elif command == "check":
        check_price_once(config.get('products', {}))
    
    elif command == "add":
        if len(sys.argv) < 4:
            print("❌ 用法: python3 ram_monitor.py add <名称> <SKU_ID>")
            sys.exit(1)
        add_product(config, sys.argv[2], sys.argv[3])
    
    elif command == "list":
        list_products(config)
    
    elif command == "history":
        sku_id = sys.argv[2] if len(sys.argv) > 2 else None
        show_history(sku_id=sku_id)
    
    elif command == "init":
        save_config({"products": DEFAULT_PRODUCTS})
        print("✅ 已初始化配置文件")
        print(f"📁 配置文件: {CONFIG_FILE}")
    
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()
