#!/bin/bash
# CheckTree Orchestrator 快速开始脚本
# 运行此脚本进行初始化和演示

set -e

echo "=========================================="
echo "CheckTree Orchestrator 快速开始"
echo "=========================================="
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "Error: 需要 python3"
    exit 1
fi

# 检查 git 环境
if ! command -v git &> /dev/null; then
    echo "Error: 需要 git"
    exit 1
fi

# 1. 创建配置目录
echo "Step 1: 创建配置目录..."
mkdir -p .clawboss/config
mkdir -p .clawboss/logs
mkdir -p .clawboss/worktrees
echo "✓ 完成"

# 2. 复制配置文件
echo ""
echo "Step 2: 复制配置文件..."
if [ ! -f .clawboss/config/orchestrator.yaml ]; then
    cp .clawboss-standards/templates/orchestrator-config.yaml .clawboss/config/orchestrator.yaml
    echo "✓ 配置文件已创建: .clawboss/config/orchestrator.yaml"
else
    echo "⚠ 配置文件已存在，跳过"
fi

# 3. 检查依赖
echo ""
echo "Step 3: 检查 Python 依赖..."
python3 -c "import yaml" 2>/dev/null && echo "✓ PyYAML 已安装" || {
    echo "安装 PyYAML..."
    pip install pyyaml
}

# 4. 运行分析
echo ""
echo "Step 4: 分析项目..."
python3 .clawboss-standards/scripts/orchestrator.py analyze

# 5. 显示可用命令
echo ""
echo "=========================================="
echo "可用命令"
echo "=========================================="
echo ""
echo "# 分析依赖图"
echo "python3 .clawboss-standards/scripts/orchestrator.py analyze"
echo ""
echo "# 查看状态"
echo "python3 .clawboss-standards/scripts/orchestrator.py status"
echo ""
echo "# 启动并行开发（自动模式）"
echo "python3 .clawboss-standards/scripts/orchestrator.py run --mode=auto --max-agents=3"
echo ""
echo "# 开发特定 Issue"
echo "python3 .clawboss-standards/scripts/orchestrator.py run --issue=ISSUE-SETUP-001"
echo ""
echo "# 清理 worktrees"
echo "python3 .clawboss-standards/scripts/orchestrator.py cleanup"
echo ""
echo "# 运行集成测试"
echo "python3 .clawboss-standards/scripts/run-integration-tests.py --all"
echo ""
echo "=========================================="
echo "开始使用吧！"
echo "=========================================="
