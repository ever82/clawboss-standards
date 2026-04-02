#!/bin/bash
# CheckTree 状态同步脚本
# 将 Issue 状态同步到 CheckTree.md

set -e

ISSUE_ID="$1"
STATUS="$2"  # pending | in_progress | completed | failed

if [ -z "$ISSUE_ID" ] || [ -z "$STATUS" ]; then
    echo "Usage: $0 <issue-id> <status>"
    exit 1
fi

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CHECHTREE_FILE="$PROJECT_ROOT/.clawboss/checktree/CheckTree.md"

# 状态到图标的映射
case "$STATUS" in
    "pending")    ICON="⏳" ;;
    "in_progress") ICON="🔄" ;;
    "completed")  ICON="✅" ;;
    "failed")     ICON="❌" ;;
    "blocked")    ICON="🔴" ;;
    "ready")      ICON="▶️" ;;
    *)            ICON="❓" ;;
esac

echo "Syncing $ISSUE_ID status to CheckTree.md..."

# 替换 CheckTree.md 中的状态图标
# 匹配模式: [⏳|🔄|✅|❌|🔴] ISSUE-XXX
# 需要匹配各种状态图标

python3 << EOF
import re
from pathlib import Path

checktree_file = Path("$CHECHTREE_FILE")
issue_id = "$ISSUE_ID"
icon = "$ICON"

if not checktree_file.exists():
    print(f"CheckTree.md not found at {checktree_file}")
    exit(1)

content = checktree_file.read_text(encoding='utf-8')

# 状态图标列表
status_icons = ['⏳', '🔄', '✅', '❌', '🔴', '▶️', '❓']

# 构建正则表达式匹配该 issue 的行
# 匹配格式: [图标] ISSUE-XXX 或 图标 ISSUE-XXX
pattern = rf'\[([{"".join(status_icons)}])\]\s*{issue_id}|{issue_id}.*?\[([{"".join(status_icons)}])\]'

def replace_status(match):
    # 保留其他部分，只替换图标
    if match.group(1):
        return f"[{icon}] {issue_id}"
    elif match.group(2):
        return f"{issue_id} [{icon}]"
    return match.group(0)

# 使用更简单的方法：直接替换该 issue 的图标
# 查找包含 issue_id 的行并替换图标
lines = content.split('\n')
new_lines = []
found = False

for line in lines:
    if issue_id in line:
        # 替换行中的任何状态图标
        new_line = re.sub(r'\[([⏳🔄✅❌🔴▶️❓])\]', f'[{icon}]', line)
        new_lines.append(new_line)
        found = True
    else:
        new_lines.append(line)

if found:
    checktree_file.write_text('\n'.join(new_lines), encoding='utf-8')
    print(f"Updated {issue_id} -> {icon}")
else:
    print(f"Issue {issue_id} not found in CheckTree.md")

EOF

echo "Sync completed."
