# CheckTree 并行开发系统 (CheckTree Parallel Development System)

## 概述

一个可配置的、自主运行的 Issue 开发系统，支持：
- 并行开发多个无依赖的 Issue
- 每个 Issue 独立的 worktree
- 可配置的最大并行数量
- 集成测试/E2E 测试在主分支执行
- 自动依赖解析和调度

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator (Python)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Dependency  │  │   Parallel   │  │    Worktree Manager  │  │
│  │    Parser    │  │   Scheduler  │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
   │ Agent 1 │           │ Agent 2 │           │ Agent 3 │
   │ Worktree│           │ Worktree│           │ Worktree│
   │ Issue-A │           │ Issue-B │           │ Issue-C │
   └────┬────┘           └────┬────┘           └────┬────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Merge & Test     │
                    │  (Main Branch)    │
                    └───────────────────┘
```

## 核心概念

### 1. Issue 状态流转

```
pending → analyzing → ready → in_progress → review → merge_pending
                                           ↓
                                      completed
```

### 2. 并行度控制

通过配置 `max_parallel_agents` 控制同时运行的 Issue 数量（默认 3）。

### 3. Worktree 策略

- 每个正在开发的 Issue 拥有独立的 git worktree
- Worktree 命名: `.clawboss/worktrees/{issue-id}/`
- 开发完成后，worktree 可以选择保留或删除

### 4. 测试策略

| 测试类型 | 执行位置 | 触发时机 |
|----------|----------|----------|
| 单元测试 | Issue Worktree | 开发过程中 |
| 集成测试 | Main Branch (临时合并) | Issue 完成后 |
| E2E 测试 | Main Branch (临时合并) | 一批 Issues 完成后 |
| 验收测试 | Main Branch | 里程碑节点 |

## 配置说明

### orchestrator.yaml

```yaml
parallel:
  max_agents: 3                    # 最大并行数
  max_retries: 2                   # 失败重试次数
  timeout_minutes: 120             # 单个 Issue 超时

worktree:
  base_path: ".clawboss/worktrees"
  auto_cleanup: false              # 完成后是否自动删除 worktree
  keep_on_failure: true            # 失败时保留 worktree 以便调试

testing:
  integration:
    auto_merge: true               # 自动创建临时合并分支
    branch_prefix: "test/integration"
  e2e:
    trigger: "milestone"           # milestone | batch | manual
    batch_size: 5                  # 每批 Issues 数量

notifications:
  on_issue_complete: true
  on_failure: true
  on_milestone: true
```

## 命令行接口

```bash
# 启动编排器（开发模式 - 自动执行 ready 状态的 Issues）
python -m clawboss.orchestrator run --mode=auto

# 启动编排器（建议模式 - 询问用户确认）
python -m clawboss.orchestrator run --mode=interactive

# 只分析依赖图，不执行
python -m clawboss.orchestrator analyze

# 执行特定 Issue
python -m clawboss.orchestrator run --issue=ISSUE-CORE-001

# 查看当前状态
python -m clawboss.orchestrator status

# 清理所有 worktrees
python -m clawboss.orchestrator cleanup
```

## Claude Code Hooks 集成

### 1. Post-Completion Hook

在 Claude Code 完成一个 Task 后自动触发：

```json
{
  "hooks": {
    "post_completion": ".clawboss/hooks/on-task-complete.sh"
  }
}
```

### 2. Issue 状态同步

Task 完成后自动更新 Issue 状态并触发下一个可用 Issue。

## Claude Code Skills 集成

### /checktree-run

触发编排器运行，自动发现并执行 ready 状态的 Issues。

### /checktree-status

显示当前所有 Issues 的状态和并行执行情况。

### /checktree-next

手动触发下一个可用的 Issue 开发。

## 目录结构

```
.clawboss/
├── orchestrator/
│   ├── __init__.py
│   ├── main.py                 # CLI 入口
│   ├── scheduler.py            # 并行调度器
│   ├── worktree_manager.py     # Worktree 管理
│   ├── dependency_graph.py     # 依赖图解析
│   ├── agent_factory.py        # Agent 创建
│   └── config.py               # 配置管理
├── hooks/
│   ├── on-task-complete.sh     # Task 完成钩子
│   ├── on-issue-complete.sh    # Issue 完成钩子
│   └── on-merge-request.sh     # 合并请求钩子
├── config/
│   └── orchestrator.yaml       # 编排器配置
└── worktrees/                  # Issue worktrees (gitignored)
    ├── ISSUE-CORE-001/
    ├── ISSUE-CORE-002/
    └── ...
```

## 沉淀到 clawboss-standards

### 标准文件

1. `templates/orchestrator-config.yaml` - 默认配置模板
2. `sop/parallel-development.md` - 并行开发 SOP
3. `scripts/orchestrator.py` - 编排器脚本
4. `hooks/task-complete.sh` - 完成钩子模板

## 工作流程

### 1. 初始化阶段

```
读取 CheckTree.md
  ↓
