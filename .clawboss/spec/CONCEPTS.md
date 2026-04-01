# AI-Me Core Concepts

## Behavior

Behavior is the core unit of the system, representing something a user needs to accomplish. A behavior has the following properties:

### Properties

- **ID**: Unique identifier (e.g., `beh_abc123`)
- **Name**: Short description of the behavior
- **Description**: Detailed explanation of the behavior's content and goals
- **Status**: Current lifecycle stage
- **Parent Behavior**: Upper-level behavior (if this is a sub-behavior)
- **Child Behaviors**: List of lower-level behaviors
- **Workspace Path**: Associated folder path
- **Behavior Class**: Associated behavior class ID (see below)
- **Priority**: Priority level (high/medium/low)
- **Tags**: List of tags for categorization
- **Metadata**: JSON object for extensible custom data

#### Time Management

- **Start Time**: When the behavior actually started (set automatically when status changes to `doing`)
- **End Time**: When the behavior actually ended (set automatically when status changes to `done`)
- **Actual Duration**: Total time spent on the behavior (in minutes), calculated from start and end times
- **Planned Duration**: Estimated time required to complete the behavior (in minutes), set by user during creation or planning
- **Deadline**: Target completion date/time
- **Due Date**: Alias for deadline, interchangeable

#### Time Aggregation (Parent-Child)

Time is aggregated hierarchically from leaf behaviors up to root behaviors:

```
Learn Rust Programming [Total: 450 min]
├── Self Actual: 60 min            ← time spent directly on this behavior
├── Self Planned: 90 min
│
└── Child Behaviors Total: 390 min ← sum of all children's Total Actual
    ├── Basic Syntax [Total: 150 min = 30 + 120]
    │   ├── Self Actual: 30 min
    │   ├── Self Planned: 45 min
    │   └── Child Behaviors Total: 120 min
    │       ├── Variables [Total: 60 min = 60 + 0]
    │       │   ├── Self Actual: 60 min
    │       │   └── Self Planned: 60 min
    │       └── Control Flow [Total: 60 min = 45 + 15]
    │           ├── Self Actual: 45 min
    │           ├── Self Planned: 45 min
    │           └── Child Behaviors Total: 15 min
    │               └── Sub-topic [Total: 15 min]
    │                   └── Self Actual: 15 min
    │
    └── Project Practice [Total: 240 min = 30 + 210]
        ├── Self Actual: 30 min
        ├── Self Planned: 60 min
        └── Child Behaviors Total: 210 min
            ├── CLI Tool [Total: 120 min = 90 + 30]
            │   ├── Self Actual: 90 min
            │   ├── Self Planned: 100 min
            │   └── Child Behaviors Total: 30 min
            │       └── Implementation [Total: 30 min]
            │           └── Self Actual: 30 min
            └── Web Service [Total: 90 min = 75 + 15]
                ├── Self Actual: 75 min
                ├── Self Planned: 80 min
                └── Child Behaviors Total: 15 min
                    └── Testing [Total: 15 min]
                        └── Self Actual: 15 min
```

**Time Aggregation Rules**:

1. **Total Actual Duration** = Self Actual Duration + Sum of All Children's **Total** Actual Duration
2. **Total Planned Duration** = Self Planned Duration + Sum of All Children's **Total** Planned Duration
3. **Time Efficiency** = Total Actual / Total Planned × 100%

**Calculation Example**:
- Sub-topic: Total Actual = 15 (self) + 0 (no children) = 15 min
- Variables: Total Actual = 60 (self) + 0 (no children) = 60 min
- Control Flow: Total Actual = 45 (self) + 15 (Sub-topic) = 60 min
- Basic Syntax: Total Actual = 30 (self) + 60 (Variables) + 60 (Control Flow) = 150 min
- Implementation: Total Actual = 30 (self) + 0 = 30 min
- CLI Tool: Total Actual = 90 (self) + 30 (Implementation) = 120 min
- Web Service: Total Actual = 75 (self) + 15 (Testing) = 90 min
- Project Practice: Total Actual = 30 (self) + 120 (CLI Tool) + 90 (Web Service) = 240 min
- Learn Rust Programming: Total Actual = 60 (self) + 150 (Basic Syntax) + 240 (Project Practice) = 450 min

**CLI Examples**:
```bash
# View time report with aggregation
ai-me show <id> --time-report

# Output shows:
# ├─ Self Time: 60 min (actual) / 90 min (planned) = 67%
# ├─ Children Time: 420 min (actual) / 360 min (planned) = 117%
# └─ Total Time: 480 min (actual) / 450 min (planned) = 107%

# List behaviors with time stats
ai-me list --with-time

# Filter by time efficiency
ai-me list --efficiency-over 100    # Over budget
ai-me list --efficiency-under 80    # Under budget (efficient!)
```

#### Dependencies

- **Dependencies**: List of other behavior IDs that must be completed before this behavior can start
  - A behavior cannot transition to `doing` if any dependency is not `done`
  - Circular dependencies are prevented by the system
  - Visualized in tree view with dependency lines

#### Acceptance Criteria

- **Acceptance Criteria**: Conditions that must be met for the behavior to be considered complete
  - Can be a checklist of items
  - Can reference external deliverables (files, documents, etc.)
  - Can reference metrics (test coverage, performance benchmarks, etc.)
  - All criteria must be checked before marking behavior as `done`

