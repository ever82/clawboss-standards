# Task Template

### Task YAML Structure

```yaml
id: "TASK-001"
title: "Task title"
status: "pending" | "in_progress" | "completed" | "failed" | "cancelled"

# Relationships
issue_id: "ISSUE-{MODULE}-{NUMBER}"    # Parent issue this task belongs to
parent_task: null                       # Parent task ID (null for top-level tasks)
child_tasks: []                         # List of child task IDs

# Goal and result
goal: |-
  What this task aims to accomplish
result: null                            # Filled on completion

# Session information
session_id: null                        # Claude Code session identifier
session_start: null                     # ISO 8601 datetime
session_end: null                       # ISO 8601 datetime
execution_time_minutes: null            # Calculated from start/end

# Metrics
files_modified: 0
lines_added: 0
lines_removed: 0
files_touched: []                       # List of file paths modified/created

# Timestamps
created_at: "2026-04-01T10:00:00+08:00"
started_at: null
completed_at: null

# Additional context
approach: null                          # Optional: planned approach before starting
blockers: []                            # List of blockers encountered
notes: ""                               # Free-form notes
```

### File Location

Tasks are stored inside each issue's folder:

```
.clawboss/checktree/issues/ISSUE-{MODULE}-{NUMBER}/tasks/TASK-{NUMBER}~{slug}.yaml
```

### Task ID Convention

- Sequential numbers within each issue: `TASK-001`, `TASK-002`, ...
- Globally unique when combined with issue_id
- Sub-tasks use the parent task's ID as reference in `parent_task` field

### Task Lifecycle

1. **pending**: Task created but not started
2. **in_progress**: Claude Code session is active
3. **completed**: Session finished successfully, `result` is filled
4. **failed**: Session encountered unrecoverable errors
5. **cancelled**: Task was abandoned or superseded

### Metrics Fields

| Field | Description |
|-------|-------------|
| `files_modified` | Total number of files modified/created |
| `lines_added` | Lines of code added |
| `lines_removed` | Lines of code removed |
| `files_touched` | Explicit list of file paths for traceability |
| `execution_time_minutes` | Wall-clock time from session_start to session_end |

### Task Decomposition

Tasks can be decomposed into sub-tasks using `parent_task` / `child_tasks`:

```yaml
# Parent task
id: "TASK-001"
child_tasks: ["TASK-002", "TASK-003"]

# Sub-task
id: "TASK-002"
parent_task: "TASK-001"
```
