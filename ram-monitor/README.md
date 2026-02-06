# 🖥️ 内存条价格监控器

监控京东商城内存条价格，支持定时检查和降价提醒。

## 功能

- ✅ 实时监控多个内存条商品价格
- 📈 自动记录价格历史
- 📉 检测价格变化（涨价/降价）
- 💾 本地保存历史数据（JSON格式）
- 🔔 支持多种查询命令

## 快速开始

### 1. 安装依赖

本脚本无需安装额外依赖，使用 Python 3 内置库：

```bash
python3 --version  # 确保是 Python 3.6+
```

### 2. 配置商品

编辑 `config.json` 文件，添加你想要监控的内存条商品：

```json
{
  "products": {
    "金士顿DDR4 3200 16GB": "商品SKU_ID",
    "芝奇DDR4 3600 16GB": "商品SKU_ID"
  }
}
```

或者使用命令行添加：

```bash
python3 ram_monitor.py add "金士顿DDR4 16GB" 100026643164
```

### 3. 获取商品SKU_ID

在京东商品页面URL中找到SKU_ID，例如：
- 商品链接: `https://item.jd.com/100026643164.html`
- SKU_ID: `100026643164`

### 4. 运行监控

#### 持续监控模式

```bash
# 每5分钟检查一次（默认）
python3 ram_monitor.py monitor

# 每10分钟检查一次
python3 ram_monitor.py monitor 600
```

#### 只检查一次

```bash
python3 ram_monitor.py check
```

### 5. 查看结果

```bash
# 列出所有监控商品
python3 ram_monitor.py list

# 查看价格历史
python3 ram_monitor.py history

# 查看指定商品历史
python3 ram_monitor.py history 100026643164
```

## 文件说明

```
ram-monitor/
├── ram_monitor.py      # 主程序
├── config.json         # 商品配置（自动生成）
├── price_history.json  # 价格历史记录（自动生成）
└── README.md          # 说明文档
```

## 常见问题

### Q: 京东价格获取失败？

A: 京东有反爬虫机制，可能需要：
1. 使用代理
2. 降低检查频率
3. 添加请求头模拟浏览器

### Q: 如何添加微信/邮件提醒？

A: 当前版本不支持自动提醒，可以：
1. 手动查看控制台输出
2. 定期运行 `python3 ram_monitor.py history` 查看历史
3. 使用cron定时任务 + 系统通知

### Q: 如何在服务器上长期运行？

A: 使用 nohup 或 systemd：

```bash
# 使用 nohup
nohup python3 ram_monitor.py monitor > monitor.log 2>&1 &

# 使用 systemd（推荐）
# 创建 /etc/systemd/system/ram-monitor.service
```

## 高级用法

### 添加代理支持

修改 `ram_monitor.py` 中的 `get_jd_price` 函数：

```python
def get_jd_price(sku_id):
    proxy = {
        'http': 'http://user:pass@proxy.com:port',
        'https': 'https://user:pass@proxy.com:port'
    }
    # 使用 proxy 参数
```

### 定时任务（Linux/Mac）

```bash
# 编辑 crontab
crontab -e

# 添加：每小时检查一次价格
0 * * * * cd /path/to/ram-monitor && python3 ram_monitor.py check >> price.log 2>&1
```

## 数据来源

- 京东商城 (jd.com)
- 价格API: `https://p.3.cn/prices/mgets`

## 注意事项

1. 请合理设置检查频率，避免对京东服务器造成压力
2. 京东可能随时更改API或增加反爬虫机制
3. 建议在非高峰时段运行（如凌晨）
4. 价格仅供参考，实际价格以京东页面为准

## License

MIT License