#### Metadata

- **Creation Time**: When the behavior was created
- **Update Time**: When the behavior was last modified
- **Progress**: Completion percentage (0-100), auto-calculated from sub-behaviors


### Status Flow

```
                    todo
                   /    \
              doing      paused
             /    \       /
           done  blocked--
            |       |
            +-------+-----> todo (reopen)
```

- **todo**: Created but not started
- **doing**: Currently in progress
- **done**: Completed
- **paused**: Deliberately paused
- **blocked**: Blocked by external factors or dependencies

**Status Transition Rules**:

| From | To | Condition |
|------|-----|-----------|
| `todo` | `doing` | User starts working on the behavior |
| `doing` | `done` | All acceptance criteria met |
| `doing` | `paused` | User deliberately pauses |
| `doing` | `blocked` | External blocker or unmet dependency |
| `paused` | `doing` | User resumes work |
| `paused` | `todo` | User decides not to continue now |
| `blocked` | `doing` | Blocker resolved, dependencies completed |
| `blocked` | `todo` | Blocked indefinitely, back to backlog |
| `done` | `doing` | Re-opened for additional work |
| `done` | `todo` | Re-opened to backlog status |

### Automatic Time Tracking

The system automatically tracks time based on status transitions:

| Transition | Action |
|------------|--------|
| `todo` → `doing` | **Start Time** is set to current time |
| `doing` → `done` | **End Time** is set to current time, **Actual Duration** is calculated |
| `doing` → `paused` | Duration is accumulated but not finalized |
| `paused` → `doing` | Timer resumes (accumulates from previous sessions) |

**Actual Duration Calculation**: Sum of all `doing` periods until `done`.

### Dependencies

Behaviors can depend on other behaviors:

```
Write Blog Post [todo]
├── Research Topic [done]     ← dependency
├── Create Outline [done]     ← dependency
└── Write Draft [todo]
    └── Review Draft [todo]   ← depends on Write Draft
```

**Rules**:
- A behavior cannot start (`doing`) until all dependencies are `done`
- Attempting to start will show a warning with the blocking dependencies
- Circular dependencies are prevented (A depends on B, B depends on A)
- Dependencies can cross parent-child boundaries

**CLI Examples**:
```bash
# Add dependency
ai-me update <behavior-id> --depends-on <other-behavior-id>

# Remove dependency
ai-me update <behavior-id> --remove-depends-on <other-behavior-id>

# View dependency chain
ai-me tree <behavior-id> --with-deps
```

### Acceptance Criteria

Acceptance criteria define what "done" means:

```markdown
## Acceptance Criteria for "Write Blog Post"

- [ ] Article is at least 1500 words
- [ ] Contains code examples
- [ ] Proofread by at least 1 person
- [ ] Published to blog platform
- [ ] Social media post drafted
```

**Types of Criteria**:
1. **Checklist**: Simple yes/no items
2. **File-based**: Workspace must contain specific files
3. **Metric-based**: Performance thresholds, test coverage, etc.
4. **External**: Links to external deliverables (PRs, deployed apps, etc.)

**Completion Check**:
- Before marking as `done`, system prompts to review acceptance criteria
- Can force complete with `--force` flag
- Incomplete criteria are tracked in metadata

## BehaviorClass

BehaviorClass is the **type definition** of a behavior, similar to the "class vs instance" relationship in object-oriented programming. BehaviorClass provides execution guidance and knowledge accumulation for behavior instances.

### Core Concept

```
Behavior Class Tree (Template Layer)    Behavior Instance Tree (Execution Layer)

Learning                                Learning Rust Programming [doing]
├── Reading                             ├── Basic Syntax Learning [done]
├── Practicing                          │   ├── Variables and Data Types [done]
└── Writing                             │   └── Control Flow [doing]
                                        └── Project Practice [todo]
                                            ├── CLI Tool Development
                                            └── Web Service Development
```

### BehaviorClass Properties

- **ID**: Unique identifier (e.g., `learning`)
- **Name**: Short name (e.g., "Learning")
- **Description**: Function description of the class
- **Parent Class**: Upper-level behavior class (supports inheritance)
- **Icon/Color**: Visual identifier
- **Author**: Creator of the class
- **Version**: Class version

### BehaviorClass Documentation

Each behavior class has a Markdown document. At runtime, documents are located at `~/ai-me/classes/{class-id}.md` after merging from the source directory tree.

**Source vs Runtime Locations**:
- **Source files** (in `behavior-classes/` directory tree): `_doc.{locale}.md` files
- **Runtime merged docs** (in `~/ai-me/classes/`): `{class-id}.{locale}.md` files generated by the system

```markdown
# Learning

## Rules

Guidelines to follow when executing learning behaviors:

- Define clear learning objectives before each session
- Learning sessions should not exceed 90 minutes, must take breaks
- Must write summary notes after completing learning
- Regularly review learned content

## Experiences

Accumulated experiences and insights about learning:

- Pomodoro Technique is very effective for deep learning
- Morning is the golden time for memory
- Teaching others is the best way to learn
- 2024-03: Found that combining practice is 3x more efficient than pure reading

## Methods

Specific methods/steps for executing learning behaviors:

### Feynman Technique

1. Choose a concept
2. Explain it in simple language to a beginner
3. Identify where you get stuck, go back and study
4. Simplify language, use analogies

### Deliberate Practice

1. Identify specific weak areas
2. Design targeted exercises
3. Get immediate feedback
4. Repeat until proficient

## Recommended Subclasses

- Reading
- Practicing
- Writing
```

