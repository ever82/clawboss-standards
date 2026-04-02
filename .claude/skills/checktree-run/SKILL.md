---
name: checktree-run
description: Start CheckTree parallel development orchestrator
argument-hint: [--max-agents=N]
---

You are the CheckTree orchestrator runner. Your task is to start the parallel development system.

Run this command in the project root (D:\projects\ai-me):

```
python .clawboss-standards/scripts/orchestrator.py run --mode=auto $ARGUMENTS
```

If the user specifies arguments like `--max-agents=3`, include them in the command.

Report progress as Issues are processed. The orchestrator will:
1. Find all ready Issues (dependencies completed)
2. Start up to max parallel agents
3. Each agent works on its own Issue in an isolated worktree
4. Monitor progress and report completion
