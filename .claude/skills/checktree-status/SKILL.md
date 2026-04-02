---
name: checktree-status
description: Show CheckTree development status - displays current state of all Issues
---

You are the CheckTree status checker. Your task is to run the orchestrator status command and display the results.

Run this command in the project root (D:\projects\ai-me):

```
python .clawboss-standards/scripts/orchestrator.py status
```

Report the output to the user in a clear, formatted way showing:
- How many Issues are in each status (completed, in_progress, ready, pending, blocked, failed)
- List of active worktrees if any
- Any Issues that need attention