### Behavior Class Directory Tree (Class Tree Directory)

Behavior classes are stored in a **directory tree + YAML files** format, facilitating version control, sharing, and collaboration.

#### Directory Structure

```
behavior-classes/                    # Behavior class directory tree root
├── _index.yaml                      # Root index file
├── learning/                        # Parent class directory
│   ├── _class.yaml                  # Class definition file
│   ├── _doc.en.md                   # Class documentation (English)
│   ├── _doc.zh.md                   # Class documentation (Chinese)
│   ├── reading/                     # Subclass directory
│   │   ├── _class.yaml
│   │   ├── _doc.en.md
│   │   └── _doc.zh.md
│   ├── practicing/
│   │   ├── _class.yaml
│   │   ├── _doc.en.md
│   │   └── _doc.zh.md
│   └── writing/
│       ├── _class.yaml
│       ├── _doc.en.md
│       └── _doc.zh.md
├── work/
│   ├── _class.yaml
│   ├── _doc.en.md
│   ├── _doc.zh.md
│   ├── programming/
│   │   ├── _class.yaml
│   │   ├── _doc.en.md
│   │   └── _doc.zh.md
│   │   ├── web-development/
│   │   │   ├── _class.yaml
│   │   │   ├── _doc.en.md
│   │   │   └── _doc.zh.md
│   │   └── cli-tools/
│   │       ├── _class.yaml
│   │       ├── _doc.en.md
│   │       └── _doc.zh.md
│   └── writing/
│       ├── _class.yaml
│       ├── _doc.en.md
│       └── _doc.zh.md
└── life/
    ├── _class.yaml
    ├── _doc.en.md
    └── _doc.zh.md
```

#### YAML File Format

**_class.yaml** - Class Definition with i18n support:

```yaml
id: learning                    # Unique identifier (required)
name:                           # Multi-language display names
  en: Learning                  # English
  zh: 学习                       # Chinese
description:                    # Multi-language descriptions
  en: The process of acquiring new knowledge and skills
  zh: 获取新知识和技能的过程
icon: 📚                        # Emoji icon
color: "#4f46e5"               # Theme color
author: ai-me-team             # Author
version: "1.0.0"               # Version
created_at: "2024-03-29"       # Creation date
updated_at: "2024-03-29"       # Update date
tags: ["general", "growth"]      # Tags (English as standard)
locales: ["en", "zh"]            # Supported locales
```

**_index.yaml** - Root Index (optional):

```yaml
name:
  en: AI-Me System Behavior Class Tree
  zh: AI-Me 系统行为类树
description:
  en: Officially maintained behavior class collection
  zh: 官方维护的行为类集合
version: "1.0.0"
author: ai-me-team
repository: https://github.com/ai-me/behavior-classes
locales: ["en", "zh"]
default_locale: "en"
```

#### Multi-Language Support

##### Language Selection

Users can set their preferred language:

```bash
# Set language
ai-me config set language zh

# View current language
ai-me config get language

# List supported languages
ai-me config languages
```

Or via environment variable:
```bash
export AI_ME_LANG=zh
```

Supported languages (ISO 639-1 codes):
- `en` - English (default)
- `zh` - Chinese (中文)

More languages can be added in the future by extending the `locales` array in `_class.yaml` files.

##### Document File Naming Convention

- `_doc.md` or `_doc.en.md` - Default/English version
- `_doc.zh.md` - Chinese version
- `_doc.ja.md` - Japanese version
- `_doc.{locale}.md` - Any locale

If a language-specific document doesn't exist, the system falls back to:
1. The user's preferred language version
2. The default language version (English)
3. Any available language version

##### Runtime Document Loading

```typescript
// Example: User language is 'zh', loading 'learning' class
const userLang = 'zh';
const classId = 'learning';

// System looks for runtime merged documents in order:
// 1. ~/ai-me/classes/learning.zh.md (Chinese, merged at runtime)
// 2. ~/ai-me/classes/learning.en.md (English fallback)
// 3. ~/ai-me/classes/learning.md (Default)

// Source files (before merge) in behavior-classes/ directory:
// - behavior-classes/learning/_doc.zh.md (Chinese source)
// - behavior-classes/learning/_doc.en.md (English source)
```

**Naming Convention Summary**:
| Location | Source File | Runtime File |
|----------|-------------|--------------|
| Default | `_doc.md` | `{class-id}.md` |
| English | `_doc.en.md` | `{class-id}.en.md` |
| Chinese | `_doc.zh.md` | `{class-id}.zh.md` |
| Japanese | `_doc.ja.md` | `{class-id}.ja.md` |
| Any locale | `_doc.{locale}.md` | `{class-id}.{locale}.md` |

##### Merging Multi-Language Documents

When importing from directory tree, the system:

1. **Validates locale support**: Check if `_class.yaml` declares the locale
2. **Creates merged docs**: For each supported locale, create a merged document
3. **Falls back gracefully**: If a subclass lacks a translation, use parent class translation

Example merged document structure:
```
~/ai-me/classes/
├── learning.en.md          # Merged English doc
├── learning.zh.md          # Merged Chinese doc
├── learning.ja.md          # Merged Japanese doc
├── reading.en.md
├── reading.zh.md
└── ...
```

