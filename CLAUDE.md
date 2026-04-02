# CheckTree Orchestrator Skills

本文档定义 Claude Code 可用的 CheckTree 相关 Skills。

## Skill 定义

### checktree-status

显示当前所有 Issues 的状态和并行执行情况。

```
/checktree-status
```

**实现**: 调用 `python .clawboss-standards/scripts/orchestrator.py status`

---

### checktree-analyze

分析 CheckTree.md 中的依赖图，显示可执行和被阻塞的 Issues。

```
/checktree-analyze
```

**实现**: 调用 `python .clawboss-standards/scripts/orchestrator.py analyze`

---

### checktree-run

启动并行开发编排器，自动发现并执行 ready 状态的 Issues。

```
/checktree-run [--max-agents=N]
```

**参数**:
- `--max-agents`: 最大并行数（可选，默认从配置读取）

**实现**: 调用 `python .clawboss-standards/scripts/orchestrator.py run --mode=auto`

---

### checktree-next

手动启动下一个可用的 Issue 开发。

```
/checktree-next [ISSUE-ID]
```

**参数**:
- `ISSUE-ID`: 可选的特定 Issue ID，不提供则自动选择

**实现**: 调用 `python .clawboss-standards/scripts/orchestrator.py run --issue=ISSUE-ID`

---

### checktree-cleanup

清理所有 worktrees 和临时分支。

```
/checktree-cleanup [--force]
```

**参数**:
- `--force`: 强制清理正在运行的 worktrees

**实现**: 调用 `python .clawboss-standards/scripts/orchestrator.py cleanup`

---

### checktree-milestone

运行里程碑验收测试。

```
/checktree-milestone MILESTONE-ID
```

**参数**:
- `MILESTONE-ID`: 里程碑 ID，如 `MILESTONE-1`

**实现**: 运行 E2E 测试并生成里程碑报告

---

### checktree-test

在当前 Issue 的 worktree 中运行测试。

```
/checktree-test [unit|integration|e2e]
```

**参数**:
- 测试类型: `unit`（默认）、`integration`、`e2e`

**实现**: 读取 Issue YAML 中的测试配置并执行

---

## 快捷方式

### 开发下一个 Issue

```
# 直接开始开发
/checktree-next

# 或使用简写
/next
```

### 查看进度

```
# 查看所有状态
/checktree-status

# 简写
/status
```

---

## 使用示例

### 场景 1: 开始新的一天

```
User: /checktree-status

Claude: [显示当前状态...]
  - Ready: 3 Issues
  - In Progress: 1 Issue
  - Blocked: 122 Issues

User: /checktree-run

Claude: [启动并行开发，最多 3 个 Agent]
```

### 场景 2: 开发特定 Issue

```
User: /checktree-next ISSUE-CORE-001

Claude: [创建 worktree，启动 Agent 开发该 Issue]
```

### 场景 3: 运行测试

```
User: /checktree-test unit

Claude: [读取 Issue YAML，执行单元测试]
```

---

## 配置 Skills

在项目的 `CLAUDE.md` 中添加：

```markdown
# CheckTree Development Skills

## Available Commands

| Command | Description |
|---------|-------------|
| `/checktree-status` | 显示当前开发状态 |
| `/checktree-analyze` | 分析依赖图 |
| `/checktree-run` | 启动并行开发 |
| `/checktree-next` | 开始下一个 Issue |
| `/checktree-cleanup` | 清理 worktrees |
| `/checktree-milestone` | 运行里程碑测试 |
| `/checktree-test` | 运行测试 |

## Shortcuts

| Shortcut | Alias for |
|----------|-----------|
| `/status` | `/checktree-status` |
| `/next` | `/checktree-next` |
| `/run` | `/checktree-run` |

## Configuration

- Max parallel agents: 3
- Auto cleanup: false
- Test trigger: batch
```

---

## 实现提示

这些 Skills 可以通过以下方式实现：

1. **Shell 脚本包装器**: 创建 `.clawboss-standards/skills/checktree-*.sh`
2. **Python CLI**: 主入口 `orchestrator.py`
3. **Claude Code native commands**: 在 `settings.json` 中配置

示例 `settings.json` 配置：

```json
{
  "customCommands": {
    "checktree-status": {
      "description": "Show CheckTree development status",
      "script": "python .clawboss-standards/scripts/orchestrator.py status"
    },
    "checktree-analyze": {
      "description": "Analyze dependency graph",
      "script": "python .clawboss-standards/scripts/orchestrator.py analyze"
    },
    "checktree-run": {
      "description": "Start parallel development",
      "script": "python .clawboss-standards/scripts/orchestrator.py run --mode=auto"
    },
    "checktree-next": {
      "description": "Start next ready issue",
      "script": "python .clawboss-standards/scripts/orchestrator.py run --issue=${ARGUMENT}"
    },
    "checktree-cleanup": {
      "description": "Clean up worktrees",
      "script": "python .clawboss-standards/scripts/orchestrator.py cleanup"
    }
  }
}
```
