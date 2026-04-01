# AI-Me Database Schema V2

## Overview

This document describes the corrected and enhanced SQLite database schema for the AI-Me behavior management system. This version fixes issues from the original schema, including removed alias fields, added proper constraints, and comprehensive indexing.

---

## Table of Contents

1. [Schema Changes Summary](#schema-changes-summary)
2. [Table Definitions](#table-definitions)
3. [Indexes](#indexes)
4. [Data Validation Rules](#data-validation-rules)
5. [Migration Guide](#migration-guide)

---

## Schema Changes Summary

### Major Changes from V1

| Change Type | Description |
|-------------|-------------|
| **Removed** | `due_date` field (alias for `deadline`) |
| **Removed** | `completed_at` field (use `end_time` instead) |
| **Added** | `acceptance_criteria` independent table (replaces JSON field) |
| **Added** | CHECK constraints for data validation |
| **Added** | Additional indexes for performance |
| **Added** | Explicit ON DELETE/UPDATE cascade rules |
| **Added** | `sort_order` field for ordering within parent |
| **Added** | `estimated_time` and `time_unit` fields |

---

## Table Definitions

### 1. behaviors

Main table storing all behavior instances.

```sql
CREATE TABLE behaviors (
    -- Primary identification
    id TEXT PRIMARY KEY,
    -- Format: beh_{nanoid(10)}
    -- Example: beh_a1b2c3d4e5

    -- Core fields
    name TEXT NOT NULL,
    -- Behavior name/title

    description TEXT,
    -- Detailed description

    status TEXT NOT NULL DEFAULT 'todo',
    -- Status: todo | doing | done | paused | blocked

    priority TEXT DEFAULT 'medium',
    -- Priority: high | medium | low

    -- Hierarchy
    parent_id TEXT,
    -- Parent behavior ID (NULL for root behaviors)

    sort_order INTEGER DEFAULT 0,
    -- Display order among siblings

    -- Classification
    class_id TEXT,
    -- Associated behavior class ID

    workspace_path TEXT NOT NULL,
    -- Absolute path to behavior workspace folder

    -- Time Management - SELF (time spent directly on this behavior)
    self_planned_duration INTEGER DEFAULT 0 CHECK (self_planned_duration >= 0),
    -- Planned duration for this behavior only (minutes)

    self_actual_duration INTEGER DEFAULT 0 CHECK (self_actual_duration >= 0),
    -- Actual duration for this behavior only (minutes)

    start_time TIMESTAMP,
    -- When behavior actually started (set on todo->doing transition)

    end_time TIMESTAMP,
    -- When behavior actually ended (set on doing->done transition)

    deadline TIMESTAMP,
    -- Target completion date/time

    -- Time Management - TOTAL (auto-calculated from self + descendants)
    total_planned_duration INTEGER DEFAULT 0 CHECK (total_planned_duration >= 0),
    -- Total planned duration including all children (minutes)

    total_actual_duration INTEGER DEFAULT 0 CHECK (total_actual_duration >= 0),
    -- Total actual duration including all children (minutes)

    time_efficiency FLOAT CHECK (time_efficiency IS NULL OR (time_efficiency >= 0 AND time_efficiency <= 1000)),
    -- Efficiency ratio: total_actual / total_planned * 100
    -- NULL if no planned time, capped at 1000%

    -- Progress
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    -- Completion percentage 0-100

    -- Time tracking cache
    children_time_cached_at TIMESTAMP,
    -- When time aggregation was last calculated

    -- Additional timing
    estimated_time INTEGER,
    -- User estimate for completion time

    time_unit TEXT DEFAULT 'minute' CHECK (time_unit IN ('minute', 'hour', 'day')),
    -- Unit for estimated_time

    -- Metadata
    metadata TEXT,
    -- JSON extra data (custom fields)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Creation timestamp

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Last update timestamp

    -- Constraints
    CONSTRAINT chk_status CHECK (status IN ('todo', 'doing', 'done', 'paused', 'blocked')),
    CONSTRAINT chk_priority CHECK (priority IN ('high', 'medium', 'low')),

    -- Foreign Keys with cascade rules
    FOREIGN KEY (parent_id) REFERENCES behaviors(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (class_id) REFERENCES behavior_classes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
```

#### behaviors Table Notes

- **Self vs Total Time**: `self_*` fields track time directly spent on this behavior; `total_*` fields aggregate time from all descendants.
- **Time Efficiency**: Calculated as `total_actual_duration / total_planned_duration * 100`. NULL if `total_planned_duration` is 0.
- **Cascade Rules**: Deleting a parent behavior cascades to all children. Deleting a class sets `class_id` to NULL rather than deleting behaviors.

---

### 2. behavior_dependencies

Stores behavior dependency relationships (many-to-many).

```sql
CREATE TABLE behavior_dependencies (
    behavior_id TEXT NOT NULL,
    -- The behavior that has the dependency

    depends_on_id TEXT NOT NULL,
    -- The behavior it depends on

    dependency_type TEXT DEFAULT 'hard' CHECK (dependency_type IN ('hard', 'soft')),
    -- hard: must complete before starting
    -- soft: recommended but not blocking

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (behavior_id, depends_on_id),

    -- Constraints
    CONSTRAINT chk_not_self CHECK (behavior_id != depends_on_id),
    -- Prevent self-dependency

    -- Foreign Keys
    FOREIGN KEY (behavior_id) REFERENCES behaviors(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (depends_on_id) REFERENCES behaviors(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
```

#### behavior_dependencies Table Notes

- **Hard Dependency**: The behavior cannot start until all hard dependencies are `done`.
- **Soft Dependency**: Warning shown if not complete, but not blocking.
- **Cycle Prevention**: Application layer must ensure no circular dependencies exist.

---

### 3. acceptance_criteria

Stores acceptance criteria checklist items (separate from behaviors table).

```sql
CREATE TABLE acceptance_criteria (
    id TEXT PRIMARY KEY,
    -- Format: acr_{nanoid(10)}

    behavior_id TEXT NOT NULL,
    -- Associated behavior

    description TEXT NOT NULL,
    -- Criterion description

    is_checked BOOLEAN DEFAULT 0,
    -- Whether criterion is completed

    checked_at TIMESTAMP,
    -- When criterion was marked complete

    sort_order INTEGER DEFAULT 0,
    -- Display order

    criterion_type TEXT DEFAULT 'checklist' CHECK (criterion_type IN ('checklist', 'file', 'metric', 'external')),
    -- checklist: simple yes/no item
    -- file: must contain specific file
    -- metric: numeric threshold
    -- external: external deliverable (link)

    target_value TEXT,
    -- For metric type: target threshold

    actual_value TEXT,
    -- For metric type: actual value

    external_url TEXT,
    -- For external type: URL reference

    file_pattern TEXT,
    -- For file type: glob pattern to match

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key
    FOREIGN KEY (behavior_id) REFERENCES behaviors(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
```

#### acceptance_criteria Table Notes

- **Replaces JSON Field**: Original schema stored criteria as JSON in `behaviors.acceptance_criteria`.
- **Types**:
  - `checklist`: Simple checkbox item
  - `file`: Workspace must contain file matching `file_pattern`
  - `metric`: Numeric comparison between `actual_value` and `target_value`
  - `external`: Link to external deliverable (PR, deployed app, etc.)

---

### 4. behavior_classes

Stores behavior class definitions (templates/types).

```sql
CREATE TABLE behavior_classes (
    id TEXT PRIMARY KEY,
    -- Unique class identifier
    -- Example: learning, programming, writing

    name TEXT NOT NULL,
    -- JSON object: {"en": "Learning", "zh": "学习"}

    description TEXT,
    -- JSON object: {"en": "...", "zh": "..."}

    parent_id TEXT,
    -- Parent class for inheritance

    icon TEXT,
    -- Emoji icon

    color TEXT DEFAULT '#6366f1' CHECK (color REGEXP '^#[0-9A-Fa-f]{6}$'),
    -- Hex color code

    source TEXT DEFAULT 'custom' CHECK (source IN ('system', 'custom', 'imported')),
    -- system: officially maintained
    -- custom: user created
    -- imported: from external source

    author TEXT,
    -- Creator name

    version TEXT DEFAULT '1.0.0',
    -- Semantic version

    is_system BOOLEAN DEFAULT 0 CHECK (is_system IN (0, 1)),
    -- 1 if system class (protected from deletion)

    is_custom BOOLEAN DEFAULT 1 CHECK (is_custom IN (0, 1)),
    -- 1 if user custom class

    locales TEXT,
    -- JSON array: ["en", "zh", "ja"]

    tags TEXT,
    -- JSON array of class tags

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key
    FOREIGN KEY (parent_id) REFERENCES behavior_classes(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
```

#### behavior_classes Table Notes

- **Inheritance**: Single inheritance via `parent_id`. Documents are merged along inheritance chain.
- **System Protection**: `is_system=1` classes cannot be deleted or modified by users.
- **i18n**: `name` and `description` store JSON objects with locale keys.

---

### 5. class_documents

Stores multi-language class document metadata.

```sql
CREATE TABLE class_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    class_id TEXT NOT NULL,
    -- Foreign key to behavior_classes

    locale TEXT NOT NULL CHECK (locale REGEXP '^[a-z]{2}$'),
    -- Language code: en, zh, ja, etc.

    doc_path TEXT NOT NULL,
    -- Path to merged document file

    content_hash TEXT,
    -- SHA256 hash for change detection

    is_generated BOOLEAN DEFAULT 1 CHECK (is_generated IN (0, 1)),
    -- 1 if auto-generated from source files

    generated_at TIMESTAMP,
    -- When document was last generated

    source_paths TEXT,
    -- JSON array of source file paths

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one document per class per locale
    UNIQUE(class_id, locale),

    -- Foreign Key
    FOREIGN KEY (class_id) REFERENCES behavior_classes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
```

#### class_documents Table Notes

- **Runtime Documents**: Stores paths to merged documents in `~/ai-me/classes/` directory.
- **Source Tracking**: `source_paths` tracks which source files were used to generate this document.
- **Change Detection**: `content_hash` enables quick change detection for regeneration.

---

### 6. tags

Tag definitions for categorization.

```sql
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    -- Format: tag_{nanoid(10)}

    name TEXT UNIQUE NOT NULL,
    -- Unique tag name

    color TEXT DEFAULT '#6366f1' CHECK (color REGEXP '^#[0-9A-Fa-f]{6}$'),
    -- Tag color

    description TEXT,
    -- Tag description

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 7. behavior_tags

Many-to-many relationship between behaviors and tags.

```sql
CREATE TABLE behavior_tags (
    behavior_id TEXT NOT NULL,

    tag_id TEXT NOT NULL,

    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    assigned_by TEXT,
    -- User or system that assigned the tag

    PRIMARY KEY (behavior_id, tag_id),

    -- Foreign Keys
    FOREIGN KEY (behavior_id) REFERENCES behaviors(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (tag_id) REFERENCES tags(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
```

---

### 8. user_settings

User preferences and configuration.

```sql
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,
    -- Setting key

    value TEXT NOT NULL,
    -- Setting value (JSON for complex values)

    value_type TEXT DEFAULT 'string' CHECK (value_type IN ('string', 'number', 'boolean', 'json')),
    -- Data type hint

    description TEXT,
    -- Setting description

    is_system BOOLEAN DEFAULT 0 CHECK (is_system IN (0, 1)),
    -- 1 if system setting (protected)

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### user_settings Table Notes

- **Key Examples**: `language`, `default_workspace`, `theme`, `auto_backup_enabled`
- **Value Storage**: All values stored as TEXT; `value_type` helps with parsing.

---

## Indexes

### behaviors Table Indexes

```sql
-- Hierarchy lookup
CREATE INDEX idx_behaviors_parent ON behaviors(parent_id);

-- Status filtering
CREATE INDEX idx_behaviors_status ON behaviors(status);

-- Priority filtering
CREATE INDEX idx_behaviors_priority ON behaviors(priority);

-- Class filtering
CREATE INDEX idx_behaviors_class ON behaviors(class_id);

-- Deadline tracking (for overdue queries)
CREATE INDEX idx_behaviors_deadline ON behaviors(deadline) WHERE deadline IS NOT NULL;

-- Active behaviors by start time
CREATE INDEX idx_behaviors_start_time ON behaviors(start_time) WHERE start_time IS NOT NULL;

-- Sort order within parent
CREATE INDEX idx_behaviors_sort_order ON behaviors(parent_id, sort_order);

-- Combined index for common list queries
CREATE INDEX idx_behaviors_status_priority ON behaviors(status, priority);

-- Workspace path lookup
CREATE INDEX idx_behaviors_workspace ON behaviors(workspace_path);

-- Recently updated behaviors
CREATE INDEX idx_behaviors_updated_at ON behaviors(updated_at DESC);
```

### behavior_dependencies Table Indexes

```sql
-- Dependencies of a behavior
CREATE INDEX idx_deps_behavior ON behavior_dependencies(behavior_id);

-- Behaviors depending on a specific behavior
CREATE INDEX idx_deps_depends_on ON behavior_dependencies(depends_on_id);

-- Dependency type filtering
CREATE INDEX idx_deps_type ON behavior_dependencies(dependency_type);
```

### acceptance_criteria Table Indexes

```sql
-- Criteria for a behavior
CREATE INDEX idx_criteria_behavior ON acceptance_criteria(behavior_id);

-- Unchecked criteria (for completion checking)
CREATE INDEX idx_criteria_unchecked ON acceptance_criteria(behavior_id, is_checked) WHERE is_checked = 0;

-- Sort order
CREATE INDEX idx_criteria_sort ON acceptance_criteria(behavior_id, sort_order);
```

### behavior_classes Table Indexes

```sql
-- Parent class lookup
CREATE INDEX idx_classes_parent ON behavior_classes(parent_id);

-- System vs custom filtering
CREATE INDEX idx_classes_source ON behavior_classes(source);

-- System class protection
CREATE INDEX idx_classes_system ON behavior_classes(is_system) WHERE is_system = 1;
```

### class_documents Table Indexes

```sql
-- Documents by class
CREATE INDEX idx_docs_class ON class_documents(class_id);

-- Documents by locale
CREATE INDEX idx_docs_locale ON class_documents(locale);

-- Generated document tracking
CREATE INDEX idx_docs_generated ON class_documents(is_generated) WHERE is_generated = 1;
```

### tags Table Indexes

```sql
-- Tag name lookup
CREATE INDEX idx_tags_name ON tags(name);
```

### behavior_tags Table Indexes

```sql
-- Tags for a behavior
CREATE INDEX idx_behavior_tags_behavior ON behavior_tags(behavior_id);

-- Behaviors with a tag
CREATE INDEX idx_behavior_tags_tag ON behavior_tags(tag_id);
```

---

## Data Validation Rules

### Status Transitions

```sql
-- Enforced at application layer, documented here:
-- todo -> doing, paused, blocked
-- doing -> done, paused, blocked
-- paused -> doing, todo
-- blocked -> doing, todo
-- done -> doing, todo
```

### Priority Values

| Value | Description |
|-------|-------------|
| `high` | Urgent/critical behaviors |
| `medium` | Normal priority (default) |
| `low` | Can be deferred |

### Time Constraints

```sql
-- All duration fields must be non-negative
CHECK (self_planned_duration >= 0)
CHECK (self_actual_duration >= 0)
CHECK (total_planned_duration >= 0)
CHECK (total_actual_duration >= 0)

-- Progress must be 0-100
CHECK (progress >= 0 AND progress <= 100)

-- Efficiency capped at 1000% (10x over budget)
CHECK (time_efficiency IS NULL OR time_efficiency <= 1000)
```

### Color Format

```sql
-- Hex colors must match pattern
CHECK (color REGEXP '^#[0-9A-Fa-f]{6}$')
```

### Locale Format

```sql
-- Locale codes must be 2 lowercase letters
CHECK (locale REGEXP '^[a-z]{2}$')
```

---

## Migration Guide

### From V1 to V2

#### Step 1: Backup Data

```bash
# Create backup before migration
cp ai-me.db ai-me.db.v1.backup
```

#### Step 2: Create New Tables

```sql
-- Create acceptance_criteria table
CREATE TABLE acceptance_criteria (...);

-- Migrate JSON criteria to new table
INSERT INTO acceptance_criteria (id, behavior_id, description, is_checked)
SELECT
    'acr_' || lower(hex(randomblob(5))),
    b.id,
    json_extract(value, '$.description'),
    COALESCE(json_extract(value, '$.checked'), 0)
FROM behaviors b,
     json_each(COALESCE(b.acceptance_criteria, '[]'))
WHERE json_valid(COALESCE(b.acceptance_criteria, '[]'));
```

#### Step 3: Update behaviors Table

```sql
-- Remove alias fields (data preserved in deadline and end_time)
-- Note: SQLite doesn't support DROP COLUMN directly
-- Use table recreation approach:

-- 1. Create new behaviors table without alias fields
-- 2. Copy data: due_date -> deadline, completed_at -> end_time
-- 3. Drop old table, rename new table
-- 4. Recreate indexes
```

#### Step 4: Update Indexes

```sql
-- Remove obsolete index
DROP INDEX IF EXISTS idx_behaviors_due_date;

-- Create new indexes
CREATE INDEX idx_behaviors_sort_order ON behaviors(parent_id, sort_order);
CREATE INDEX idx_behaviors_status_priority ON behaviors(status, priority);
```

### Data Migration Checklist

- [ ] Backup existing database
- [ ] Extract JSON acceptance criteria to new table
- [ ] Verify `due_date` data is in `deadline` field
- [ ] Verify `completed_at` data is in `end_time` field
- [ ] Recreate behaviors table without alias columns
- [ ] Rebuild all indexes
- [ ] Verify foreign key integrity
- [ ] Run application tests

---

## Schema Diagram

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  behavior_      │     │                      │     │      tags       │
│  dependencies   │◄────┤     behaviors        ├────►│                 │
│                 │     │                      │     └─────────────────┘
└─────────────────┘     │  - id (PK)           │              │
                        │  - name              │              │
┌─────────────────┐     │  - status            │     ┌─────────────────┐
│ acceptance_     │◄────┤  - parent_id (FK)    │     │ behavior_tags   │
│ criteria        │     │  - class_id (FK)     │     │  (junction)     │
│                 │     │  - workspace_path    │     └─────────────────┘
└─────────────────┘     │  - deadline          │
                        │  - end_time          │
┌─────────────────┐     │  - progress          │
│ behavior_       │◄────┘                      │
│ classes         │                            │
│                 │     ┌──────────────────────┘
│  - id (PK)      │     │
│  - parent_id(FK)│◄────┘
│  - name (i18n)  │
└────────┬────────┘
         │
         │
┌────────▼────────┐
│ class_          │
│ documents       │
│                 │
│  - class_id(FK) │
│  - locale       │
└─────────────────┘
```

---

## Appendix: Quick Reference

### Common Queries

```sql
-- Get all active (non-done) behaviors
SELECT * FROM behaviors WHERE status != 'done' ORDER BY deadline ASC;

-- Get behaviors with incomplete criteria
SELECT b.*, COUNT(ac.id) as criteria_count
FROM behaviors b
LEFT JOIN acceptance_criteria ac ON b.id = ac.behavior_id AND ac.is_checked = 0
WHERE b.status != 'done'
GROUP BY b.id
HAVING criteria_count > 0;

-- Get overdue behaviors
SELECT * FROM behaviors
WHERE deadline < datetime('now')
  AND status NOT IN ('done', 'paused')
  AND deadline IS NOT NULL;

-- Get behavior tree with depth
WITH RECURSIVE tree AS (
    SELECT *, 0 as depth FROM behaviors WHERE parent_id IS NULL
    UNION ALL
    SELECT b.*, t.depth + 1
    FROM behaviors b
    JOIN tree t ON b.parent_id = t.id
)
SELECT * FROM tree ORDER BY depth, sort_order;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| V1 | 2024-03 | Initial schema |
| V2 | 2026-03-29 | Removed aliases, added constraints, split acceptance_criteria |
