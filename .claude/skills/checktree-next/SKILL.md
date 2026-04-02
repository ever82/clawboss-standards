---
name: checktree-next
description: Start development on a specific Issue
argument-hint: [ISSUE-ID]
---

You are the CheckTree Issue starter. Your task is to begin development on a specific Issue.

Run this command in the project root (D:\projects\ai-me):

```
python .clawboss-standards/scripts/orchestrator.py run --issue=$ARGUMENTS
```

The ISSUE-ID should be in format like `ISSUE-SETUP-001` or `ISSUE-CORE-001`.

Report what Issue is being started and confirm the worktree was created successfully.