##### Contributing Translations

Community can contribute translations via pull requests:

```
behavior-classes/
├── learning/
│   ├── _class.yaml          # Add locale to 'locales' array
│   ├── _doc.en.md           # Existing
│   ├── _doc.zh.md           # Existing
│   └── _doc.ja.md           # New Japanese translation
```

Translation contribution workflow:
1. Fork the repository
2. Add translation files following naming convention
3. Update `_class.yaml` with new locale
4. Submit pull request

#### Inheritance Mechanism

The directory structure represents inheritance relationships:
- Parent directory = Parent class
- Subdirectory = Child class
- Same-level directories = Sibling classes

In the above structure:
- `learning` is the root class
- `learning/reading`, `learning/practicing`, `learning/writing` all inherit from `learning`
- `work/programming/web-development` inherits from `programming`, which inherits from `work`

#### Import and Export

**System Import** (during installation):
```bash
# Clone from official repository and import
ai-me class import --official

# Import from local directory
ai-me class import ./behavior-classes/

# Import from GitHub
ai-me class import https://github.com/user/behavior-classes
```

**User Export** (for sharing):
```bash
# Export all custom classes as directory tree
ai-me class export ./my-classes/

# Export with system classes (full backup)
ai-me class export --include-system ./backup/

# Package as shareable file
ai-me class export --package ./my-classes.zip
```

#### Class Documentation Merging

The system automatically merges documents along the inheritance chain:

```
Feynman Technique (learning/reading) =
  learning._doc.md rules + experiences + methods
  + reading._doc.md rules + experiences + methods
```

Merging rules:
1. **Rules**: Parent class rules first, then child class rules (can override)
2. **Experiences**: Merged in chronological order
3. **Methods**: Child class methods take precedence, same-name methods override

#### Version Updates

When system behavior classes are updated:

```bash
# Check for updates
ai-me class update --check

# Update system classes (preserve user custom content)
ai-me class update --official

# View changelog
ai-me class changelog
```

#### Custom Extensions

Users can create private class trees locally:

```
~/ai-me/my-classes/
├── _index.yaml
├── my-learning-methods/
│   ├── _class.yaml
│   ├── _doc.md
│   └── morning-reading/
│       ├── _class.yaml
│       └── _doc.md
```

Import private class tree:
```bash
ai-me class import ~/ai-me/my-classes/
```

### Inheritance Mechanism

Behavior classes support single inheritance, where child classes automatically inherit rules, experiences, and methods from parent classes:

```
Learning
└── Coding
    └── RustLearning
        └── AsyncRustLearning
```

- **AsyncRustLearning** inherits: Rules + Experiences + Methods merged from the chain
- Child classes can **override** parent class content
- Child classes can **extend** with new content

### Use Cases

1. **Standardized Processes**: Define standard checklists for "Code Review" class
2. **Knowledge Accumulation**: Accumulate headline writing tips in the "Writing" class
3. **Smart Suggestions**: AI suggests to users based on behavior class rules and experiences
4. **Template Reuse**: Automatically apply class templates when creating same-type behaviors

### Relationship with Behavior Instances

| Dimension | BehaviorClass | Behavior |
|-----------|---------------|----------|
| Level | Template layer ("Learning") | Execution layer ("Learning Rust") |
| Quantity | Reusable, limited number | Created for each execution |
| Lifecycle | Long-term, continuous accumulation | Archived after completion |
| Modification Frequency | Low (accumulating knowledge) | High (status changes) |
| Storage | Markdown documents | SQLite database |
| Purpose | Guidance and knowledge | Tracking and execution |

## Behavior Tree

Behaviors form a tree structure through parent-child relationships:

```
Learning Rust Programming (root behavior)
├── Basic Syntax Learning
│   ├── Variables and Data Types
│   ├── Control Flow
│   └── Functions and Modules
├── Project Practice
│   ├── CLI Tool Development
│   └── Web Service Development
└── Advanced Topics
    ├── Concurrency
    └── Unsafe Code
```

### Rules

1. Each behavior can have 0 or more child behaviors
2. Each behavior can have at most 1 parent behavior (except root)
3. Tree structure supports unlimited levels (but recommend ≤ 5 for usability)

## Workspace

Each behavior corresponds to an independent folder called a workspace.

### Features

- **Auto-creation**: Folder automatically created at `~/ai-me/workspaces/{behavior-id}/` when behavior is created
- **Free organization**: Users can freely store files in the workspace
- **Cascading structure**: Child behavior workspaces can be nested within parent or independent
- **Quick access**: Quickly open workspace via CLI or AI commands

### Usage Example

```
~/ai-me/workspaces/
├── beh_abc123/           # "Learning Rust Programming"
│   ├── notes.md
│   ├── resources/
│   └── beh_def456/       # "Basic Syntax Learning" (nested workspace)
│       └── exercises/
└── beh_xyz789/           # "Writing Blog Post"
    ├── draft.md
    └── images/
```

## AI Agent Integration

The system interacts with Claude Code and other AI agents through a natural language interface.

### Interaction Modes

1. **Command Mode**: `ai-me create "Learning Rust Programming" --parent "Skill Development"`
2. **Dialogue Mode**: User describes needs in natural language, AI parses and executes
   - "Help me create a Rust learning behavior with foundation and practice phases"
   - "Mark 'Basic Syntax Learning' as doing"
   - "Open the workspace for my current active behavior"

