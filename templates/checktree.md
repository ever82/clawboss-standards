## CheckTree - Project Issue Logic Dependency Graph

CheckTree is a tree-structured issue management system that maps the entire project. When all issues in the CheckTree are resolved, the project is complete.

## Overview

This document visualizes the issue dependency graph using Mermaid diagrams. Each issue is a node, and arrows indicate dependencies (prerequisites).

issue name rule:ISSUE-{Module}-{NUMBER}


### Key Features

- **Tree Structure**: Issues form a logical dependency tree, not linear GitHub issues
- **YAML Format**: Each issue is a YAML file with structured metadata
- **Criteria-based**: Each issue contains multiple criteria (acceptance criteria) with independent status
- **Dependency Tracking**: Prerequisites define execution order
- **Visual Graph**: Mermaid diagram shows issue relationships and progress
- **Test Strategy**: Five-level testing (unit/integration/e2e/agent/human)
## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🔄 | In Progress |
| ⏳ | Pending |
| 🔴 | Blocked |

## Issue Dependency Graph

```mermaid
flowchart TD
    subgraph Infrastructure["🏗️ Infrastructure"]
        INFRA001[⏳ ISSUE-INFRA-1<br/>{INFRA_TITLE}]
        INFRA002[⏳ ISSUE-INFRA-2<br/>{INFRA_TITLE_2}]
    end

    subgraph Features["✨ Features"]
        FEAT001[⏳ ISSUE-FEAT-1<br/>{FEAT_TITLE}]
        FEAT002[⏳ ISSUE-FEAT-2<br/>{FEAT_TITLE_2}]
    end

    subgraph Components["🧩 Components"]
        COMP001[⏳ ISSUE-COMP-1<br/>{COMP_TITLE}]
        COMP002[⏳ ISSUE-COMP-2<br/>{COMP_TITLE_2}]
    end

    subgraph Testing["🧪 Testing"]
        TEST001[⏳ ISSUE-TEST-1<br/>{TEST_TITLE}]
        TEST002[⏳ ISSUE-TEST-2<br/>{TEST_TITLE_2}]
    end

    subgraph Milestones["🎯 Milestones"]
        MILESTONE001[⏳ MILESTONE-1<br/>{MILESTONE_TITLE}]
    end

    %% Dependencies
    INFRA001 --> FEAT001
    INFRA002 --> COMP001
    FEAT001 --> COMP001
    COMP001 --> TEST001
    COMP002 --> TEST002
    TEST001 --> MILESTONE001
    TEST002 --> MILESTONE001
```