解析所有 Issue YAML
  ↓
构建依赖图
  ↓
标记 ready 状态的 Issues（无未完成的依赖）
```

### 2. 执行阶段

```
while 存在 pending/ready 的 Issues:
    获取当前可并行的 Issues (ready 状态)
    
    while 运行中的 Agents < max_parallel:
        取出下一个 ready Issue
        创建 worktree
        启动 Agent 开发 Issue
    
    等待任意 Agent 完成
    更新依赖图
    标记新 ready 的 Issues
```

### 3. 测试阶段

```
当一批 Issues 完成:
    创建临时合并分支 (main + completed issues)
    运行集成测试
    运行 E2E 测试
    
    if 测试通过:
        标记 Issues 为 completed
        可选: 自动合并到 main
    else:
        标记 Issues 为 failed
        保留 worktree 供调试
```

## 实现要点

### 1. Agent 启动方式

使用 Claude Code 的 `agent` 命令或 Agent SDK 启动独立会话：

```python
# 伪代码
claude_agent = Agent.create(
    name=f"developer-{issue_id}",
    worktree=worktree_path,
    prompt=build_issue_prompt(issue_data),
    mode="auto"  # 或 "plan" 根据配置
)
```

### 2. 状态同步机制

- Issue 状态存储在 YAML 文件中
- 使用文件锁或原子操作确保并发安全
- Agent 完成后更新 YAML 状态

### 3. 依赖解析

从 CheckTree.md 的 Mermaid 图解析依赖关系：

```python
def parse_dependencies(checktree_md):
    """解析 Mermaid 图中的依赖关系"""
    # 提取 --> 箭头关系
    # 构建 DAG
    # 拓扑排序得到执行顺序
```

### 4. 测试流水线

```python
def run_integration_tests(issue_branches):
    """在临时分支上运行集成测试"""
    # 1. 创建临时分支 test/integration-{timestamp}
    # 2. 合并所有 issue 分支
    # 3. 运行集成测试命令
    # 4. 返回结果
    # 5. 清理临时分支
```

## 扩展性设计

### 1. 插件系统

支持自定义钩子：

```yaml
hooks:
  pre_issue_start: "scripts/notify-start.sh"
  post_issue_complete: "scripts/notify-complete.sh"
  on_test_failure: "scripts/handle-test-failure.sh"
```

### 2. 多策略调度

```yaml
scheduler:
  strategy: "parallel"  # parallel | priority | milestone_first
  priority_rules:
    - "ISSUE-INFRA-*"    # 基础设施优先
    - "ISSUE-CORE-*"     # 核心功能其次
```

### 3. 资源限制

```yaml
resources:
  max_disk_gb: 50           # worktree 总大小限制
  max_memory_gb: 16         # 单个 Agent 内存限制
  max_cpu_percent: 80       # CPU 使用率限制
```

## 使用示例

### 示例 1: 自动开发整个项目

```bash
# 配置并行度
echo "parallel:\n  max_agents: 3" > .clawboss/config/orchestrator.yaml

# 启动编排器
python -m clawboss.orchestrator run --mode=auto

# 系统会自动:
# 1. 分析所有 Issues
# 2. 并行开发最多 3 个无依赖的 Issues
# 3. 完成后自动运行集成测试
# 4. 成功后合并到 main
```

### 示例 2: 仅开发特定模块

```bash
python -m clawboss.orchestrator run --module=CORE --max-agents=2
```

### 示例 3: 手动控制模式

```bash
# 查看可执行的 Issues
python -m clawboss.orchestrator queue

# 手动启动特定 Issue
python -m clawboss.orchestrator start ISSUE-CORE-001

# 查看运行中的 Agents
python -m clawboss.orchestrator agents
```

## 与现有系统集成

### 与 CheckTree.md 集成

编排器直接读取 CheckTree.md 中的 Mermaid 图解析依赖关系，无需额外配置。

### 与 Issue YAML 集成

读取 `.clawboss/checktree/issues/` 下的 YAML 文件，实时更新状态。

### 与 CLAUDE.md 集成

在 CLAUDE.md 中添加编排器指令：

```markdown
# 并行开发
使用 orchestrator 管理多个 Issue 的并行开发：
- 最大并行数: 3
- 自动测试: 启用
- 清理策略: 保留失败的 worktree
```

## 总结

这个系统提供：

1. **自动化** - 自动发现、调度、执行 Issues
2. **并行化** - 最大化利用资源，加速开发
3. **隔离性** - 每个 Issue 独立 worktree，互不干扰
4. **可靠性** - 集成测试保护主分支
5. **可观测** - 实时状态和进度跟踪
6. **可配置** - 灵活的配置适应不同项目需求
