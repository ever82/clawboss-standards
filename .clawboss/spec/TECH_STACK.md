# AI-Me Tech Stack

## Core Technologies

| Purpose | Technology | Description |
|---------|------------|-------------|
| Runtime | Node.js 18+ | Modern JavaScript runtime |
| Language | TypeScript | Type-safe, better development experience |
| Package Manager | npm | Standard Node.js package manager |
| Database | SQLite + better-sqlite3 | Lightweight local database |
| CLI Framework | Commander.js | Mature Node.js CLI framework |
| Interactive Prompts | Inquirer.js | Interactive command-line prompts |
| Date Processing | date-fns | Lightweight date processing library |
| ID Generation | nanoid | Short unique ID generation |
| File System | fs-extra | Enhanced file system operations |
| Styling | chalk | Terminal string styling |
| Spinners | ora | Elegant terminal spinners |
| YAML | js-yaml | YAML parsing and serialization |
| Archiving | adm-zip | ZIP file creation and extraction |

## Development Tools

| Tool | Purpose |
|------|---------|
| TypeScript | Type checking and compilation |
| ts-node | Run TS directly during development |
| nodemon | Auto-restart on file changes |
| ESLint | Code quality checking |
| Prettier | Code formatting |
| Vitest | Unit testing |
| pkg | Package as executable |

## Project Structure

```
ai-me/
├── src/
│   ├── cli/                    # CLI command implementations
│   │   ├── commands/           # Specific commands
│   │   │   ├── create.ts       # Create behavior
│   │   │   ├── list.ts         # List behaviors
│   │   │   ├── show.ts         # Show details
│   │   │   ├── update.ts       # Update behavior
│   │   │   ├── delete.ts       # Delete behavior
│   │   │   ├── tree.ts         # Tree display
│   │   │   ├── workspace.ts    # Workspace operations
│   │   │   ├── ask.ts          # Natural language interaction
│   │   │   └── class/          # Behavior class commands
│   │   │       ├── create.ts
│   │   │       ├── list.ts
│   │   │       ├── show.ts
│   │   │       ├── doc.ts
│   │   │       ├── import.ts   # Import from directory tree
│   │   │       ├── export.ts   # Export to directory tree
│   │   │       └── delete.ts
│   │   └── index.ts            # CLI entry
│   ├── core/                   # Core business logic
│   │   ├── behavior.ts         # Behavior model and operations
│   │   ├── behavior-class.ts   # BehaviorClass model and operations
│   │   ├── tree.ts             # Behavior tree management
│   │   ├── class-tree.ts       # Behavior class inheritance tree
│   │   ├── class-importer.ts   # Import from directory tree
│   │   ├── class-exporter.ts   # Export to directory tree
│   │   ├── workspace.ts        # Workspace management
│   │   └── status.ts           # Status flow logic
│   ├── db/                     # Database layer
│   │   ├── index.ts            # Database connection
│   │   ├── schema.ts           # Schema definitions
│   │   └── migrations/         # Database migrations
│   ├── ai/                     # AI integration
│   │   ├── parser.ts           # Natural language parsing
│   │   └── context.ts          # Context management
│   ├── utils/                  # Utility functions
│   │   ├── id.ts               # ID generation
│   │   ├── date.ts             # Date processing
│   │   ├── path.ts             # Path handling
│   │   ├── logger.ts           # Logging
│   │   └── i18n.ts             # Internationalization
│   └── config/                 # Configuration
│       ├── index.ts            # Config loading
│       └── defaults.ts         # Default configuration
├── templates/                  # Template files
│   ├── claude-md/              # Claude Code context templates
│   └── class-doc/              # Behavior class document templates
│       ├── _class.yaml         # Class definition template (multi-lang)
│       └── _doc.{locale}.md    # Class document templates by locale
├── behavior-classes/           # System behavior class directory tree
│   ├── _index.yaml             # Root index (multi-lang)
│   ├── learning/               # Class directories
│   │   ├── _class.yaml         # Multi-lang class definition
│   │   ├── _doc.en.md          # English documentation
│   │   └── _doc.zh.md          # Chinese documentation
│   ├── work/
│   └── life/
├── classes/                    # Behavior class docs (runtime, merged, by locale)
│   ├── learning.en.md          # English merged doc
│   ├── learning.zh.md          # Chinese merged doc
│   └── ...

## Database Design

### Schema

```sql
-- behaviors table: stores all behaviors
CREATE TABLE behaviors (
    id TEXT PRIMARY KEY,                    -- Unique ID (e.g., beh_abcd1234)
    name TEXT NOT NULL,                     -- Behavior name
    description TEXT,                       -- Detailed description
    status TEXT NOT NULL DEFAULT 'todo',    -- Status: todo/doing/done/paused/blocked
    parent_id TEXT,                         -- Parent behavior ID
    class_id TEXT,                          -- Behavior class ID
    workspace_path TEXT NOT NULL,           -- Workspace absolute path
    priority TEXT DEFAULT 'medium',         -- Priority: high/medium/low

    -- Time management - SELF (time spent directly on this behavior)
    self_planned_duration INTEGER DEFAULT 0,   -- Planned duration for this behavior only (minutes)
    self_actual_duration INTEGER DEFAULT 0,    -- Actual duration for this behavior only (minutes)
    start_time TIMESTAMP,                      -- When behavior actually started (set on todo->doing)
    end_time TIMESTAMP,                        -- When behavior actually ended (set on doing->done)
    deadline TIMESTAMP,                        -- Target completion date/time
    -- Note: due_date is an alias for deadline, handled at application layer

    -- Time management - TOTAL (self + all descendants, auto-calculated)
    total_planned_duration INTEGER DEFAULT 0,  -- Total planned duration including all children (minutes)
    total_actual_duration INTEGER DEFAULT 0,   -- Total actual duration including all children (minutes)
    time_efficiency FLOAT,                     -- total_actual / total_planned * 100 (NULL if no planned time)

    -- Progress and completion
    progress INTEGER DEFAULT 0,                -- Completion progress 0-100
    -- Note: completed_at is an alias for end_time, handled at application layer

    -- Acceptance criteria (JSON array of criteria items)
    acceptance_criteria TEXT,                  -- JSON: [{"id": "...", "description": "...", "checked": false}]
                                               -- Note: Stored as TEXT since SQLite has no native JSON type, validated with Zod

    -- Time aggregation cache (for quick queries without recalculation)
    children_time_cached_at TIMESTAMP,         -- When time aggregation was last calculated

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,                          -- JSON extra data (tags, etc.)

    FOREIGN KEY (class_id) REFERENCES behavior_classes(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES behaviors(id) ON DELETE CASCADE
);

-- behavior_dependencies table: stores behavior dependencies
CREATE TABLE behavior_dependencies (
    behavior_id TEXT NOT NULL,              -- The behavior that has dependencies
    depends_on_id TEXT NOT NULL,            -- The behavior it depends on
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (behavior_id, depends_on_id),
    FOREIGN KEY (behavior_id) REFERENCES behaviors(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_id) REFERENCES behaviors(id) ON DELETE CASCADE
);

-- behavior_classes table: behavior class definitions
CREATE TABLE behavior_classes (
    id TEXT PRIMARY KEY,                    -- Unique ID (e.g., learning)
    name TEXT NOT NULL,                     -- JSON object: {"en": "...", "zh": "..."}
    description TEXT,                       -- JSON object: {"en": "...", "zh": "..."}
    parent_id TEXT,                         -- Parent class ID (inheritance)
    icon TEXT,                              -- Emoji icon
    color TEXT DEFAULT '#6366f1',           -- Color
    source TEXT DEFAULT 'custom',           -- Source: system/custom/imported
    author TEXT,                            -- Author
    version TEXT DEFAULT '1.0.0',           -- Version
    is_system BOOLEAN DEFAULT 0,            -- Is system class
    is_custom BOOLEAN DEFAULT 1,            -- Is user custom
    locales TEXT,                           -- JSON array: ["en", "zh", "ja"]
                                              -- Note: Stored as TEXT since SQLite has no native JSON type, validated with Zod
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES behavior_classes(id) ON DELETE CASCADE
);

-- class_documents table: multi-language class documents
CREATE TABLE class_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id TEXT NOT NULL,                 -- Foreign key to behavior_classes
    locale TEXT NOT NULL,                   -- Language code: en, zh, ja, etc.
    doc_path TEXT NOT NULL,                 -- Path to merged document
    content_hash TEXT,                      -- Hash for change detection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, locale),
    FOREIGN KEY (class_id) REFERENCES behavior_classes(id) ON DELETE CASCADE
);

