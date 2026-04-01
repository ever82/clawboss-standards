## CheckTree - Project Issue Logic Dependency Graph

CheckTree is a tree-structured issue management system that maps the entire project. When all issues in the CheckTree are resolved, the project is complete.

## Overview

This document visualizes the issue dependency graph using Mermaid diagrams. Each issue is a node, and arrows indicate dependencies (prerequisites).

**任何时候查看 CheckTree.md 就能掌握项目的当前进展。**

## Issue Naming Rule

`ISSUE-{Module}-{NUMBER}`

## Issue Status

每个 Issue 必须包含状态字段：

| Status | Symbol | Meaning |
|--------|--------|---------|
| `pending` | ⏳ | Not started |
| `in_progress` | 🔄 | In progress |
| `completed` | ✅ | Completed |
| `blocked` | 🔴 | Blocked |

## Issue Dependency Graph

```mermaid
flowchart TD
    subgraph Setup["📋 Setup"]
        INIT001[⏳ ISSUE-SETUP-001<br/>创建 Spec 文档]
        INIT002[⏳ ISSUE-SETUP-002<br/>创建 Issues]
    end

    subgraph SetupChildren["📋 Setup Children"]
        INIT002A[⏳ ISSUE-SETUP-002A<br/>完善 CheckTree.md]
        INIT002B[⏳ ISSUE-SETUP-002B<br/>生成 Issues]
    end

    INIT001 --> INIT002
    INIT002 --> INIT002A
    INIT002 --> INIT002B

    subgraph Features["✨ Features"]
        FEAT001[⏳ ISSUE-FEAT-001<br/>{FEAT_TITLE}]
    end

    subgraph Components["🧩 Components"]
        COMP001[⏳ ISSUE-COMP-001<br/>{COMP_TITLE}]
    end

    subgraph Testing["🧪 Testing"]
        TEST001[⏳ ISSUE-TEST-001<br/>{TEST_TITLE}]
    end

    %% Default setup dependencies
    INIT002a --> FEAT001
    FEAT001 --> COMP001
    COMP001 --> TEST001
```

## Default Issues

每个新项目默认包含以下 Issue：

### ISSUE-SETUP-001: 创建 Spec 文档

- **状态**: pending
- **描述**: 创建 `.clawboss/spec/` 目录下的规格文档
- **包含子任务**:
  - [ ] CONCEPTS.md - 核心概念定义
  - [ ] PROJECT.md - 项目介绍
  - [ ] TECH_STACK.md - 技术栈
  - [ ] ARCHITECTURE.md - 架构与模块设计

### ISSUE-SETUP-002: 创建 Issues

- **状态**: pending
- **描述**: 根据 CheckTree.md 生成所有 Issue 文件
- **依赖**: ISSUE-SETUP-001
- **包含子 Issue**:
  - **ISSUE-SETUP-002A**: 完善 CheckTree.md — 细化各 Issue 的描述
  - **ISSUE-SETUP-002B**: 生成 Issues — 根据 CheckTree.md 创建所有 Issue YAML 文件

## Key Features

- **Tree Structure**: Issues form a logical dependency tree, not linear GitHub issues
- **YAML Format**: Each issue is a YAML file with structured metadata
- **Criteria-based**: Each issue contains multiple criteria (acceptance criteria) with independent status
- **Dependency Tracking**: Prerequisites define execution order
- **Visual Graph**: Mermaid diagram shows issue relationships and progress
- **Single Source of Truth**: CheckTree.md is the single source of truth for project progress
