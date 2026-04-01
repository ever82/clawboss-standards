# ClawBoss Templates

This directory contains all standard Markdown template files used by the ClawBoss project. The ClawBoss program uses these templates to initialize new projects or generate standard files.

## Development Cycle

所有项目都遵循以下开发周期：

### 1. 创建 CheckTree.md

每个新项目从创建 `checktree/CheckTree.md` 开始。**任何时候查看 CheckTree.md 就能掌握项目的当前进展**，它是项目的单一真相来源。

CheckTree.md 模板中的每个 Issue 必须包含状态字段（如 `pending`/`in_progress`/`completed`），以便追踪进度。

1. **创建 Spec 文档** — 创建 `.clawboss/spec/` 下的所有规格文档
2. **创建 Issues** — 根据 CheckTree.md 生成所有 Issue，包含两个子 Issue：
   - **完善 CheckTree.md** — 细化 CheckTree.md 中的 Issue 描述
   - **生成 Issues** — 根据 CheckTree.md 生成 `.clawboss/checktree/issues/` 下的所有 Issue 文件

### 2. 创建 Issue 文件

每个 Issue 都是一个独立的工作单元，存储在 `.clawboss/checktree/issues/ISSUE-{ID}/` 目录下。

### 3. 根据 Issues 开发

开发人员逐个 Issue 创建 Task，逐个完成。每个 Task 对应一个 Claude Code 会话。

### Issue 类型

| Issue 类型 | 说明 |
|-----------|------|
| Spec 文档 | 创建规格文档 (CONCEPTS.md, PROJECT.md, TECH_STACK.md, ARCHITECTURE.md) |
| CheckTree | 完善 CheckTree.md |
| Issues 生成 | 根据 CheckTree.md 生成所有 Issue |
| 功能开发 | 具体功能开发 |

### 流程图

```
创建 CheckTree.md
       │
       ├── Issue: 创建 Spec 文档
       │
       └── Issue: 创建 Issues
                   │
                   ├── 子 Issue: 完善 CheckTree.md
                   │
                   └── 子 Issue: 生成 Issues
                                  │
                                  └── 逐个 Issue 开发
                                        │
                                        └── 逐个 Task 执行
```

## Template Documentation

| Document | Description |
|----------|-------------|
| [project.md](./project.md) | Project-level and user-level templates, file structure convention |
| [issue.md](./issue.md) | CheckTree issue system, YAML structure, naming conventions |
| [task.md](./task.md) | Task system for tracking Claude Code sessions within issues |
# Project Templates

This file contains all project-level templates used by the ClawBoss system.

## Template List

### Project-level Templates (in `.clawboss/` directory)

| Template File | Purpose | Output Location |
|--------------|---------|-----------------|
| `checktree.md` | CheckTree issue dependency graph | `.clawboss/checktree/CheckTree.md` |
| `issue.yaml` | Issue file template (YAML format) | `.clawboss/checktree/issues/ISSUE-{ID}/ISSUE-{ID}~{slug}.yaml` |
| `task.yaml` | Task file template (YAML format) | `.clawboss/checktree/issues/ISSUE-{ID}/tasks/TASK-{NUMBER}~{slug}.yaml` |
| `concepts.md` | Core concepts definition | `.clawboss/spec/CONCEPTS.md` |
| `project.md` | Project introduction | `.clawboss/spec/PROJECT.md` |
| `tech_stack.md` | Technology stack | `.clawboss/spec/TECH_STACK.md` |
| `architecture.md` | Architecture & module design | `.clawboss/spec/ARCHITECTURE.md` |


### User-level Templates (in `~/.clawboss/` directory)

| Template File | Purpose | Output Location |
|--------------|---------|-----------------|
| `user.md` | User profile | `~/.clawboss/user.md` |
| `settings.json` | User settings | `~/.clawboss/settings.json` |

## Variable Substitution Rules

Templates use `{VARIABLE}` format placeholders, which the ClawBoss program automatically replaces based on context.

## Custom Templates

Users can place custom templates in the `~/.clawboss/templates/` directory to override default templates. ClawBoss will prioritize user custom templates.

## References

- [Project Documentation](../.clawboss/spec/PROJECT.md)
- [Core Concepts](../.clawboss/spec/CONCEPTS.md)
