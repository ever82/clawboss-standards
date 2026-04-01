# AI-Me Behavior Management System

## Project Overview

AI-Me is an AI-driven personal behavior management system. It helps users break down large goals into actionable behaviors, organize them in a tree structure, and manage workspaces to track and complete each behavior systematically.

## Core Goals

1. **Behavior Decomposition**: Break complex behaviors into manageable sub-behaviors
2. **Status Tracking**: Clearly display the current status of each behavior
3. **Workspace**: Each behavior has an associated folder for related files
4. **AI-Driven**: Natural language interaction via Claude Code and other AI agents
5. **Easy Installation**: One-line installation for quick setup

## Target Users

- Individuals managing complex projects
- People who want systematic tracking of life/work goals
- Technical users comfortable with CLI and AI assistants
- Knowledge workers who need to organize large amounts of files

## Use Cases

1. **Project Management**: Decompose a project into requirements, design, development, testing phases, with specific tasks in each phase
2. **Learning Goals**: Break down learning a new skill into foundation, advanced, and practice modules
3. **Habit Building**: Track daily habit execution and progress
4. **Content Creation**: Manage the full workflow from ideation, outline, draft to publication

## System Boundaries

### Included Features

- Behavior CRUD operations (Create, Read, Update, Delete)
- Tree structure hierarchy management (parent-child relationships)
- Behavior status management (todo, doing, done, paused, blocked)
- Automatic workspace folder creation and management
- SQLite local data storage
- CLI command-line interface
- Behavior Class system (directory tree + YAML + Markdown)
  - System behavior class library (officially maintained, updatable)
  - User-defined behavior classes
  - Import/export directory tree format (for sharing)
- Claude Code integration (via context injection)

### Excluded Features

- Multi-user collaboration (purely personal local tool)
- Cloud sync (initial version)
- GUI (initial version)
- Mobile app (initial version)

## Distribution Methods

1. **Command-line install script**: `curl -sSL https://install.ai-me.dev | bash`
2. **npm**: `npm install -g ai-me`
3. **Homebrew**: `brew install ai-me`

## Project Structure

```
ai-me/
├── .clawboss/              # System configuration and metadata
│   ├── checktree/          # Behavior tree structure definitions
│   └── spec/               # System specification documents
├── data/                   # SQLite database
├── behavior-classes/       # System behavior class directory tree (YAML+Markdown)
│   ├── _index.yaml         # Root index
│   ├── learning/           # Behavior class directories
│   ├── work/
│   └── life/
├── classes/                # Behavior class docs storage (runtime, merged)
│   ├── {class-id}.md       # Each behavior class documentation
│   └── ...
├── workspaces/             # Behavior workspace root directory
│   ├── {behavior-id}/      # Individual folder for each behavior
│   └── ...
├── templates/              # System templates
│   └── class-doc/          # Behavior class document templates
├── cli/                    # CLI source code
└── docs/                   # User documentation
```

## Success Criteria

1. Users can create and manage behaviors through natural language
2. Behavior tree structure is clear and navigation is easy
3. Workspaces are automatically associated with seamless file management
4. Installation is simple, completed with one command
5. Integration with Claude Code is smooth and natural

## Related Links

- [Core Concepts](./CONCEPTS.md)
- [Tech Stack](./TECH_STACK.md)
- [Architecture](./ARCHITECTURE.md)
