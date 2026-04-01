# harness-agent

## init-project
    {先输入一段关于项目的想法}//////////////////请根据我上面的想法生成项目的初始文档

## review-techstack
    发起多个agents来review TECH_STACK.md ，看看有没有可以优化的地方，有没有哪些坑需要注意，有没有不符合最佳实践的地方
## review-architecture
    发起多个agents来review ARCHITECTURE.md ，看看架构设计、模块划分有没有可以优化的地方，有没有哪些坑需要注意，有没有不符合最佳实践的地方
## review-checktree
    发起多个agents来review CheckTree.md，看看每个issue的module划分是否正确，看看还有没有需要增加的issue，看看issue的依赖关系是否合理，看看issue的划分是否还有更好的方案。注意测试只有搭建测试框架可以作为issue，具体的测试则不能作为issue，因为每个issue会有自己对应的测试。

## generate-issues
    发起多个agents根据CheckTree.md生成对应的issue yaml文档，要按照.clawboss-standards/templates/issue.md来生成，要特别注意每个issue的验收通过条件一定要尽量充分，前提依赖要尽量考虑完备

## review-issues
    发起多个agents review 每一个issue yaml文档，按照.clawboss-standards/sop/review-issue.md 来

## create-task
    在当前issue的tasks/目录下创建task YAML文件（按照.clawboss-standards/templates/task.md模板），格式为 .clawboss/checktree/issues/ISSUE-{ID}/tasks/TASK-{NUMBER}.yaml。每个task对应一个Claude Code session，记录目标、结果、执行时间和修改的文件。task可以有父子关系。

