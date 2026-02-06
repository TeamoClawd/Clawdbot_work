#!/usr/bin/env python3
"""
feishu-task: 飞书任务管理
支持在群聊和私聊中创建、分配、完成任务
"""

import json, urllib.request, re, os, sys
from datetime import datetime, timedelta
from urllib.parse import parse_qs

# ============ 配置 ============
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")

def load_config():
    """加载飞书配置"""
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return config.get("channels", {}).get("feishu", {})
    except:
        return {}

def get_token(app_id, app_secret):
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode())["tenant_access_token"]

def get_user_id_by_name(token, name):
    """通过名字查找用户ID"""
    url = f"https://open.feishu.cn/open-apis/contact/v3/users?page_size=100"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        users = data.get("data", {}).get("items", [])
        for user in users:
            if name in user.get("name", "") or user.get("name", "") in name:
                return user.get("open_id")
    except:
        pass
    return None

def create_task(token, title, description="", due_time=None, reminder_minutes=0, assignee_id=None):
    """创建任务"""
    url = "https://open.feishu.cn/open-apis/task/v2/tasks"
    
    payload = {
        "task_id": f"task-{int(datetime.now().timestamp())}",
        "title": title,
        "summary": description[:50] if description else title[:50],
        "description": description
    }
    
    if due_time:
        due_ts = int(due_time.timestamp() * 1000)
        payload["due"] = {
            "date": due_time.strftime("%Y-%m-%d"),
            "timestamp": str(due_ts),
            "timezone": "Asia/Shanghai"
        }
    
    if assignee_id:
        payload["members"] = [{"id": assignee_id, "role": "assignee"}]
    
    if reminder_minutes > 0 and due_time:
        remind_ts = int((due_time - timedelta(minutes=reminder_minutes)).timestamp() * 1000)
        payload["reminders"] = [{
            "is_whole_day": False,
            "trigger_time": str(remind_ts),
            "type": "absolute",
            "relative_fire_minute": reminder_minutes
        }]
    
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    req.get_method = lambda: 'POST'
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        if result.get("code") == 0:
            return {"success": True, "task_guid": result.get("data", {}).get("task", {}).get("guid")}
        else:
            return {"success": False, "error": result.get("msg")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def complete_task(token, task_guid):
    """完成任务"""
    url = f"https://open.feishu.cn/open-apis/task/v2/tasks/{task_guid}"
    payload = {
        "task": {"completed_at": str(int(datetime.now().timestamp() * 1000))},
        "update_fields": ["completed_at"]
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    req.get_method = lambda: 'PATCH'
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        return {"success": result.get("code") == 0, "error": result.get("msg")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_task(token, task_guid):
    """删除任务"""
    url = f"https://open.feishu.cn/open-apis/task/v2/tasks/{task_guid}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.get_method = lambda: 'DELETE'
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        return {"success": result.get("code") == 0, "error": result.get("msg")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_tasks(token, page_size=20):
    """查询任务列表"""
    url = f"https://open.feishu.cn/open-apis/task/v2/tasks?page_size={page_size}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        if result.get("code") == 0:
            tasks = result.get("data", {}).get("items", [])
            return {"success": True, "tasks": tasks}
        return {"success": False, "error": result.get("msg")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_task(token, task_guid):
    """查询单个任务详情"""
    url = f"https://open.feishu.cn/open-apis/task/v2/tasks/{task_guid}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        if result.get("code") == 0:
            return {"success": True, "task": result.get("data", {})}
        return {"success": False, "error": result.get("msg")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def parse_time(time_str):
    """解析时间字符串"""
    now = datetime.now()
    
    # 格式: HH:MM
    match = re.match(r'^(\d{1,2}):(\d{2})$', time_str.strip())
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # 格式: YYYY-MM-DD HH:MM
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})$', time_str.strip())
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        hour, minute = int(match.group(4)), int(match.group(5))
        return datetime(year, month, day, hour, minute)
    
    return None

def parse_command(text):
    """解析用户命令"""
    text = text.strip()
    
    # 简化命令
    if text.startswith("创建任务 "):
        title = text[5:].strip()
        return {"action": "create", "title": title}
    
    if text.startswith("创建 "):
        parts = text[3:].split(" ", 3)
        title = parts[0]
        due_time = parse_time(parts[1]) if len(parts) > 1 else None
        
        reminder = 0
        desc = ""
        if len(parts) > 2:
            for part in parts[2:]:
                if part.startswith("--reminder "):
                    try:
                        reminder = int(part[11:])
                    except:
                        pass
                elif part.startswith("--desc "):
                    desc = part[7:]
        
        return {"action": "create_full", "title": title, "due_time": due_time, 
                "reminder": reminder, "description": desc}
    
    if text.startswith("分配 "):
        # 格式: 分配 @成员 标题 [截止时间]
        # 提取被@成员的名字
        text_without_at = re.sub(r'@(\S+)', r'\1', text[3:]).strip()
        parts = text_without_at.split(" ", 1)
        member_name = parts[0]
        title = parts[1] if len(parts) > 1 else ""
        due_time = None
        if " " in title:
            parts2 = title.split(" ", 1)
            potential_time = parse_time(parts2[0])
            if potential_time:
                title = parts2[1]
                due_time = potential_time
            else:
                due_time = parse_time(parts2[1]) if len(parts2) > 1 else None
                title = parts2[0]
        
        return {"action": "assign", "member": member_name, "title": title, "due_time": due_time}
    
    if text.startswith("完成 "):
        task_id = text[3:].strip()
        return {"action": "complete", "task_id": task_id}
    
    if text.startswith("删除 "):
        task_id = text[3:].strip()
        return {"action": "delete", "task_id": task_id}
    
    if text in ["列表", "list"]:
        return {"action": "list"}
    
    if text.startswith("查看 "):
        task_id = text[3:].strip()
        return {"action": "view", "task_id": task_id}
    
    # 默认：创建任务
    return {"action": "create", "title": text}

def build_response(result, command):
    """构建回复消息"""
    action = command.get("action")
    
    if action == "create" and result.get("success"):
        task_guid = result.get("task_guid")
        return f"✅ 任务创建成功！\n任务ID: `{task_guid}`\n\n💡 提示：完成任务请发送 `/task 完成 {task_guid}`"
    
    if action == "create_full" and result.get("success"):
        task_guid = result.get("task_guid")
        due_str = command.get("due_time", "").strftime("%Y-%m-%d %H:%M") if command.get("due_time") else "未设置"
        return f"✅ 任务创建成功！\n标题: {command['title']}\n截止时间: {due_str}\n任务ID: `{task_guid}`\n\n💡 提示：完成任务请发送 `/task 完成 {task_guid}`"
    
    if action == "assign" and result.get("success"):
        task_guid = result.get("task_guid")
        return f"✅ 任务已分配给 {command['member']}！\n任务ID: `{task_guid}`"
    
    if action == "complete" and result.get("success"):
        return "✅ 任务已完成！🎉"
    
    if action == "delete" and result.get("success"):
        return "✅ 任务已删除！🗑️"
    
    if action == "list" and result.get("success"):
        tasks = result.get("tasks", [])
        if not tasks:
            return "📋 当前没有任务"
        
        lines = ["📋 任务列表\n"]
        for i, task in enumerate(tasks, 1):
            title = task.get("title", "未命名")
            status = "✅" if task.get("completed_at") else "🔄"
            due = task.get("due", {}).get("date", "无")
            lines.append(f"{i}. {status} {title} (截止: {due})")
        
        return "\n".join(lines)
    
    if action == "view" and result.get("success"):
        task = result.get("task", {})
        title = task.get("title", "未命名")
        desc = task.get("description", "")
        due = task.get("due", {})
        due_str = f"{due.get('date')} {due.get('time', '')}" if due else "未设置"
        status = "已完成" if task.get("completed_at") else "进行中"
        
        return f"📋 任务详情\n标题: {title}\n描述: {desc}\n截止: {due_str}\n状态: {status}\nID: `{task.get('guid')}`"
    
    return f"❌ 操作失败: {result.get('error', '未知错误')}"

def main():
    """主函数"""
    # 从标准输入读取命令
    if len(sys.argv) > 1:
        # 从命令行参数读取（群聊触发）
        command_text = " ".join(sys.argv[1:])
    else:
        # 从 stdin 读取（私聊触发）
        command_text = sys.stdin.read().strip()
    
    if not command_text:
        print("请提供任务命令")
        return
    
    # 加载配置
    config = load_config()
    app_id = config.get("appId")
    app_secret = config.get("appSecret")
    
    if not app_id or not app_secret:
        print("❌ 错误: 未配置飞书应用")
        return
    
    # 获取 token
    try:
        token = get_token(app_id, app_secret)
    except Exception as e:
        print(f"❌ 获取访问令牌失败: {e}")
        return
    
    # 解析命令
    command = parse_command(command_text)
    action = command.get("action")
    
    # 执行操作
    if action == "create":
        result = create_task(token, command["title"])
    elif action == "create_full":
        result = create_task(
            token, command["title"], command.get("description", ""),
            command.get("due_time"), command.get("reminder", 0)
        )
    elif action == "assign":
        # 先查找成员ID
        member_id = get_user_id_by_name(token, command["member"])
        if not member_id:
            print(f"❌ 未找到成员: {command['member']}")
            return
        result = create_task(
            token, command["title"], "", command.get("due_time"), 0, member_id
        )
    elif action == "complete":
        result = complete_task(token, command["task_id"])
    elif action == "delete":
        result = delete_task(token, command["task_id"])
    elif action == "list":
        result = list_tasks(token)
    elif action == "view":
        result = get_task(token, command["task_id"])
    else:
        print("❌ 未知的命令")
        return
    
    # 输出结果
    response = build_response(result, command)
    print(response)

if __name__ == "__main__":
    main()