### Natural Language Parsing

The system supports intelligent natural language understanding with the following capabilities:

#### Fuzzy Intent Matching

Multiple phrases can trigger the same action:

| Intent | Trigger Phrases |
|--------|-----------------|
| Create Behavior | "create", "new", "add", "start", "begin", "initiate" |
| Start Doing | "start", "begin", "work on", "switch to", "focus on", "continue" |
| Mark Done | "done", "complete", "finish", "mark as done", "wrap up" |
| Pause | "pause", "stop", "hold", "suspend", "take a break" |
| List Behaviors | "list", "show", "display", "what am I working on" |
| Open Workspace | "open", "switch to", "go to", "navigate to", "cd to" |
| Update Status | "update", "change", "set", "mark as" |
| Delete | "delete", "remove", "cancel", "drop" |

#### Context Memory

The system maintains context across the conversation:

```
User: "Create a new behavior called 'Learn Rust'"
AI: "Created behavior 'Learn Rust' (beh_rust_001)."

User: "Add some sub-behaviors for it"  # "it" refers to beh_rust_001
AI: "What sub-behaviors would you like to add to 'Learn Rust'?"

User: "Basics, advanced topics, and a project"  # Implicit parent = beh_rust_001
AI: "Created 3 sub-behaviors under 'Learn Rust': Basics (beh_...), ..."

User: "Start working on the basics"  # Resolves to the recently created "Basics"
AI: "Updated 'Basics' status to 'doing'. Workspace opened."
```

**Context Memory Rules**:
- Recently created/modified behaviors are prioritized in reference resolution
- Active (`doing`) behaviors are always in context
- Child behaviors inherit parent context
- Context expires after 10 minutes of inactivity

#### Multi-Turn Dialogue Support

The system supports multi-turn conversations for complex operations:

**Example: Creating a Behavior with Details**
```
User: "I want to create a new behavior"
AI: "What's the name of the behavior?"
User: "Write a blog post about Rust"
AI: "Got it. Would you like to set a deadline or planned duration?"
User: "Due by next Friday, about 4 hours of work"
AI: "Deadline set to 2026-04-04, planned duration 4 hours. Any parent behavior?"
User: "Put it under Content Creation"
AI: "Created 'Write a blog post about Rust' under 'Content Creation'."
```

**Example: Clarifying Ambiguous Requests**
```
User: "Mark it as done"
AI: "You have 3 active behaviors: 'Learning Rust', 'Code Review', 'Email Client'. Which one?"
User: "The code review one"
AI: "Marked 'Code Review' as done. Great job!"
```

#### Entity Extraction

The system extracts structured data from natural language:

| Entity Type | Examples | Extraction |
|-------------|----------|------------|
| Behavior Name | "Learn Rust Programming" | `name: "Learn Rust Programming"` |
| Status | "start working", "mark done" | `status: doing/done/paused/blocked` |
| Time Duration | "about 2 hours", "30 minutes" | `planned_duration: 120` (minutes) |
| Deadline | "by Friday", "due tomorrow", "before March 31" | `deadline: 2026-03-29` |
| Priority | "high priority", "urgent", "low priority" | `priority: high/medium/low` |
| Parent Reference | "under Project X", "part of Y" | `parent_id: beh_...` |
| Tags | "tagged as learning", "category: work" | `tags: ["learning"]` |

#### Fallback Behavior

When intent is unclear, the AI will:
1. Ask clarifying questions
2. Suggest similar commands
3. Show examples of valid requests

```
User: "Do the thing"
AI: "I'm not sure what you'd like to do. Did you mean:
   - Start working on an existing behavior?
   - Create a new behavior?
   - Mark something as complete?

   Try saying something like:
   - 'Start working on Learning Rust'
   - 'Create a new behavior called Write Blog Post'
   - 'Mark Code Review as done'"
```

### AI Capabilities

- Parse user natural language intent with fuzzy matching
- Maintain conversation context for multi-turn dialogues
- Extract structured data (time, status, priority) from text
- Auto-suggest behavior decomposition schemes
- Execute related operations based on context
- Generate behavior progress reports

### AI Suggestion Commands

```bash
# Get AI-suggested sub-behaviors for a behavior
ai-me suggest-decomposition <behavior-id>
# Output: List of recommended sub-behaviors with descriptions and estimated times
# Based on: behavior class rules, historical data, similar behaviors

# Get AI-suggested behavior class for a description
ai-me suggest-class "<description>"
# Output: Recommended class(es) with confidence scores
# Example: "learning/programming/rust" (confidence: 92%)

# Get AI-suggested time estimate for a behavior
ai-me suggest-time <behavior-id>
# Output: Recommended planned duration based on:
#   - Similar past behaviors
#   - Behavior class benchmarks
#   - User's historical estimation accuracy
# Example: "Recommended: 180 minutes (based on 5 similar tasks, avg: 165 min)"

# Batch suggest decompositions for multiple behaviors
ai-me suggest-decomposition --all-todo
# Generates suggestions for all todo behaviors

# Compare actual vs suggested time
ai-me suggest-time <id> --compare
# Shows: Planned | AI Suggested | Actual (if completed) | Variance
```

#### Suggestion Feedback Loop

Users can provide feedback on AI suggestions to improve future recommendations:

