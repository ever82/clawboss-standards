# ClawBoss Templates

This directory contains all standard Markdown template files used by the ClawBoss project. The ClawBoss program uses these templates to initialize new projects or generate standard files.

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
