# Issue Templates

### Issue YAML Structure

```yaml
id: "ISSUE-{MODULE}-1"
issue_number: 1
title: "Issue Title"
slug: "issue-slug"
status: "pending" | "in_progress" | "completed"
description: "Issue description"
is_parent: false | true  # If true, this issue has sub-issues
sub_issues:  # Only if is_parent: true
  - "ISSUE-{MODULE}-1-A"
  - "ISSUE-{MODULE}-1-B"
parent_issue: null | "ISSUE-{MODULE}-0"  # Set for sub-issues to reference parent
prerequisites:  # Issue IDs that must complete before this one
  - "ISSUE-{MODULE}-1"
created_at: "2026-03-27"
completed_at: null | "2026-03-27"
# When all acceptance criteria pass and guarantee the issue logic is implemented, it's sufficient. When any failing criterion guarantees the issue logic is not fully implemented, it's necessary. When both conditions are met, it's sufficient_necessary.
logic: sufficient_necessary | sufficient | necessary
# Acceptance criteria
criteria:
  - id: "ISSUE-{MODULE}-1~criterion-1"
    name: "Criterion name"
    description: "Criterion description"
    status: "pending" | "in_progress" | "passed" | "failed"
    coverage:
      # When issue is first created, it's either not_needed or lacking. Only change to sufficient after tests are written and verified adequate.
      unit: sufficient | lacking | not_needed
      integration: sufficient | lacking | not_needed
      e2e: sufficient | lacking | not_needed
      ai: sufficient | lacking | not_needed
      manual: sufficient | lacking | not_needed
    # Detailed description for each verification method. Required when the corresponding type in coverage is not not_needed.
    verification:
      # Unit test verification details
      unit:
        # Specific command to run tests, e.g.: "npm test -- src/utils/validator.test.ts"
        command: ""
        # List of expected test file paths
        test_files: []
      # Integration test verification details
      integration:
        command: ""
        test_files: []
      # E2E test verification details
      e2e:
        command: ""
        test_files: []
      # AI verification details - using AI for code review or feature validation
      ai:
        # AI verification prompt, should include specific requirements and checkpoints
        prompt: |
          Please verify the following acceptance criteria are met:
          1. ...
          2. ...
          Return format: {"passed": true/false, "reason": "detailed explanation"}
        # Context file paths required for AI verification
        context_files: []
        # AI model selection, e.g.: claude-opus-4-6, claude-sonnet-4-6
        model: "claude-sonnet-4-6"
      # Manual verification details - items requiring human manual inspection
      manual:
        # Specific instructions for manual verification, should detail check steps and expected results
        instructions: |
          1. Open browser and visit http://localhost:3000
          2. Click XXX button
          3. Verify YYY is displayed
        # Tools/environment required for verification
        required_tools: ["browser", "dev server"]
    # Indicates the time required to execute all tests, to be evaluated by AI
    execution_time: "<5 seconds"  # Optional
    prerequisites:
      - "ISSUE-{MODULE}-1~criterion-1"
```

### Folder Structure Convention

Each issue is stored in its own folder under `.clawboss/checktree/issues/`:

```
issues/
├── ISSUE-{MODULE}-{NUMBER}/
│   ├── ISSUE-{MODULE}-{NUMBER}~{slug}.yaml   # Issue definition
│   └── tasks/                                 # Tasks created during issue processing
│       ├── TASK-001~{slug}.yaml                # One YAML file per Claude Code session
│       └── TASK-002~{slug}.yaml
└── ...
```

**Task files** follow the schema defined in `templates/task.md`.

### File Naming Convention (Legacy)

Issues were previously stored as flat files in `.clawboss/checktree/issues_yaml/`:

```
ISSUE-{MODULE}-{NUMBER}~{slug}.yaml
ISSUE-{MODULE}-{NUMBER}-A~{sub-slug}.yaml  # Sub-issue
ISSUE-{MODULE}-{NUMBER}-H1~{sub-slug}.yaml  # Grouped sub-issue
```

These have been migrated to the folder structure above. The `issues_yaml/` directory is kept as backup.