```bash
# Rate a suggestion
ai-me suggest-feedback <suggestion-id> --rating good
ai-me suggest-feedback <suggestion-id> --rating poor --reason "overestimated by 2x"

# View suggestion accuracy statistics
ai-me suggest-stats
# Shows: acceptance rate, average variance, improvement over time
```

## Installation and Initialization

### Installation Script

```bash
# One-line installation
curl -sSL https://install.ai-me.dev | bash

# Or use package manager
npm install -g ai-me
brew install ai-me
```

### Initialization Process

1. Create `~/ai-me/` directory in user's home
2. Initialize SQLite database
3. Create configuration files
4. Create workspace root directory
5. Import system behavior classes from directory tree
6. Prompt user to start Claude Code in `~/ai-me` directory

## Claude Code Integration

### Context Injection

Write in `~/ai-me/.claude/CLAUDE.md`:

```markdown
# AI-Me Behavior Management System

## Current Behavior Context

{{CURRENT_BEHAVIOR}}

## Active Behaviors

{{ACTIVE_BEHAVIORS}}

## Blocked Behaviors

{{BLOCKED_BEHAVIORS}}

## Time Summary

{{TIME_SUMMARY}}

## Upcoming Deadlines

{{UPCOMING_DEADLINES}}

## Recent Completed

{{RECENT_COMPLETED}}

## System Recommendations

{{SYSTEM_RECOMMENDATIONS}}

## Available Commands

You can help users manage behaviors by calling CLI:
- `ai-me create "..."` - Create behavior
- `ai-me list` - List behaviors
- `ai-me update <id> --status doing` - Update status
- `ai-me cd <id>` - Switch workspace
- `ai-me context` - Show current context
- `ai-me suggest-decomposition <id>` - AI-suggested sub-behaviors
- `ai-me suggest-time <id>` - AI-suggested time estimate

## Workflow Suggestions

1. When user says "start working on something", help create or activate the behavior
2. When user completes part of work, help update progress or mark sub-behavior as done
3. When user needs to see progress, use tree command to show overall situation
```

### Context Template Variables

The following template variables are automatically substituted when generating Claude Code context:

| Variable | Content | Format |
|----------|---------|--------|
| `{{CURRENT_BEHAVIOR}}` | Behavior associated with the current working directory | Full behavior details including name, status, time stats, and workspace path |
| `{{ACTIVE_BEHAVIORS}}` | All behaviors with `doing` status | List of active behaviors with ID, name, elapsed time, and workspace |
| `{{BLOCKED_BEHAVIORS}}` | Behaviors with `blocked` status | List of blocked behaviors with blocker reason and blocking dependencies |
| `{{TIME_SUMMARY}}` | Time statistics summary | Today's/This week's/This month's time allocation across behaviors |
| `{{UPCOMING_DEADLINES}}` | Behaviors with approaching deadlines | List of behaviors with deadlines within 7 days, sorted by urgency |
| `{{RECENT_COMPLETED}}` | Recently completed behaviors | Last 3-5 behaviors marked as `done`, with completion time and duration |
| `{{SYSTEM_RECOMMENDATIONS}}` | AI-generated suggestions | Based on current context: next actions, time allocation suggestions, risk warnings |

#### Example Template Output

**{{CURRENT_BEHAVIOR}}**:
```
Behavior: Learning Rust Programming (beh_rust_001)
Status: doing (started 2 hours ago)
Progress: 35% (3 of 8 sub-behaviors completed)
Time: 120 min actual / 180 min planned (67% efficiency)
Workspace: ~/ai-me/workspaces/beh_rust_001/
Parent: Skill Development
Class: learning/programming
```

**{{ACTIVE_BEHAVIORS}}**:
```
1. Learning Rust Programming (beh_rust_001) - doing for 2h 15m
2. Write Weekly Report (beh_wr_042) - doing for 30m
3. Fix Bug #1234 (beh_bug_1234) - doing for 15m (paused, waiting for review)
```

**{{BLOCKED_BEHAVIORS}}**:
```
1. Deploy to Production (beh_dep_001)
   Blocked by: beh_test_001 (integration tests not passing)
   Reason: CI pipeline failed, waiting for fix

2. Refactor Database Schema (beh_db_002)
   Blocked by: beh_rust_001 (need to complete Rust learning first)
   Reason: Prerequisite skill not yet acquired
```

**{{TIME_SUMMARY}}** (2026-03-29):
```
Today:
- Total tracked: 4h 30m
- Top behavior: Learning Rust (2h 15m)
- Efficiency: 85% (under budget)

This Week:
- Total tracked: 28h 15m
- Average daily: 4h 2m
- Most active class: programming (12h)

This Month:
- Total tracked: 112h 30m
- Completion rate: 78%
- Trend: +15% vs last month
```

**{{UPCOMING_DEADLINES}}**:
```
Due in 2 days (2026-03-31):
- Submit Project Proposal (beh_prop_001) [high priority]

Due in 5 days (2026-04-03):
- Complete Code Review (beh_cr_007)
- Update Documentation (beh_doc_012)

Due in 7 days (2026-04-05):
- Release v2.0 (beh_rel_020)
```

