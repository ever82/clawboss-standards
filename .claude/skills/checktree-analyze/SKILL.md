---
name: checktree-analyze
description: Analyze CheckTree dependency graph - shows ready and blocked Issues
---

You are the CheckTree analyzer. Your task is to analyze the dependency graph and report on the project status.

Run this command in the project root (D:\projects\ai-me):

```
python .clawboss-standards/scripts/orchestrator.py analyze
```

Report the output to the user, including:
- Status distribution (how many Issues in each state)
- List of ready-to-start Issues (no blocking dependencies)
- List of blocked Issues (waiting for dependencies)
- Topological order if available