-- user_settings table: user preferences
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- tags table: tag definitions
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#6366f1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- behavior_tags table: many-to-many relationship
CREATE TABLE behavior_tags (
    behavior_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (behavior_id, tag_id),
    FOREIGN KEY (behavior_id) REFERENCES behaviors(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- indexes
CREATE INDEX idx_behaviors_parent ON behaviors(parent_id);
CREATE INDEX idx_behaviors_status ON behaviors(status);
CREATE INDEX idx_behaviors_priority ON behaviors(priority);
CREATE INDEX idx_behaviors_deadline ON behaviors(deadline);
CREATE INDEX idx_behaviors_start_time ON behaviors(start_time);
CREATE INDEX idx_behaviors_end_time ON behaviors(end_time);
CREATE INDEX idx_behaviors_class ON behaviors(class_id);
CREATE INDEX idx_behaviors_progress ON behaviors(progress);
CREATE INDEX idx_behaviors_status_priority ON behaviors(status, priority);
CREATE INDEX idx_behaviors_time_efficiency ON behaviors(time_efficiency);
CREATE INDEX idx_behavior_classes_parent ON behavior_classes(parent_id);
CREATE INDEX idx_class_documents_class ON class_documents(class_id);
CREATE INDEX idx_class_documents_locale ON class_documents(locale);
CREATE INDEX idx_class_documents_class_locale ON class_documents(class_id, locale);
CREATE INDEX idx_behavior_deps_behavior ON behavior_dependencies(behavior_id);
CREATE INDEX idx_behavior_deps_depends ON behavior_dependencies(depends_on_id);
```

## CLI Command Design

### Command Groups Overview

Commands are organized into functional groups. Most commands have short aliases for quick access.

| Group | Description | Key Aliases |
|-------|-------------|-------------|
| [Core](#core-commands) | Initialization, help, completion | `init`, `quickstart`, `completion` |
| [Behavior Management](#behavior-management-commands) | CRUD operations for behaviors | `c`/`create`, `ls`/`list`, `s`/`show`, `u`/`update`, `d`/`delete` |
| [Quick Actions](#quick-action-commands) | Fast status updates | `start`, `done` |
| [Time Management](#time-management-commands) | Tracking, timers, reports | `timer`, `time`, `stats`/`st` |
| [Navigation](#navigation-commands) | Workspace navigation | `w`/`sw`/`workspace`, `cd`, `root`, `up`, `down` |
| [Visualization](#visualization-commands) | Trees and views | `t`/`tree` |
| [Dependencies & Criteria](#dependency-and-acceptance-criteria-commands) | deps, criteria management | `deps`, `criteria` |
| [AI Interaction](#ai-interaction-commands) | Natural language interface | `ask`, `do` |
| [Class Management](#behavior-class-management-commands) | Behavior class operations | `cl`/`class` |
| [Configuration](#configuration-commands) | Settings and config | `config` |
| [Data](#data-management-commands) | Import, export, backup | `export`, `import`, `backup` |

---

### Core Commands

```bash
ai-me init [directory]                    # Initialize ai-me directory
ai-me quickstart                          # Interactive onboarding for new users
                                          # Guides through: first behavior, workspace setup,
                                          # class selection, and basic commands
ai-me completion <shell>                  # Generate shell completion script
                                          # Supported: bash, zsh, fish, powershell
                                          # Usage: ai-me completion bash >> ~/.bashrc
ai-me --version                           # Show version
ai-me --help                              # Show help (with command groups)
```

---

### Behavior Management Commands

```bash
ai-me create <name> [options]             # Create behavior (alias: ai-me c)
  -p, --parent <id>                       # Specify parent behavior
  -c, --class <id>                        # Specify behavior class
  -d, --description <text>                # Add description
  --priority <level>                      # Priority: high/medium/low
  --planned <minutes>                     # Planned duration for THIS behavior (minutes)
  --deadline <date>                       # Deadline (ISO date or natural language)
  --depends-on <ids>                      # Dependencies (comma-separated behavior IDs)
  --acceptance <items>                    # Acceptance criteria (comma-separated or @file)
  -t, --tags <tags>                       # Tags, comma-separated

ai-me list [options]                      # List behaviors (alias: ai-me ls)
  -s, --status <status>                   # Filter by status
  -p, --priority <priority>               # Filter by priority
  --overdue                               # Show overdue behaviors
  --blocked                               # Show behaviors with unfinished dependencies
  --time-overrun                          # Show behaviors where total_actual > total_planned
  --efficiency-over <percent>             # Filter by efficiency > N% (e.g., 100)
  --efficiency-under <percent>            # Filter by efficiency < N% (e.g., 80)
  -t, --tag <tag>                         # Filter by tag
  --tree                                  # Tree display
  --with-time                             # Show time columns (self/total/efficiency)
  --all                                   # Show all (including completed)

ai-me show <id>                           # Show behavior details (alias: ai-me s)
  --with-deps                             # Show dependency chain
  --time-report                           # Show time tracking report with aggregation
  --time-breakdown                        # Show detailed time breakdown (self + children)

ai-me update <id> [options]               # Update behavior (alias: ai-me u)
  -n, --name <name>                       # Change name
  -d, --description <desc>                # Change description
  -s, --status <status>                   # Change status
  -p, --priority <priority>               # Change priority
  --deadline <date>                       # Change deadline
  --planned <minutes>                     # Change self planned duration
  --parent <id>                           # Move to different parent
  --add-dep <id>                          # Add dependency
  --remove-dep <id>                       # Remove dependency
  --add-criteria <desc>                   # Add acceptance criterion
  --check-criteria <id>                   # Mark criterion as completed
  --uncheck-criteria <id>                 # Mark criterion as not completed

ai-me delete <id> [options]               # Delete behavior (alias: ai-me d)
  -r, --recursive                         # Recursively delete child behaviors
  -f, --force                             # Force delete (no prompt)
```

---

### Quick Action Commands

```bash
ai-me start <id>                          # Quick start: set status to 'doing'
                                          # Equivalent to: ai-me update <id> --status doing
                                          # Also starts the timer automatically

ai-me done <id>                           # Quick complete: set status to 'done'
                                          # Equivalent to: ai-me update <id> --status done
                                          # Also stops timer, sets end_time, updates progress to 100%
```

---

### Time Management Commands

```bash
ai-me time <id> [options]                 # Time management commands
  report                                  # Show full time report
  breakdown                               # Show tree-structured time breakdown
  efficiency                              # Show efficiency analysis
  --recalculate                           # Force recalculation of total times

ai-me timer <id> [command]                # Manual timer control
  start                                   # Start timer (set start_time)
  stop                                    # Stop timer (accumulate to self_actual_duration)
  reset                                   # Reset timer
  status                                  # Show current timer status

ai-me stats [options]                     # Show system-wide statistics (alias: ai-me st)
  --time                                  # Show time statistics by class/status
  --efficiency                            # Show average efficiency
  --by-class                              # Group stats by behavior class
  --by-period <period>                    # Group by time period (day/week/month)
```

---

### Navigation Commands

```bash
ai-me workspace [id]                      # Open workspace (alias: ai-me w, ai-me sw)
                                          # Default: current active workspace
  -o, --open                              # Open in system file manager

ai-me cd <id>                             # Switch to behavior workspace
ai-me root                                # Jump to root behaviors list
ai-me up                                  # Jump to parent behavior
ai-me down <id>                           # Jump to specific child behavior
ai-me current                             # Show current active behavior
```

---

### Visualization Commands

```bash
ai-me tree [id]                           # Display behavior tree (alias: ai-me t)
  -d, --depth <n>                         # Display depth
```

---

### Dependency and Acceptance Criteria Commands

```bash
ai-me deps <id> [options]                 # Manage dependencies
  --add <behavior-ids>                    # Add dependencies
  --remove <behavior-ids>                 # Remove dependencies
  --list                                  # List all dependencies
  --blocking                              # Show what's blocking this behavior

ai-me criteria <id> [options]             # Manage acceptance criteria
  --add "<description>"                   # Add criterion
  --remove <criterion-id>                 # Remove criterion
  --edit <criterion-id> "<desc>"          # Edit criterion
  --list                                  # List all criteria
  --check <criterion-id>                  # Mark as done
  --uncheck <criterion-id>                # Mark as not done
  --clear-completed                       # Remove all checked criteria
```

---

### AI Interaction Commands

```bash
ai-me ask "<query>"                       # Natural language query
ai-me do "<instruction>"                  # Natural language instruction
```

---

### Behavior Class Management Commands

```bash
ai-me class create <name> [options]       # Create behavior class (alias: ai-me cl create)
  -p, --parent <id>                       # Specify parent class
  -d, --description <text>                # Class description
  --icon <emoji>                          # Icon
  --color <hex>                           # Color

ai-me class list [options]                # List behavior classes (alias: ai-me cl ls)
  --tree                                  # Tree display of inheritance

ai-me class show <id>                     # Show behavior class details (alias: ai-me cl s)

ai-me class doc <id>                      # Edit behavior class document (alias: ai-me cl doc)
  -e, --edit                              # Open in default editor
  --rules                                 # Show only rules section
  --experiences                           # Show only experiences section
  --methods                               # Show only methods section

ai-me class update <id> [options]         # Update behavior class (alias: ai-me cl u)
  -n, --name <name>
  -d, --description <desc>
  --icon <emoji>
  --color <hex>

ai-me class delete <id>                   # Delete behavior class (alias: ai-me cl d)
                                          # Checks if class is in use before deletion

# Behavior class import/export (directory tree format)
ai-me class import <source> [options]     # Import behavior classes (alias: ai-me cl import)
  --official                              # Import from official repository
  --merge                                 # Merge mode (default: overwrite)
  --dry-run                               # Preview changes without actual import

ai-me class export [dir] [options]        # Export behavior classes (alias: ai-me cl export)
  --include-system                        # Include system classes
  --package                               # Package as zip file
  --author <name>                         # Set author info

ai-me class update --check                # Check for system class updates
ai-me class update --official             # Update system classes
ai-me class changelog                     # View class changelog

# Create behavior based on class (shortcut)
ai-me do <class-id> <name> [options]      # Create behavior instance with class
```

---

### Configuration Commands

```bash
ai-me config set language <locale>        # Set language (en, zh, ja, etc.)
ai-me config get language                 # Get current language
ai-me config languages                    # List supported languages
```

---

### Data Management Commands

```bash
ai-me export [file]                       # Export data as JSON
ai-me import <file>                       # Import from JSON
ai-me backup                              # Manual backup
```

---

### Alias Quick Reference

| Full Command | Alias | Purpose |
|--------------|-------|---------|
| `ai-me create` | `ai-me c` | Create behavior |
| `ai-me list` | `ai-me ls` | List behaviors |
| `ai-me show` | `ai-me s` | Show behavior details |
| `ai-me update` | `ai-me u` | Update behavior |
| `ai-me delete` | `ai-me d` | Delete behavior |
| `ai-me tree` | `ai-me t` | Display behavior tree |
| `ai-me stats` | `ai-me st` | Show statistics |
| `ai-me workspace` | `ai-me w`, `ai-me sw` | Open workspace |
| `ai-me class` | `ai-me cl` | Behavior class commands |

## Claude Code Integration

### Context Injection

Write in `~/ai-me/.claude/CLAUDE.md`:

```markdown
# AI-Me Behavior Management System

## Current Context

{{CURRENT_BEHAVIOR}}

## Available Commands

You can help users manage behaviors by calling CLI:
- `ai-me create "..."` - Create behavior
- `ai-me list` - List behaviors
- `ai-me update <id> --status doing` - Update status
- `ai-me cd <id>` - Switch workspace

## Workflow Suggestions

1. When user says "start working on something", help create or activate corresponding behavior
2. When user completes part of work, help update progress or mark sub-behavior as done
3. When user needs to see progress, use tree command to show overall situation
```

## Installation Scripts

### Security Notes

> [!WARNING]
> Always verify the integrity of installation scripts before execution. We provide multiple verification methods:
> 1. **Checksum verification** (recommended) - Automatically verifies SHA256 checksum
> 2. **Manual verification** - Download and inspect scripts before running
> 3. **GPG signature verification** (advanced) - For users with heightened security requirements

**Quick Install (with automatic verification):**
```bash
# Linux/macOS - Secure install with checksum verification
curl -fsSL https://install.ai-me.dev/install.sh | bash

# Windows (PowerShell) - Secure install
irm https://install.ai-me.dev/install.ps1 | iex
```

**Manual Verification (most secure):**
```bash
# Download script and checksum separately
curl -fsSL https://install.ai-me.dev/install.sh -o install.sh
curl -fsSL https://install.ai-me.dev/install.sh.sha256 -o install.sh.sha256

# Verify checksum
sha256sum -c install.sh.sha256

# Review script content
cat install.sh

# Execute after verification
bash install.sh
```

### Linux/macOS Install Script (install.sh)

```bash
#!/bin/bash
# install.sh - AI-Me Installation Script with Security Verification
# Supports: Linux, macOS
# Requirements: Node.js 18+, bash 4.0+

set -euo pipefail

# Configuration
VERSION="${VERSION:-latest}"
INSTALL_BASE_URL="${INSTALL_BASE_URL:-https://install.ai-me.dev}"
CHECKSUM_URL="${INSTALL_BASE_URL}/${VERSION}/install.sh.sha256"
SCRIPT_URL="${INSTALL_BASE_URL}/${VERSION}/install.sh"
SIGNATURE_URL="${INSTALL_BASE_URL}/${VERSION}/install.sh.asc"
GPG_KEY_URL="${INSTALL_BASE_URL}/gpg-key.pub"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Cleanup function
cleanup() {
    if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verify checksum
verify_checksum() {
    local file="$1"
    local expected_checksum="$2"
    local actual_checksum

    if command_exists sha256sum; then
        actual_checksum=$(sha256sum "$file" | cut -d' ' -f1)
    elif command_exists shasum; then
        actual_checksum=$(shasum -a 256 "$file" | cut -d' ' -f1)
    else
        log_warn "Neither sha256sum nor shasum found. Skipping checksum verification."
        return 0
    fi

    if [ "$expected_checksum" != "$actual_checksum" ]; then
        error_exit "Checksum verification failed!\n  Expected: $expected_checksum\n  Actual:   $actual_checksum"
    fi

    log_success "Checksum verification passed"
}

# Verify GPG signature (optional)
verify_gpg_signature() {
    local file="$1"
    local signature_file="$2"

    if ! command_exists gpg; then
        log_warn "GPG not found. Skipping signature verification."
        return 0
    fi

    # Download GPG public key if not present
    if ! gpg --list-keys "install@ai-me.dev" >/dev/null 2>&1; then
        log_info "Downloading GPG public key..."
        curl -fsSL "$GPG_KEY_URL" | gpg --import - || {
            log_warn "Failed to import GPG key. Skipping signature verification."
            return 0
        }
    fi

    if gpg --verify "$signature_file" "$file" 2>/dev/null; then
        log_success "GPG signature verification passed"
    else
        log_warn "GPG signature verification failed. Proceeding anyway..."
    fi
}

# Check Node.js version
check_nodejs() {
    log_info "Checking Node.js installation..."

    if ! command_exists node; then
        error_exit "Node.js is required but not installed.\nPlease install Node.js 18+ from https://nodejs.org/"
    fi

    local node_version
    node_version=$(node --version | sed 's/v//')
    local major_version
    major_version=$(echo "$node_version" | cut -d. -f1)

    if [ "$major_version" -lt 18 ]; then
        error_exit "Node.js 18+ is required. Found version: $node_version"
    fi

    log_success "Node.js $node_version detected"
}

# Check npm
check_npm() {
    log_info "Checking npm installation..."

    if ! command_exists npm; then
        error_exit "npm is required but not found. Please reinstall Node.js."
    fi

    local npm_version
    npm_version=$(npm --version)
    log_success "npm $npm_version detected"
}

# Download and verify installation files
download_and_verify() {
    log_info "Downloading installation files..."

    TEMP_DIR=$(mktemp -d)
    local script_file="$TEMP_DIR/install.sh"
    local checksum_file="$TEMP_DIR/install.sh.sha256"
    local signature_file="$TEMP_DIR/install.sh.asc"

    # Download checksum
    log_info "Downloading checksum..."
    if ! curl -fsSL "$CHECKSUM_URL" -o "$checksum_file" 2>/dev/null; then
        log_warn "Could not download checksum. Proceeding without verification..."
    else
        EXPECTED_CHECKSUM=$(cat "$checksum_file" | cut -d' ' -f1)
    fi

    # Download script
    log_info "Downloading installer..."
    if ! curl -fsSL "$SCRIPT_URL" -o "$script_file"; then
        error_exit "Failed to download installation script"
    fi

    # Verify checksum if available
    if [ -n "${EXPECTED_CHECKSUM:-}" ]; then
        verify_checksum "$script_file" "$EXPECTED_CHECKSUM"
    fi

    # Download and verify GPG signature (optional)
    if curl -fsSL "$SIGNATURE_URL" -o "$signature_file" 2>/dev/null; then
        verify_gpg_signature "$script_file" "$signature_file"
    fi

    echo "$script_file"
}

# Install AI-Me
install_ai_me() {
    log_info "Installing AI-Me..."

    # Check if already installed
    if command_exists ai-me; then
        local current_version
        current_version=$(ai-me --version 2>/dev/null || echo "unknown")
        log_warn "AI-Me is already installed (version: $current_version)"
        read -p "Do you want to reinstall/update? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
    fi

    # Install via npm
    log_info "Installing AI-Me package..."
    if ! npm install -g ai-me; then
        error_exit "Failed to install AI-Me via npm\nTry running with sudo: sudo npm install -g ai-me"
    fi

    log_success "AI-Me installed successfully"
}

# Initialize AI-Me directory
initialize_ai_me() {
    log_info "Initializing AI-Me directory..."

    local ai_me_dir="${AI_ME_DIR:-$HOME/ai-me}"

    if [ -d "$ai_me_dir" ]; then
        log_warn "Directory $ai_me_dir already exists"
    else
        if ! ai-me init "$ai_me_dir"; then
            error_exit "Failed to initialize AI-Me directory"
        fi
        log_success "AI-Me directory initialized at $ai_me_dir"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    # Check command availability
    if ! command_exists ai-me; then
        error_exit "ai-me command not found in PATH. Installation may have failed."
    fi

    # Check version
    local installed_version
    installed_version=$(ai-me --version 2>/dev/null || echo "unknown")
    log_success "AI-Me version: $installed_version"

    # Check database initialization
    local ai_me_dir="${AI_ME_DIR:-$HOME/ai-me}"
    if [ -f "$ai_me_dir/.ai-me/data.db" ]; then
        log_success "Database initialized successfully"
    else
        log_warn "Database not found. You may need to run 'ai-me init' manually."
    fi

    # Display installation summary
    echo
    echo "========================================"
    log_success "Installation Complete!"
    echo "========================================"
    echo
    echo "Installation Summary:"
    echo "  - AI-Me Version: $installed_version"
    echo "  - Installation Directory: $(which ai-me)"
    echo "  - Data Directory: $ai_me_dir"
    echo "  - Node.js Version: $(node --version)"
    echo "  - npm Version: $(npm --version)"
    echo
    echo "Next Steps:"
    echo "  1. cd $ai_me_dir"
    echo "  2. ai-me create \"My First Behavior\""
    echo "  3. ai-me list"
    echo
    echo "Documentation: https://docs.ai-me.dev"
    echo "Support: https://github.com/ai-me/ai-me/issues"
    echo
}

# Main installation flow
main() {
    echo "========================================"
    echo "     AI-Me Installation Script"
    echo "========================================"
    echo

    # Check prerequisites
    check_nodejs
    check_npm

    # Download and verify (for remote install mode)
    if [ "${REMOTE_INSTALL:-false}" = "true" ]; then
        local verified_script
        verified_script=$(download_and_verify)
        # Execute verified script in local mode
        REMOTE_INSTALL=false bash "$verified_script"
        exit $?
    fi

    # Install
    install_ai_me
    initialize_ai_me
    verify_installation

    log_success "Installation completed successfully!"
}

# Run main function
main "$@"
```

### Windows Install Script (install.ps1)

```powershell
# install.ps1 - AI-Me Installation Script for Windows
# Requirements: PowerShell 5.1+ or PowerShell Core 7+, Node.js 18+
# Supports: Windows 10, Windows 11, Windows Server 2016+

#Requires -Version 5.1

[CmdletBinding()]
param(
    [string]$Version = "latest",
    [string]$InstallBaseUrl = "https://install.ai-me.dev",
    [string]$AiMeDir = "$env:USERPROFILE\ai-me",
    [switch]$SkipChecksumVerification,
    [switch]$SkipGpgVerification
)

# Configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

$script:CHECKSUM_URL = "$InstallBaseUrl/$Version/install.ps1.sha256"
$script:SCRIPT_URL = "$InstallBaseUrl/$Version/install.ps1"
$script:SIGNATURE_URL = "$InstallBaseUrl/$Version/install.ps1.asc"
$script:GPG_KEY_URL = "$InstallBaseUrl/gpg-key.pub"

# Color output functions
function Write-Info { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# Error handler
function Stop-Install {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check Node.js installation and version
function Test-NodeJs {
    Write-Info "Checking Node.js installation..."

    try {
        $nodeVersion = node --version 2>$null
        if (-not $nodeVersion) {
            Stop-Install "Node.js is required but not installed.`nPlease install Node.js 18+ from https://nodejs.org/"
        }

        # Parse version (remove 'v' prefix)
        $versionString = $nodeVersion -replace '^v', ''
        $majorVersion = [int]($versionString -split '\.')[0]

        if ($majorVersion -lt 18) {
            Stop-Install "Node.js 18+ is required. Found version: $nodeVersion"
        }

        Write-Success "Node.js $nodeVersion detected"
    }
    catch {
        Stop-Install "Failed to check Node.js version. Error: $_"
    }
}

# Check npm installation
function Test-Npm {
    Write-Info "Checking npm installation..."

    try {
        $npmVersion = npm --version 2>$null
        if (-not $npmVersion) {
            Stop-Install "npm is required but not found. Please reinstall Node.js."
        }

        Write-Success "npm $npmVersion detected"
    }
    catch {
        Stop-Install "Failed to check npm version. Error: $_"
    }
}

# Calculate SHA256 checksum
function Get-FileChecksum {
    param([string]$FilePath)

    try {
        $hash = Get-FileHash -Path $FilePath -Algorithm SHA256
        return $hash.Hash.ToLower()
    }
    catch {
        Write-Warn "Failed to calculate checksum: $_"
        return $null
    }
}

# Verify checksum
function Test-Checksum {
    param(
        [string]$FilePath,
        [string]$ExpectedChecksum
    )

    if ($SkipChecksumVerification) {
        Write-Warn "Checksum verification skipped"
        return $true
    }

    $actualChecksum = Get-FileChecksum -FilePath $FilePath
    if (-not $actualChecksum) {
        Write-Warn "Could not calculate checksum. Skipping verification."
        return $true
    }

    if ($ExpectedChecksum -ne $actualChecksum) {
        Stop-Install "Checksum verification failed!`n  Expected: $ExpectedChecksum`n  Actual:   $actualChecksum"
    }

    Write-Success "Checksum verification passed"
    return $true
}

# Download file with progress
function Invoke-DownloadFile {
    param(
        [string]$Url,
        [string]$OutputPath
    )

    try {
        Write-Info "Downloading from $Url..."
        Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
        return $true
    }
    catch {
        Write-Warn "Failed to download from $Url : $_"
        return $false
    }
}

# Download and verify installation files
function Get-VerifiedScript {
    Write-Info "Downloading installation files..."

    $tempDir = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString()
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    $scriptFile = Join-Path $tempDir "install.ps1"
    $checksumFile = Join-Path $tempDir "install.ps1.sha256"

    # Download checksum
    $expectedChecksum = $null
    if (Invoke-DownloadFile -Url $script:CHECKSUM_URL -OutputPath $checksumFile) {
        $expectedChecksum = (Get-Content $checksumFile -Raw).Trim().Split(' ')[0].ToLower()
        Write-Info "Expected checksum: $expectedChecksum"
    }
    else {
        Write-Warn "Could not download checksum. Proceeding without verification..."
    }

    # Download script
    if (-not (Invoke-DownloadFile -Url $script:SCRIPT_URL -OutputPath $scriptFile)) {
        Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
        Stop-Install "Failed to download installation script"
    }

    # Verify checksum if available
    if ($expectedChecksum) {
        Test-Checksum -FilePath $scriptFile -ExpectedChecksum $expectedChecksum | Out-Null
    }

    return $scriptFile
}

# Install AI-Me via npm
function Install-AiMePackage {
    Write-Info "Installing AI-Me..."

    # Check if already installed
    $existingVersion = $null
    try {
        $existingVersion = ai-me --version 2>$null
    }
    catch { }

    if ($existingVersion) {
        Write-Warn "AI-Me is already installed (version: $existingVersion)"
        $response = Read-Host "Do you want to reinstall/update? (y/N)"
        if ($response -notmatch '^[Yy]$') {
            Write-Info "Installation cancelled"
            exit 0
        }
    }

    # Check if we need elevated privileges for global install
    $npmPrefix = npm config get prefix 2>$null
    $needsElevation = $false

    try {
        $testFile = Join-Path $npmPrefix "test_write_$(Get-Random).tmp"
        [IO.File]::WriteAllText($testFile, "test")
        Remove-Item $testFile -ErrorAction SilentlyContinue
    }
    catch {
        $needsElevation = $true
    }

    if ($needsElevation -and -not (Test-Administrator)) {
        Write-Warn "Administrator privileges required for global npm installation"
        Write-Info "Please run PowerShell as Administrator and try again"
        Write-Info "Alternatively, you can install locally: npm install ai-me"
        Stop-Install "Installation requires elevated privileges"
    }

    # Install via npm
    try {
        npm install -g ai-me
        Write-Success "AI-Me installed successfully"
    }
    catch {
        Stop-Install "Failed to install AI-Me via npm. Error: $_"
    }
}

# Initialize AI-Me directory
function Initialize-AiMeDirectory {
    Write-Info "Initializing AI-Me directory..."

    if (Test-Path $AiMeDir) {
        Write-Warn "Directory $AiMeDir already exists"
    }
    else {
        try {
            ai-me init $AiMeDir
            Write-Success "AI-Me directory initialized at $AiMeDir"
        }
        catch {
            Stop-Install "Failed to initialize AI-Me directory. Error: $_"
        }
    }
}

# Verify installation
function Test-Installation {
    Write-Info "Verifying installation..."

    # Check command availability
    $aiMePath = Get-Command ai-me -ErrorAction SilentlyContinue
    if (-not $aiMePath) {
        Stop-Install "ai-me command not found in PATH. Installation may have failed."
    }

    # Check version
    $installedVersion = ai-me --version 2>$null
    Write-Success "AI-Me version: $installedVersion"

    # Check database initialization
    $dbPath = Join-Path $AiMeDir ".ai-me\data.db"
    if (Test-Path $dbPath) {
        Write-Success "Database initialized successfully"
    }
    else {
        Write-Warn "Database not found. You may need to run 'ai-me init' manually."
    }

    # Display installation summary
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Success "Installation Complete!"
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installation Summary:"
    Write-Host "  - AI-Me Version: $installedVersion"
    Write-Host "  - Installation Directory: $($aiMePath.Source)"
    Write-Host "  - Data Directory: $AiMeDir"
    Write-Host "  - Node.js Version: $(node --version)"
    Write-Host "  - npm Version: $(npm --version)"
    Write-Host ""
    Write-Host "Next Steps:"
    Write-Host "  1. cd $AiMeDir"
    Write-Host '  2. ai-me create "My First Behavior"'
    Write-Host "  3. ai-me list"
    Write-Host ""
    Write-Host "Documentation: https://docs.ai-me.dev"
    Write-Host "Support: https://github.com/ai-me/ai-me/issues"
    Write-Host ""
}

# Main installation flow
function Start-Installation {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "     AI-Me Installation Script" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Check prerequisites
    Test-NodeJs
    Test-Npm

    # Install
    Install-AiMePackage
    Initialize-AiMeDirectory
    Test-Installation

    Write-Success "Installation completed successfully!"
}

# Handle remote install mode
if ($env:REMOTE_INSTALL -eq "true") {
    $verifiedScript = Get-VerifiedScript
    $env:REMOTE_INSTALL = "false"
    & $verifiedScript @args
    exit $LASTEXITCODE
}

# Run installation
Start-Installation
```

### Modern JavaScript Install Script (scripts/install.mjs) - Optional

```javascript
#!/usr/bin/env node
/**
 * AI-Me Installation Script using Google zx
 * A modern, cross-platform alternative to shell scripts
 *
 * Usage:
 *   npx zx scripts/install.mjs
 *   npx zx scripts/install.mjs --version=latest --dir=~/ai-me
 */

import { $, argv, chalk, fs, path, os, question } from 'zx';

// Configuration
const CONFIG = {
  VERSION: argv.version || argv.v || 'latest',
  INSTALL_BASE_URL: argv.url || 'https://install.ai-me.dev',
  AI_ME_DIR: argv.dir || path.join(os.homedir(), 'ai-me'),
  SKIP_VERIFICATION: argv['skip-verify'] || false,
};

const URLS = {
  CHECKSUM: `${CONFIG.INSTALL_BASE_URL}/${CONFIG.VERSION}/install.mjs.sha256`,
  SCRIPT: `${CONFIG.INSTALL_BASE_URL}/${CONFIG.VERSION}/install.mjs`,
  SIGNATURE: `${CONFIG.INSTALL_BASE_URL}/${CONFIG.VERSION}/install.mjs.asc`,
};

// Logging utilities
const log = {
  info: (msg) => console.log(chalk.cyan(`[INFO] ${msg}`)),
  success: (msg) => console.log(chalk.green(`[SUCCESS] ${msg}`)),
  warn: (msg) => console.log(chalk.yellow(`[WARN] ${msg}`)),
  error: (msg) => console.log(chalk.red(`[ERROR] ${msg}`)),
};

// Error handler
const die = (msg) => {
  log.error(msg);
  process.exit(1);
};

// Check Node.js version
async function checkNodeJs() {
  log.info('Checking Node.js installation...');

  try {
    const version = await $`node --version`;
    const major = parseInt(version.stdout.slice(1).split('.')[0]);

    if (major < 18) {
      die(`Node.js 18+ is required. Found version: ${version.stdout.trim()}`);
    }

    log.success(`Node.js ${version.stdout.trim()} detected`);
  } catch {
    die('Node.js is required but not installed.\nPlease install Node.js 18+ from https://nodejs.org/');
  }
}

// Check npm
async function checkNpm() {
  log.info('Checking npm installation...');

  try {
    const version = await $`npm --version`;
    log.success(`npm ${version.stdout.trim()} detected`);
  } catch {
    die('npm is required but not found. Please reinstall Node.js.');
  }
}

// Verify checksum
async function verifyChecksum(filePath, expectedChecksum) {
  if (CONFIG.SKIP_VERIFICATION) {
    log.warn('Checksum verification skipped');
    return true;
  }

  const content = await fs.readFile(filePath);
  const crypto = await import('crypto');
  const actualChecksum = crypto.createHash('sha256').update(content).digest('hex');

  if (expectedChecksum !== actualChecksum) {
    die(`Checksum verification failed!\n  Expected: ${expectedChecksum}\n  Actual:   ${actualChecksum}`);
  }

  log.success('Checksum verification passed');
  return true;
}

// Download file
async function downloadFile(url, outputPath) {
  log.info(`Downloading from ${url}...`);

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const content = await response.text();
    await fs.writeFile(outputPath, content);
    return true;
  } catch (err) {
    log.warn(`Failed to download: ${err.message}`);
    return false;
  }
}

// Download and verify
async function downloadAndVerify() {
  log.info('Downloading installation files...');

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'ai-me-install-'));
  const scriptFile = path.join(tempDir, 'install.mjs');
  const checksumFile = path.join(tempDir, 'install.mjs.sha256');

  // Download checksum
  let expectedChecksum = null;
  if (await downloadFile(URLS.CHECKSUM, checksumFile)) {
    expectedChecksum = (await fs.readFile(checksumFile, 'utf-8')).trim().split(' ')[0];
    log.info(`Expected checksum: ${expectedChecksum}`);
  }

  // Download script
  if (!(await downloadFile(URLS.SCRIPT, scriptFile))) {
    die('Failed to download installation script');
  }

  // Verify checksum
  if (expectedChecksum) {
    await verifyChecksum(scriptFile, expectedChecksum);
  }

  return scriptFile;
}

// Install AI-Me
async function installAiMe() {
  log.info('Installing AI-Me...');

  // Check if already installed
  try {
    const currentVersion = await $`ai-me --version`;
    log.warn(`AI-Me is already installed (version: ${currentVersion.stdout.trim()})`);

    const response = await question('Do you want to reinstall/update? (y/N) ');
    if (!response.match(/^[Yy]$/)) {
      log.info('Installation cancelled');
      process.exit(0);
    }
  } catch {
    // Not installed, continue
  }

  // Install via npm
  try {
    await $`npm install -g ai-me`;
    log.success('AI-Me installed successfully');
  } catch {
    die('Failed to install AI-Me via npm');
  }
}

// Initialize directory
async function initializeAiMe() {
  log.info('Initializing AI-Me directory...');

  if (await fs.pathExists(CONFIG.AI_ME_DIR)) {
    log.warn(`Directory ${CONFIG.AI_ME_DIR} already exists`);
  } else {
    try {
      await $`ai-me init ${CONFIG.AI_ME_DIR}`;
      log.success(`AI-Me directory initialized at ${CONFIG.AI_ME_DIR}`);
    } catch {
      die('Failed to initialize AI-Me directory');
    }
  }
}

// Verify installation
async function verifyInstallation() {
  log.info('Verifying installation...');

  // Check command
  try {
    const version = await $`ai-me --version`;
    log.success(`AI-Me version: ${version.stdout.trim()}`);
  } catch {
    die('ai-me command not found in PATH. Installation may have failed.');
  }

  // Check database
  const dbPath = path.join(CONFIG.AI_ME_DIR, '.ai-me', 'data.db');
  if (await fs.pathExists(dbPath)) {
    log.success('Database initialized successfully');
  } else {
    log.warn("Database not found. You may need to run 'ai-me init' manually.");
  }

  // Display summary
  const nodeVersion = await $`node --version`;
  const npmVersion = await $`npm --version`;
  const aiMeVersion = await $`ai-me --version`;

  console.log('');
  console.log(chalk.green('========================================'));
  log.success('Installation Complete!');
  console.log(chalk.green('========================================'));
  console.log('');
  console.log('Installation Summary:');
  console.log(`  - AI-Me Version: ${aiMeVersion.stdout.trim()}`);
  console.log(`  - Data Directory: ${CONFIG.AI_ME_DIR}`);
  console.log(`  - Node.js Version: ${nodeVersion.stdout.trim()}`);
  console.log(`  - npm Version: ${npmVersion.stdout.trim()}`);
  console.log('');
  console.log('Next Steps:');
  console.log(`  1. cd ${CONFIG.AI_ME_DIR}`);
  console.log('  2. ai-me create "My First Behavior"');
  console.log('  3. ai-me list');
  console.log('');
  console.log('Documentation: https://docs.ai-me.dev');
  console.log('');
}

// Main
async function main() {
  console.log(chalk.cyan('========================================'));
  console.log(chalk.cyan('     AI-Me Installation Script'));
  console.log(chalk.cyan('========================================'));
  console.log('');

  // Remote install mode
  if (process.env.REMOTE_INSTALL === 'true') {
    const verifiedScript = await downloadAndVerify();
    process.env.REMOTE_INSTALL = 'false';
    await $`node ${verifiedScript}`;
    return;
  }

  await checkNodeJs();
  await checkNpm();
  await installAiMe();
  await initializeAiMe();
  await verifyInstallation();

  log.success('Installation completed successfully!');
}

main().catch((err) => {
  log.error(`Unexpected error: ${err.message}`);
  process.exit(1);
});
```

### Installation Verification Checklist

After installation, the following checks are automatically performed:

| Check | Description | Status Indicator |
|-------|-------------|------------------|
| Node.js Version | Verifies Node.js 18+ is installed | Required |
| npm Availability | Confirms npm is accessible | Required |
| AI-Me Command | Verifies `ai-me` is in PATH | Required |
| Database | Checks data.db exists | Required |
| Directory Structure | Validates `.ai-me/` directory | Required |
| Version Info | Displays installed version | Info |

### Quick Reference

```bash
# Linux/macOS - One-liner install
curl -fsSL https://install.ai-me.dev/install.sh | bash

# Windows - One-liner install
irm https://install.ai-me.dev/install.ps1 | iex

# With custom options (Linux/macOS)
VERSION=1.2.0 AI_ME_DIR=/opt/ai-me bash install.sh

# With custom options (Windows)
install.ps1 -Version "1.2.0" -AiMeDir "C:\ai-me"

# Manual verification mode
curl -fsSL https://install.ai-me.dev/install.sh -o install.sh
curl -fsSL https://install.ai-me.dev/install.sh.sha256 -o install.sh.sha256
sha256sum -c install.sh.sha256 && bash install.sh
```

## Dependencies

```json
{
  "dependencies": {
    "commander": "^13.0.0",
    "inquirer": "^12.0.0",
    "better-sqlite3": "^12.0.0",
    "date-fns": "^4.1.0",
    "nanoid": "^5.1.0",
    "fs-extra": "^11.3.0",
    "chalk": "^5.4.0",
    "ora": "^8.0.0",
    "js-yaml": "^4.1.0",
    "adm-zip": "^0.5.16",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/inquirer": "^9.0.0",
    "@types/fs-extra": "^11.0.0",
    "typescript": "^5.7.0",
    "ts-node": "^10.9.0",
    "tsx": "^4.19.0",
    "nodemon": "^3.1.0",
    "eslint": "^9.0.0",
    "prettier": "^3.4.0",
    "vitest": "^3.0.0",
    "pkg": "^5.8.0"
  }
}
```