**{{RECENT_COMPLETED}}**:
```
1. Setup Development Environment (beh_setup_001)
   Completed: 30 minutes ago
   Duration: 45 minutes (planned: 60 min) - 25% under budget

2. Research API Options (beh_api_003)
   Completed: 2 hours ago
   Duration: 90 minutes (planned: 60 min) - 50% over budget

3. Design Database Schema (beh_db_001)
   Completed: yesterday
   Duration: 3 hours (planned: 2.5 hours) - 20% over budget
```

**{{SYSTEM_RECOMMENDATIONS}}**:
```
Based on your current context:

1. Time Management: You have been working on "Learning Rust Programming" for 2+ hours. Consider taking a break or switching to a different task to maintain focus.

2. Priority Alert: "Submit Project Proposal" is due in 2 days and has not been started yet. Recommend switching focus.

3. Dependency Warning: "Deploy to Production" is blocked by failing tests. Consider debugging the test failures or reassigning the task.

4. Pattern Recognition: You tend to underestimate programming tasks by ~30%. Consider adding more buffer time to similar estimates.
```

### Context Management Commands

```bash
# Display current context information
ai-me context
# Shows: current behavior, active behaviors, time summary, upcoming deadlines

# Manually refresh Claude Code context file
ai-me context --refresh
# Regenerates ~/ai-me/.claude/CLAUDE.md with latest data

# Export context for debugging
ai-me context --export [format]
# Formats: json (default), yaml, markdown
# Saves to: ~/ai-me/exports/context-{timestamp}.{format}

# Show context diff since last refresh
ai-me context --diff
# Displays what has changed since the last context update

# Preview context without writing to file
ai-me context --preview
# Outputs the generated context to stdout for inspection
```

## Shell Integration

### Installation

Generate shell configuration for your shell:

```bash
# Bash
ai-me shell-init >> ~/.bashrc

# Zsh
ai-me shell-init >> ~/.zshrc

# PowerShell
ai-me shell-init | Out-File -Append $PROFILE

# Fish
ai-me shell-init --fish >> ~/.config/fish/config.fish
```

### Features

#### 1. Smart cd Command

The `ai-me cd <id>` command integrates with the shell to actually change directories:

```bash
# Changes to the behavior's workspace directory
ai-me cd beh_abc123

# Special shortcuts
ai-me cd -        # Go to previous behavior
ai-me cd ..       # Go to parent behavior
ai-me cd ~        # Go to root workspace
```

**Implementation Notes**:
- The `cd` command requires shell function wrapper to change the current directory
- Uses directory hooks to detect when user manually navigates into a workspace
- Auto-detects current behavior based on working directory

#### 2. Prompt Integration

Display current active behavior in shell prompt:

```bash
# Example prompts:
(Learning Rust) user@host:~$           # Bash/Zsh
[Learning Rust] PS C:\Users\name>       # PowerShell

# Configuration:
ai-me config set prompt.enabled true
ai-me config set prompt.format "({behavior})"
```

**Cross-Platform Support**:
- **Bash/Zsh**: `PS1` modification via `PROMPT_COMMAND`
- **PowerShell**: Custom `prompt` function
- **Fish**: `fish_prompt` function

#### 3. Keyboard Shortcuts

Quick access to behavior workspaces:

| Shortcut | Action |
|----------|--------|
| `Ctrl+G` | Open current behavior workspace in file manager/explorer |
| `Ctrl+Shift+G` | Display behavior selector (fuzzy finder) |
| `Ctrl+Alt+G` | Quick switch to recent behavior |

**Implementation**:
- Uses `bind` (Bash), `bindkey` (Zsh), `Set-PSReadlineKeyHandler` (PowerShell)
- Fuzzy finder integration with `fzf` (optional, cross-platform)

#### 4. Alias Auto-Loading

Automatic command aliases loaded at shell startup:

```bash
# Generated aliases:
alias am='ai-me'
alias amc='ai-me create'
alias aml='ai-me list'
alias ams='ai-me show'
alias amu='ai-me update'
alias amcd='ai-me cd'
alias amw='ai-me workspace'
alias amb='ai-me --simple'    # Simple mode alias
```

### Workspace Enhancements

Additional workspace commands for improved UX:

```bash
# Preview workspace contents without switching
ai-me workspace --preview <id>
# Output: Lists files, recent activity, and metadata

# List recently accessed workspaces
ai-me workspace --recent
# Output: Top 10 recently accessed workspaces with timestamps

# Archive inactive workspaces
ai-me workspace --archive <id>
# Actions:
# - Compress workspace to ~/ai-me/archives/{id}-{date}.zip
# - Keep database record but mark as archived
# - Free up space while preserving history

# Restore archived workspace
ai-me workspace --restore <archive-path>
```

### Simple Mode

Reduced command set for new users or quick operations:

```bash
# Enable simple mode for current command
ai-me --simple list

# Set default mode to simple
ai-me config set mode simple

# Simple mode commands (core only):
# - create: Create new behavior
# - list: List behaviors
# - show: Show behavior details
# - done: Mark behavior as complete
# - start: Start working on behavior

# Switch back to full mode
ai-me config set mode full
```

### Onboarding Experience

Guided setup for first-time users:

```bash
# Welcome wizard (runs automatically on first install)
ai-me welcome
# Steps:
# 1. Verify installation
# 2. Configure user preferences (language, editor, etc.)
# 3. Create first behavior example
# 4. Explain basic workflow

# Interactive tutorial
ai-me tutorial
# Covers:
# - Creating behaviors
# - Managing status
# - Using workspaces
# - Setting up shell integration

# Example gallery
ai-me examples
# Shows:
# - Personal learning tracking
# - Project management
# - Daily task organization
# - Research workflow
```

