# {PROJECT_NAME} - Project Introduction

## Project Name
{PROJECT_NAME}

## Project Location
- Local Path: {PROJECT_PATH}

## Project Description
{PROJECT_DESCRIPTION}

## Core Values
1. {VALUE_1}
2. {VALUE_2}
3. {VALUE_3}
4. {VALUE_4}

## Directory Structure
```
~/.clawboss/                     # User-level config (global)
├── user.md                     # User profile + preferences
├── projects.md                 # Project list
└── settings.json               # Global settings (LLM API key, etc.)

~/my-project/                   # Project directory
└── .clawboss/                   # Project-level config
    ├── checktree/
    │   ├── CheckTree.md        # Issue dependency graph (Mermaid)
    │   └── issues/             # Issue folders (one per issue)
    │       ├── ISSUE-{MODULE}-{NUMBER}/
    │       │   ├── ISSUE-{MODULE}-{NUMBER}~{slug}.yaml   # Issue definition
    │       │   └── tasks/                                  # Task files (one per session)
    │       │       ├── TASK-001~{slug}.yaml
    │       │       └── TASK-002~{slug}.yaml
    │       └── ...
    ├── spec/
    │   ├── CONCEPTS.md         # Core concepts
    │   ├── PROJECT.md          # Project introduction
    │   ├── TECH_STACK.md       # Technology stack
    │   └── ARCHITECTURE.md     # Architecture & module design
    ├── knowledge/              # Project knowledge
    └── sop/
        ├── SOP.md              # SOP outline
        └── SOP-XXX.md          # SOP files
```

## Content ID Convention
All content uses globally unique IDs in the format `TYPE-NAME-NUMBER`:
- ISSUE: ISSUE-{PROJECT}-001
- GOAL: GOAL-USER-001
- SOP: SOP-{PROJECT}-001

## Technology Stack

### Backend
| Component | Choice | Description |
|-----------|--------|-------------|
| **Language** | {LANGUAGE} | {REASON} |
| **Runtime Mode** | {RUNTIME_MODE} | {DESCRIPTION} |

### Core Dependencies
```{LANGUAGE}
{DEPENDENCY_1}             # {DESCRIPTION_1}
{DEPENDENCY_2}             # {DESCRIPTION_2}
{DEPENDENCY_3}             # {DESCRIPTION_3}
```

### Architecture
```{ARCHITECTURE_DIAGRAM}
```

## Custom Templates

Users can place custom templates in the `~/.clawboss/templates/` directory to override default templates. ClawBoss will prioritize user custom templates.
