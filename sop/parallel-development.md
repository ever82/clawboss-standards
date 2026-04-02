# CheckTree 并行开发 SOP

## 概述

本文档描述如何使用 CheckTree Orchestrator 实现多个 Issue 的并行开发。

## 前置条件

1. CheckTree.md 已创建并包含所有 Issues
2. 所有 Issue YAML 文件已生成（参考 ISSUE-SETUP-002）
3. Claude Code CLI 已安装并可用

## 快速开始

### 1. 初始化配置

```bash
# 复制默认配置
mkdir -p .clawboss/config
cp .clawboss-standards/templates/orchestrator-config.yaml .clawboss/config/orchestrator.yaml

# 根据需要编辑配置
vim .clawboss/config/orchestrator.yaml
```

### 2. 分析项目

```bash
# 查看可执行的 Issues
python .clawboss-standards/scripts/orchestrator.py analyze
```

输出示例：
```
============================================================
DEPENDENCY ANALYSIS
============================================================

Status Distribution:
  pending: 126
  ready: 3
  blocked: 123

Ready to start (3):
  - ISSUE-SETUP-001: 创建 Spec 文档
  - ISSUE-SETUP-002: 创建 Issues
  - ISSUE-CORE-001: Behavior 实体和类型定义

Blocked (123):
  - ISSUE-CORE-002 (waiting for: ISSUE-CORE-001, ISSUE-INFRA-003B)
  ...
```

### 3. 启动并行开发

```bash
# 自动模式（自动开始所有 ready 的 Issues）
python .clawboss-standards/scripts/orchestrator.py run --mode=auto

# 或指定最大并行数
python .clawboss-standards/scripts/orchestrator.py run --mode=auto --max-agents=3
```

## 配置详解

### 并行度配置

```yaml
parallel:
  max_agents: 3  # 最大并行数，建议 2-5
```

选择依据：
- 机器 CPU 核心数
- 内存大小（每个 Agent 约需 2-4GB）
- 项目复杂度
- 测试运行时间

### Worktree 配置

```yaml
worktree:
  base_path: ".clawboss/worktrees"  # Worktree 存放位置
  auto_cleanup: false               # 完成后自动清理
  keep_on_failure: true             # 失败时保留以便调试
```

### 测试配置

```yaml
testing:
  integration:
    auto_merge: true     # 自动在临时分支运行集成测试
    batch_size: 5        # 每批处理 5 个 Issues
  e2e:
    trigger: "milestone"  # 只在里程碑节点运行 E2E
```

## 日常工作流

### 场景 1: 每日开发

```bash
# 1. 查看当前状态
python .clawboss-standards/scripts/orchestrator.py status

# 2. 启动/继续开发
python .clawboss-standards/scripts/orchestrator.py run --mode=auto
```

### 场景 2: 开发特定模块

```bash
# 只开发 CORE 模块
python .clawboss-standards/scripts/orchestrator.py run \
    --issue=ISSUE-CORE-001 \
    --max-agents=2
```

### 场景 3: 调试失败的 Issue

```bash
# 查看失败的 Issues
grep "failed" .clawboss/logs/failed-tasks.log

# 进入失败的 worktree 调试
cd .clawboss/worktrees/ISSUE-CORE-002

# 修复后手动更新状态
python .clawboss-standards/scripts/orchestrator.py status
```

### 场景 4: 清理环境

```bash
# 清理所有 worktrees
python .clawboss-standards/scripts/orchestrator.py cleanup

# 只清理特定的
git worktree remove .clawboss/worktrees/ISSUE-CORE-001
```

## Claude Code Hooks 集成

### 配置 Hooks

在 `~/.claude/settings.json` 或项目 `CLAUDE.md` 中配置：

```json
{
  "hooks": {
    "post_completion": ".clawboss-standards/hooks/on-task-complete.sh"
  }
}
```

### Hook 工作流程

```
Task 完成
    ↓
on-task-complete.sh
    ↓
┌─────────────────────────────────────┐
│ 1. 更新 Task YAML 状态              │
│ 2. 检查 Issue 是否所有 Task 完成     │
│ 3. 同步 CheckTree.md 状态            │
│ 4. 如果 Issue 完成，触发下一批      │
└─────────────────────────────────────┘
```

## Claude Code Skills 集成

### 可用 Skills

| Skill | 功能 |
|-------|------|
| `/checktree-status` | 查看当前开发状态 |
| `/checktree-next` | 启动下一个可用的 Issue |
| `/checktree-run` | 启动编排器运行 |
| `/checktree-analyze` | 分析依赖图 |

### 配置 Skills

在 `CLAUDE.md` 中添加：

```markdown
# CheckTree Skills

Available commands:
- `/checktree-status` - 显示当前开发状态
- `/checktree-next` - 开始下一个 Issue
- `/checktree-run` - 启动并行开发

使用 orchestrator 管理 Issue 开发：
- 最大并行数: ${max_agents}
- 自动测试: ${auto_test}
```

## 测试策略

### 分层测试

```
┌─────────────────────────────────────────────┐
│ E2E 测试 (Main Branch)                      │
│ 触发: 里程碑节点或手动触发                    │
├─────────────────────────────────────────────┤
│ 集成测试 (临时合并分支)                       │
│ 触发: 每批 Issues 完成                       │
├─────────────────────────────────────────────┤
│ 单元测试 (Issue Worktree)                    │
│ 触发: 开发过程中                             │
└─────────────────────────────────────────────┘
```

### 运行集成测试

```bash
# 手动触发集成测试
python .clawboss-standards/scripts/run-integration-tests.py \
    --issues ISSUE-CORE-001 ISSUE-CORE-002 ISSUE-CORE-003
```

### 运行 E2E 测试

```bash
# 在里程碑节点运行
python .clawboss-standards/scripts/run-e2e-tests.py \
    --milestone MILESTONE-1
```

## 故障排除

### Issue 被错误标记为 blocked

```bash
# 检查依赖关系
python .clawboss-standards/scripts/orchestrator.py analyze

# 手动更新状态
# 编辑 .clawboss/checktree/issues/ISSUE-XXX/ISSUE-XXX~xxx.yaml
# 将 status: blocked 改为 status: pending
```

### Agent 无响应

```bash
# 查看运行中的进程
ps aux | grep claude

# 手动终止
kill <PID>

# 重试 Issue
python .clawboss-standards/scripts/orchestrator.py run --issue=ISSUE-XXX
```

### Worktree 冲突

```bash
# 查看所有 worktrees
git worktree list

# 移除冲突的 worktree
git worktree remove .clawboss/worktrees/ISSUE-XXX

# 重新创建
python .clawboss-standards/scripts/orchestrator.py run --issue=ISSUE-XXX
```

## 最佳实践

1. **并行度选择**
   - 开发阶段: 3-5 个并行
   - 调试阶段: 1-2 个并行
   - CI 机器: 2-3 个并行

2. **提交策略**
   - 每个 Task 完成后提交
   - Issue 完成后打标签
   - 里程碑完成后创建 Release

3. **测试策略**
   - 单元测试必须在 worktree 中通过
   - 集成测试通过后再合并
   - E2E 测试作为最终验收

4. **监控**
   - 定期查看 `python orchestrator.py status`
   - 关注 `.clawboss/logs/` 中的日志
   - 失败的 Issue 及时处理

## 参考链接

- [并行开发系统设计](../docs/parallel-development-system.md)
- [Orchestrator 配置模板](../templates/orchestrator-config.yaml)
- [Hook 脚本](../hooks/)
