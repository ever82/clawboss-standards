---
name: checktree-itest
description: Run integration tests for specific Issues
argument-hint: [ISSUE-ID-1 ISSUE-ID-2 ...]
---

You are the CheckTree integration test runner. Your task is to run integration tests for specified Issues.

Run this command in the project root (D:\projects\ai-me):

```
python .clawboss-standards/scripts/run-integration-tests.py --issues $ARGUMENTS
```

Report:
- Which Issues are being tested
- Test progress and results
- Any failures or errors encountered
