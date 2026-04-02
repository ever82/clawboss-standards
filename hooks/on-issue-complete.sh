#!/bin/bash
# CheckTree Issue 完成钩子
# 此脚本在 Issue 的所有 Task 完成后触发

set -e

ISSUE_ID="$1"

if [ -z "$ISSUE_ID" ]; then
    echo "Usage: $0 <issue-id>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "CheckTree Issue Completion Hook"
echo "=========================================="
echo "Issue: $ISSUE_ID"
echo ""

# 1. 更新 Issue YAML 状态
ISSUE_FILE=$(find "$PROJECT_ROOT/.clawboss/checktree/issues/$ISSUE_ID" -name "*.yaml" | head -1)

if [ -f "$ISSUE_FILE" ]; then
    echo "Updating Issue status..."
    python3 << EOF
import yaml
from datetime import datetime

issue_file = "$ISSUE_FILE"

with open(issue_file, 'r') as f:
    data = yaml.safe_load(f)

# 更新状态为 completed
data['status'] = 'completed'
data['completed_at'] = datetime.now().isoformat()

# 标记所有 criteria 为 passed
if 'criteria' in data:
    for criterion in data['criteria']:
        criterion['status'] = 'passed'

with open(issue_file, 'w') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)

print(f"Issue {data.get('id', 'unknown')} marked as completed")
EOF
fi

# 2. 更新 CheckTree.md 中的状态图标
echo "Updating CheckTree.md..."
"$SCRIPT_DIR/sync-checktree.sh" "$ISSUE_ID" "completed"

# 3. 查找并启动下一个可执行的 Issue
echo "Checking for next ready issues..."
python3 << 'EOF'
import yaml
from pathlib import Path
from typing import Dict, List, Set

issues_dir = Path(".clawboss/checktree/issues")

def load_issues() -> Dict:
    issues = {}
    for issue_dir in issues_dir.iterdir():
        if not issue_dir.is_dir():
            continue
        yaml_files = list(issue_dir.glob("*.yaml"))
        if yaml_files:
            with open(yaml_files[0], 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    issues[data['id']] = data
    return issues

def get_ready_issues(issues: Dict) -> List[str]:
    """获取所有可以开始开发的 Issues"""
    ready = []
    for issue_id, data in issues.items():
        if data.get('status') not in ['pending', 'blocked']:
            continue

        # 检查所有依赖是否完成
        deps = data.get('prerequisites', [])
        deps_completed = all(
            issues.get(dep, {}).get('status') == 'completed'
            for dep in deps
        )

        if deps_completed:
            ready.append(issue_id)

    return ready

issues = load_issues()
ready = get_ready_issues(issues)

print(f"Found {len(ready)} ready issues:")
for issue_id in ready[:5]:
    print(f"  - {issue_id}")
if len(ready) > 5:
    print(f"  ... and {len(ready) - 5} more")

# 如果有 ready 的 issues，可以启动编排器
if ready:
    print("\nTo start next issues, run:")
    print(f"  python .clawboss-standards/scripts/orchestrator.py run --mode=auto")
EOF

# 4. 通知（如果配置了）
CONFIG_FILE="$PROJECT_ROOT/.clawboss/config/orchestrator.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo -e "${GREEN}Issue $ISSUE_ID completed!${NC}"
fi

echo ""
echo "Hook completed."