### Workspace Templates

Auto-initialize workspaces based on behavior class:

```bash
# Template configuration in behavior class
templates:
  programming:
    folders:
      - src/
      - tests/
      - docs/
      - .github/
    files:
      - README.md
      - .gitignore
      - LICENSE
  writing:
    folders:
      - drafts/
      - research/
      - assets/
    files:
      - outline.md
      - notes.md
```

**Template Variables**:
- `{behavior_name}` - Behavior name
- `{behavior_id}` - Behavior ID
- `{date}` - Current date
- `{author}` - User name from config

### Productivity Dashboard

Analytics and reporting for behavior tracking:

```bash
# Launch dashboard
ai-me dashboard
```

**Dashboard Sections**:

1. **Daily/Weekly/Monthly Stats**:
   ```
   Today:
   - Behaviors completed: 5
   - Time spent: 4h 30m
   - Efficiency: 95%
   ```

2. **Completion Trends**:
   - Line chart: Completed behaviors over time
   - Bar chart: Time distribution by behavior class

3. **Time Efficiency Analysis**:
   - Planned vs Actual duration comparison
   - Most accurate estimation behavior classes
   - Average completion time by category

4. **AI-Generated Reports**:
   ```bash
   # Weekly summary
   ai-me report --weekly

   # Monthly summary with insights
   ai-me report --monthly --insights

   # Export as Markdown
   ai-me report --weekly --export weekly-report.md
   ```

**Report Content**:
- Summary of completed behaviors
- Time allocation analysis
- Productivity trends
- Suggestions for improvement based on patterns

### Configuration

Shell integration settings:

```bash
# View all shell settings
ai-me config shell

# Enable/disable features
ai-me config set shell.prompt true
ai-me config set shell.shortcuts true
ai-me config set shell.aliases true
ai-me config set shell.autocd true  # Auto-switch when entering workspace

# Dashboard settings
ai-me config set dashboard.auto_launch false
ai-me config set dashboard.report_schedule weekly
```

## Command Line Interface (CLI)

### Core Commands

```bash
# Behavior management
ai-me create <name> [--parent <id>] [--description <desc>]
ai-me list [--status <status>] [--tree]
ai-me show <id>
ai-me update <id> [--name <name>] [--status <status>]
ai-me delete <id>

# Workspace
ai-me workspace <id> [--open]
ai-me cd <id>

# Tree navigation
ai-me tree [id]
ai-me root
ai-me up
ai-me down <id>

# Context management
ai-me context [--refresh] [--export <format>] [--diff] [--preview]

# AI suggestions
ai-me suggest-decomposition <behavior-id> [--all-todo]
ai-me suggest-class "<description>"
ai-me suggest-time <behavior-id> [--compare]

# AI interaction
ai-me ask "<natural language query>"
```

## Data Persistence

### SQLite Database Structure

```sql
-- behaviors table
CREATE TABLE behaviors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'todo',
    parent_id TEXT REFERENCES behaviors(id),
    class_id TEXT REFERENCES behavior_classes(id),
    workspace_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- behavior_classes table
CREATE TABLE behavior_classes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    parent_id TEXT,
    icon TEXT,
    color TEXT,
    doc_path TEXT,
    source TEXT DEFAULT 'custom',
    author TEXT,
    version TEXT,
    is_system BOOLEAN DEFAULT 0,
    is_custom BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- indexes
CREATE INDEX idx_parent ON behaviors(parent_id);
CREATE INDEX idx_status ON behaviors(status);
CREATE INDEX idx_class ON behaviors(class_id);
CREATE INDEX idx_behavior_classes_parent ON behavior_classes(parent_id);
```

### Backup and Export

- Auto-backup to `~/ai-me/backups/`
- Support export to JSON/YAML format
- Support import from external data
- Support export/import behavior class directory trees

## Glossary

| Term | English | Description |
|------|---------|-------------|
| 行为 | Behavior | Core system unit, represents something to be done (instance) |
| 行为类 | BehaviorClass | Type definition of behavior, contains rules, experiences, methods |
| 行为类树 | Class Tree | Hierarchical inheritance structure of behavior classes |
| 行为树 | Behavior Tree | Hierarchical organization structure of behavior instances |
| 工作空间 | Workspace | Folder associated with a behavior |
| 根行为 | Root Behavior | Top-level behavior with no parent |
| 叶行为 | Leaf Behavior | End behavior with no children |
| 状态 | Status | Current lifecycle stage of behavior |
| 代理 | Agent | Refers to Claude Code and other AI assistants |
| 上下文 | Context | Currently active behavior and related information |
| 上下文模板变量 | Context Template Variable | Placeholders like `{{CURRENT_BEHAVIOR}}` substituted with real data |
| 模糊匹配 | Fuzzy Matching | Matching user intent to commands using similar keywords |
| 多轮对话 | Multi-turn Dialogue | Conversation context maintained across multiple exchanges |
| AI建议 | AI Suggestion | AI-generated recommendations for decomposition, class, or time |
| 阻塞行为 | Blocked Behavior | Behavior that cannot proceed due to dependencies or external factors |
| 时间聚合 | Time Aggregation | Hierarchical summation of time across parent-child behaviors |
