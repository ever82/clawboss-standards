#!/bin/bash
# CheckTree Task 完成钩子
# 此脚本在 Claude Code 完成一个 Task 后自动触发
# 使用方式: 配置到 Claude Code settings.json 的 hooks.post_completion

set -e

# 获取当前 Task 信息
TASK_FILE="$1"
ISSUE_ID="$2"
STATUS="$3"  # completed | failed

if [ -z "$TASK_FILE" ] || [ -z "$ISSUE_ID" ]; then
    echo "Usage: $0 <task-file> <issue-id> <status>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "CheckTree Task Completion Hook"
echo "=========================================="
echo "Task: $TASK_FILE"
echo "Issue: $ISSUE_ID"
echo "Status: $STATUS"
echo ""

# 1. 更新 Task YAML 状态
if [ -f "$TASK_FILE" ]; then
    echo "Updating Task status..."
    # 使用 Python 更新 YAML
    python3 << EOF
import yaml
from datetime import datetime

task_file = "$TASK_FILE"
status = "$STATUS"

with open(task_file, 'r') as f:
    data = yaml.safe_load(f)

data['status'] = status
data['completed_at'] = datetime.now().isoformat()

# 如果成功，标记完成
if status == 'completed':
    data['result'] = 'Task completed successfully'

with open(task_file, 'w') as f:
    yaml.dump(data, f, allow_unicode=True)

print(f"Task {data.get('id', 'unknown')} marked as {status}")
EOF
fi

# 2. 检查 Issue 的所有 Task 是否都已完成
ISSUE_DIR="$PROJECT_ROOT/.clawboss/checktree/issues/$ISSUE_ID"
TASKS_DIR="$ISSUE_DIR/tasks"

if [ -d "$TASKS_DIR" ]; then
    echo "Checking all tasks for $ISSUE_ID..."

    # 统计 Task 状态
    COMPLETED=$(find "$TASKS_DIR" -name "TASK-*.yaml" -exec grep -l "status: completed" {} \; | wc -l)
    TOTAL=$(find "$TASKS_DIR" -name "TASK-*.yaml" | wc -l)

    echo "Tasks completed: $COMPLETED / $TOTAL"

    # 如果所有 Task 都完成了，触发 Issue 完成流程
    if [ "$COMPLETED" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
        echo -e "${GREEN}All tasks completed for $ISSUE_ID${NC}"

        # 调用 Issue 完成钩子
        "$SCRIPT_DIR/on-issue-complete.sh" "$ISSUE_ID"
    fi
fi

# 3. 同步状态到 CheckTree.md（更新图标）
echo "Updating CheckTree.md..."
"$SCRIPT_DIR/sync-checktree.sh" "$ISSUE_ID" "$STATUS"

# 4. 如果失败，记录日志
if [ "$STATUS" == "failed" ]; then
    echo -e "${RED}Task failed for $ISSUE_ID${NC}"
    LOG_FILE="$PROJECT_ROOT/.clawboss/logs/failed-tasks.log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $ISSUE_ID - $TASK_FILE" >> "$LOG_FILE"
fi

echo ""
echo "Hook completed."
