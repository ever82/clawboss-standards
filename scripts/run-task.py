#!/usr/bin/env python3
"""
run-task.py - 启动 Claude Code 执行指定 task

用法:
    python .clawboss-standards/scripts/run-task.py TASK-001
    python .clawboss-standards/scripts/run-task.py TASK-001 -t 60
    python .clawboss-standards/scripts/run-task.py TASK-001 -m "自定义消息"
"""

import subprocess
import sys
import os
import shutil
import time
import threading
import argparse
from datetime import datetime

# 路径
PROJECT_DIR = os.getcwd()
TASKS_DIR = os.path.join(PROJECT_DIR, ".clawboss", "tasks")
SAVE_DIR = os.path.join(PROJECT_DIR, ".claude-sessions")


def find_git_bash():
    paths = [
        os.environ.get("CLAUDE_CODE_GIT_BASH_PATH"),
        r"D:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        shutil.which("bash"),
    ]
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return None


def find_claude():
    claude_path = shutil.which("claude")
    if claude_path:
        return claude_path
    for p in [os.path.expanduser("~\\AppData\\Roaming\\npm\\claude.cmd")]:
        if os.path.isfile(p):
            return p
    return None


def find_task_file(task_id):
    """查找 task 文件，支持模糊匹配"""
    if not os.path.isdir(TASKS_DIR):
        return None

    # 精确匹配
    for name in os.listdir(TASKS_DIR):
        if not name.endswith(".md"):
            continue
        stem = name[:-3]
        if stem == task_id:
            return os.path.join(TASKS_DIR, name)

    # 前缀匹配
    for name in os.listdir(TASKS_DIR):
        if not name.endswith(".md"):
            continue
        stem = name[:-3]
        if stem.startswith(task_id) or task_id in stem:
            return os.path.join(TASKS_DIR, name)

    return None


def get_git_info():
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=5
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=5
        ).stdout.strip()
        commits = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=5
        ).stdout.strip()
        return {"branch": branch, "status": status, "commits": commits}
    except:
        return {"branch": "?", "status": "", "commits": ""}


def save_summary(task_id, reason):
    """保存会话摘要"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SAVE_DIR, f"task_{task_id}_{ts}.md")
    git = get_git_info()

    content = f"""# Task {task_id} - 会话保存

- **时间**: {datetime.now().isoformat()}
- **Task ID**: {task_id}
- **原因**: {reason}
- **分支**: {git['branch']}

## Git 状态
```
{git['status'] or '(clean)'}
```

## 最近提交
```
{git['commits']}
```
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[OK] 已保存到: {path}")


def force_kill(pid):
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True, timeout=10
        )
    except:
        pass


def find_claude_pids():
    """查找 claude 相关进程"""
    pids = []
    try:
        result = subprocess.run(
            ["wmic", "process", "where",
             "commandline like '%claude%'", "get", "ProcessId"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n')[1:]:
            pid = line.strip()
            if pid.isdigit():
                pids.append(int(pid))
    except:
        pass
    return pids


def run(task_id, timeout_minutes, message):
    # 检查 task 文件
    task_file = find_task_file(task_id)
    if task_file:
        print(f"[OK] Task 文件: {task_file}")
    else:
        print(f"[WARN] 未找到 task 文件: {TASKS_DIR}/{task_id}*.md")
        print("[INFO] 将继续执行（可能 task 尚未创建）")

    # 查找 git bash
    git_bash = find_git_bash()
    if not git_bash:
        print("[ERROR] 找不到 Git Bash")
        sys.exit(1)

    claude_exe = find_claude()
    if not claude_exe:
        print("[ERROR] 找不到 claude 命令")
        sys.exit(1)

    # 替换消息中的占位符
    message = message.replace("{task_id}", task_id)
    if task_file:
        message = message.replace("{task_file}", task_file)

    escaped_msg = message.replace('"', '\\"').replace('%', '%%')

    # 记录启动前的 claude 进程（用于后续区分新旧进程）
    pids_before = set(find_claude_pids())

    # 构建并启动命令
    title = f"Task: {task_id}" + (f" ({timeout_minutes}min)" if timeout_minutes else "")
    inner = f'set CLAUDE_CODE_GIT_BASH_PATH={git_bash} && cd /d {PROJECT_DIR} && claude "{escaped_msg}"'

    subprocess.Popen(
        f'start "{title}" cmd /k "{inner}"',
        shell=True
    )

    print(f"[OK] 已启动 Claude Code")
    print(f"[INFO] Task ID: {task_id}")
    print(f"[INFO] 消息: {message[:80]}{'...' if len(message) > 80 else ''}")

    if not timeout_minutes or timeout_minutes <= 0:
        print("[INFO] 无超时限制")
        return

    print(f"[INFO] 超时: {timeout_minutes} 分钟")

    # 超时监控
    timeout_sec = timeout_minutes * 60
    start = time.time()
    stop = threading.Event()

    def monitor():
        while not stop.is_set():
            if time.time() - start >= timeout_sec:
                print(f"\n[TIMEOUT] 已超时 ({timeout_minutes} 分钟)")

                save_summary(task_id, "timeout")

                # 找到新启动的 claude 进程并关闭
                pids_after = set(find_claude_pids())
                new_pids = pids_after - pids_before
                if new_pids:
                    for pid in new_pids:
                        force_kill(pid)
                        print(f"[OK] 已关闭进程 PID:{pid}")
                else:
                    print("[WARN] 未找到 claude 进程")

                stop.set()
                return
            stop.wait(1)

    t = threading.Thread(target=monitor, daemon=True)
    t.start()

    try:
        while not stop.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] 用户中断")
        stop.set()
        save_summary(task_id, "interrupt")


def main():
    parser = argparse.ArgumentParser(
        description="启动 Claude Code 执行指定 task",
        epilog="""
示例:
  python .clawboss-standards/scripts/run-task.py TASK-001
  python .clawboss-standards/scripts/run-task.py TASK-001 -t 60
  python .clawboss-standards/scripts/run-task.py TASK-001 -t 0
  python .clawboss-standards/scripts/run-task.py TASK-001 -m "自定义消息"
        """
    )
    parser.add_argument(
        "task_id",
        help="Task ID，用于在 .clawboss/tasks/ 中查找对应的 md 文件"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        metavar="MINUTES",
        help="超时时间（分钟），默认 30，0 表示不超时"
    )
    parser.add_argument(
        "-m", "--message",
        default=None,
        metavar="MSG",
        help="启动消息，支持 {task_id} 和 {task_file} 占位符"
    )

    args = parser.parse_args()

    # 默认消息
    default_msg = (
        f"在 .clawboss/tasks/ 找到 {args.task_id} 的 task md 文件，然后执行"
    )
    message = args.message or default_msg

    run(args.task_id, args.timeout, message)


if __name__ == "__main__":
    main()
