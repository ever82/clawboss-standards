---
name: checktree-milestone
description: Run integration tests for a milestone
argument-hint: [MILESTONE-ID]
---

You are the CheckTree milestone tester. Your task is to run integration tests for all Issues in a milestone.

Run this command in the project root (D:\projects\ai-me):

```
python .clawboss-standards/scripts/run-integration-tests.py --milestone=$ARGUMENTS
```

Milestone IDs are in format like `MILESTONE-1`, `MILESTONE-2`, etc.

Report:
- Which Issues are part of this milestone
- Test results
- Whether the milestone criteria are met
