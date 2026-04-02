# review-issue

检查 Issue 质量：验收条件逻辑、测试覆盖、复杂度。

## 1. 验收条件逻辑检查

验证"验收条件通过"与"Issue 解决"的关系：

| 检查项 | 判定 | 处理 |
|--------|------|------|
| 条件通过 ⟹ Issue 解决？ | 是/否 | 否 → 补充必要条件 |
| Issue 解决 ⟹ 条件通过？ | 是/否 | 否 → 移除冗余条件 |

**目标：充要条件。若是必要非充分，必须补充。**

## 2. 测试覆盖检查

每个验收条件检查五级覆盖，标记：欠缺/足够/不需要

| 测试类型 | 单元 | 集成 | E2E | AI | 人工 |
|----------|:--:|:--:|:--:|:--:|:--:|
| Infrastructure | 必须 | 必须 | - | - | - |
| Feature | 必须 | 必须 | 必须 | 推荐 | 可选 |
| Component | 必须 | - | - | 必须 | - |

## 3. 复杂度检查

| 指标 | 阈值 | 超出处理 |
|------|------|----------|
| 代码修改 | ≤1000 行 | 拆分为子 Issue |
| 测试耗时 | ≤10 分钟 | 优化或拆分 |

**拆分策略**：按层次(模型→API→UI)、按流程(验证→处理)、按模块(A→B)

## 执行模板

```yaml
review:
  issue_id: "ISSUE-XXX-001"
  logic: sufficient_necessary | sufficient | necessary
  coverage:
    criterion_1:
      unit: sufficient | lacking | not_needed
      integration: sufficient | lacking | not_needed
      e2e: sufficient | lacking | not_needed
      ai: sufficient | lacking | not_needed
      manual: sufficient | lacking | not_needed
  complexity:
    lines: 700
    test_time: 6
    split: false
  result: approved | needs_revision
```
