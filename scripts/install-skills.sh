#!/bin/bash
# CheckTree Parallel Development System 安装脚本
# 运行此脚本即可为 Claude Code 安装所有 CheckTree Skills

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STANDARDS_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "CheckTree Skills 安装脚本"
echo "=========================================="
echo ""

# 1. 确定 Claude Code skills 目录
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"

if [ ! -d "$CLAUDE_SKILLS_DIR" ]; then
    echo "Error: Claude Code skills 目录不存在"
    echo "请先安装 Claude Code"
    exit 1
fi

echo "1. 创建 Skills 目录..."

# 2. 复制 Skills 文件
SKILLS=(
    "checktree-status"
    "checktree-analyze"
    "checktree-run"
    "checktree-next"
    "checktree-cleanup"
    "checktree-itest"
    "checktree-milestone"
)

for skill in "${SKILLS[@]}"; do
    SKILL_SRC="$STANDARDS_DIR/.claude/skills/$skill"
    SKILL_DST="$CLAUDE_SKILLS_DIR/$skill"

    if [ -d "$SKILL_SRC" ]; then
        echo "   安装 $skill..."
        mkdir -p "$SKILL_DST"
        cp "$SKILL_SRC/SKILL.md" "$SKILL_DST/"
    else
        echo "   警告: $skill 源文件不存在，跳过"
    fi
done

echo ""
echo "2. 安装完成!"
echo ""
echo "Skills 安装在: $CLAUDE_SKILLS_DIR"
echo ""

# 3. 显示可用的 Skills
echo "=========================================="
echo "已安装的 CheckTree Skills:"
echo "=========================================="
for skill in "${SKILLS[@]}"; do
    if [ -f "$CLAUDE_SKILLS_DIR/$skill/SKILL.md" ]; then
        echo "  ✓ /$skill"
    fi
done

echo ""
echo "=========================================="
echo "使用说明"
echo "=========================================="
echo ""
echo "在 Claude Code 中直接使用 slash 命令:"
echo "  /checktree-status    - 查看开发状态"
echo "  /checktree-analyze   - 分析依赖图"
echo "  /checktree-run       - 启动并行开发"
echo "  /checktree-next       - 开发特定 Issue"
echo "  /checktree-cleanup    - 清理 worktrees"
echo ""
echo "带参数使用:"
echo "  /checktree-run --max-agents=3"
echo "  /checktree-next ISSUE-SETUP-001"
echo "  /checktree-itest ISSUE-001 ISSUE-002"
echo "  /checktree-milestone MILESTONE-1"
echo ""
echo "=========================================="
echo "注意: 如果 Skills 不生效，请重启 Claude Code"
echo "=========================================="
