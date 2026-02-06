#!/bin/bash
#
# 内存条价格监控器 - 快速部署脚本
# 
# 用法:
#   chmod +x deploy.sh
#   ./deploy.sh
#

echo "🖥️  内存条价格监控器 - 部署脚本"
echo "======================================"
echo ""

# 1. 检查 Python 版本
echo "📌 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "   ✅ $PYTHON_VERSION"
else
    echo "   ❌ 未找到 Python 3，请先安装 Python"
    exit 1
fi
echo ""

# 2. 创建配置
echo "📌 初始化配置..."
if [ ! -f config.json ]; then
    cat > config.json << 'EOF'
{
  "products": {
    "金士顿DDR4 3200 16GB": "100026643164",
    "金士顿DDR5 5600 32GB": "100028908789"
  }
}
EOF
    echo "   ✅ 已创建 config.json"
    echo "   💡 提示: 请编辑 config.json 添加你关注的内存条商品"
else
    echo "   ⏭️  config.json 已存在，跳过"
fi
echo ""

# 3. 创建 systemd 服务（可选）
echo "📌 配置系统服务..."
read -p "   是否配置 systemd 服务进行后台运行? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/ram-monitor.service"
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=内存条价格监控器
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=$(which python3) $(pwd)/ram_monitor.py monitor 300
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "   ✅ 已创建服务文件: $SERVICE_FILE"
    echo ""
    echo "   📝 使用以下命令管理服务:"
    echo "      systemctl enable ram-monitor    # 开机自启"
    echo "      systemctl start ram-monitor    # 启动服务"
    echo "      systemctl status ram-monitor   # 查看状态"
    echo "      journalctl -u ram-monitor -f   # 查看日志"
else
    echo "   ⏭️  跳过 systemd 配置"
fi
echo ""

# 4. 创建定时任务（可选）
echo "📌 配置定时任务..."
read -p "   是否配置 cron 定时检查? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   📝 添加 cron 任务..."
    (crontab -l 2>/dev/null | grep -v "ram_monitor.py"; echo "0 */1 * * * cd $(pwd) && python3 $(pwd)/ram_monitor.py check >> $(pwd)/price.log 2>&1") | crontab -
    echo "   ✅ 已添加: 每小时检查一次价格"
    echo "   📝 查看 crontab: crontab -e"
else
    echo "   ⏭️  跳过 cron 配置"
fi
echo ""

# 5. 测试运行
echo "📌 测试运行..."
echo ""
echo "   运行一次价格检查:"
python3 ram_monitor.py check
echo ""

# 6. 完成
echo "======================================"
echo "✅ 部署完成!"
echo ""
echo "📁 文件位置: $(pwd)"
echo "📋 配置文档: README.md"
echo ""
echo "💡 常用命令:"
echo "   python3 ram_monitor.py check       # 检查一次价格"
echo "   python3 ram_monitor.py history     # 查看历史价格"
echo "   python3 ram_monitor.py monitor      # 持续监控"
echo ""
echo "⚠️  注意事项:"
echo "   - 请编辑 config.json 添加你关注的商品"
echo "   - 京东可能有反爬虫机制，请合理设置频率"
echo ""
