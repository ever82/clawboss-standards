#!/usr/bin/env python3
"""
CheckTree Orchestrator - 并行 Issue 开发编排器

使用方法:
    python orchestrator.py run [--mode=auto|interactive] [--max-agents=N]
    python orchestrator.py analyze
    python orchestrator.py status
    python orchestrator.py cleanup
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import asyncio.subprocess


class IssueStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    MERGE_PENDING = "merge_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Issue:
    id: str
    module: str
    number: str
    title: str
    slug: str
    status: IssueStatus
    prerequisites: List[str]
    sub_issues: List[str]
    is_parent: bool
    yaml_path: Path
    worktree_path: Optional[Path] = None
    agent_pid: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0


@dataclass
class OrchestratorConfig:
    max_agents: int = 3
    max_retries: int = 2
    timeout_minutes: int = 120
    worktree_base_path: str = ".clawboss/worktrees"
    auto_cleanup_worktree: bool = False
    keep_on_failure: bool = True
    integration_auto_merge: bool = True
    integration_branch_prefix: str = "test/integration"
    e2e_trigger: str = "milestone"  # milestone | batch | manual
    e2e_batch_size: int = 5

    @classmethod
    def from_yaml(cls, path: Path) -> "OrchestratorConfig":
        if not path.exists():
            return cls()
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        parallel = data.get('parallel', {})
        worktree = data.get('worktree', {})
        testing = data.get('testing', {})
        integration = testing.get('integration', {})
        e2e = testing.get('e2e', {})

        return cls(
            max_agents=parallel.get('max_agents', 3),
            max_retries=parallel.get('max_retries', 2),
            timeout_minutes=parallel.get('timeout_minutes', 120),
            worktree_base_path=worktree.get('base_path', '.clawboss/worktrees'),
            auto_cleanup_worktree=worktree.get('auto_cleanup', False),
            keep_on_failure=worktree.get('keep_on_failure', True),
            integration_auto_merge=integration.get('auto_merge', True),
            integration_branch_prefix=integration.get('branch_prefix', 'test/integration'),
            e2e_trigger=e2e.get('trigger', 'milestone'),
            e2e_batch_size=e2e.get('batch_size', 5),
        )


class DependencyGraph:
    """解析和管理 Issue 依赖关系"""

    def __init__(self, issues: Dict[str, Issue]):
        self.issues = issues
        self.dependencies: Dict[str, Set[str]] = {}  # issue_id -> set of prerequisite ids
        self.dependents: Dict[str, Set[str]] = {}    # issue_id -> set of dependent ids
        self._build_graph()

    def _build_graph(self):
        """从 CheckTree.md 和 Issue YAML 构建依赖图"""
        for issue_id, issue in self.issues.items():
            self.dependencies[issue_id] = set(issue.prerequisites)
            self.dependents[issue_id] = set()

        # 反向填充 dependents
        for issue_id, deps in self.dependencies.items():
            for dep in deps:
                if dep in self.dependents:
                    self.dependents[dep].add(issue_id)

    def get_ready_issues(self) -> List[str]:
        """获取所有可以开始开发的 Issues（依赖都已完成）"""
        ready = []
        for issue_id, issue in self.issues.items():
            if issue.status not in [IssueStatus.PENDING, IssueStatus.BLOCKED]:
                continue

            # 检查所有依赖是否完成
            deps_completed = all(
                self.issues.get(dep, Issue(dep, "", "", "", "", IssueStatus.COMPLETED, [], [], False, Path())).status == IssueStatus.COMPLETED
                for dep in self.dependencies.get(issue_id, [])
            )

            if deps_completed:
                ready.append(issue_id)

        return ready

    def get_blocked_issues(self) -> List[str]:
        """获取因依赖未完成而被阻塞的 Issues"""
        blocked = []
        for issue_id, issue in self.issues.items():
            if issue.status != IssueStatus.PENDING:
                continue

            has_incomplete_deps = any(
                self.issues.get(dep, Issue(dep, "", "", "", "", IssueStatus.COMPLETED, [], [], False, Path())).status != IssueStatus.COMPLETED
                for dep in self.dependencies.get(issue_id, [])
            )

            if has_incomplete_deps:
                blocked.append(issue_id)

        return blocked

    def topological_sort(self) -> List[str]:
        """返回拓扑排序后的 Issue ID 列表"""
        visited = set()
        temp_mark = set()
        result = []

        def visit(issue_id: str):
            if issue_id in temp_mark:
                raise ValueError(f"Circular dependency detected involving {issue_id}")
            if issue_id in visited:
                return

            temp_mark.add(issue_id)
            for dep in self.dependencies.get(issue_id, []):
                if dep in self.issues:
                    visit(dep)
            temp_mark.remove(issue_id)
            visited.add(issue_id)
            result.append(issue_id)

        for issue_id in self.issues:
            if issue_id not in visited:
                visit(issue_id)

        return result


class WorktreeManager:
    """管理 Issue 的独立 worktree"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, issue_id: str, base_branch: str = "master") -> Path:
        """为 Issue 创建新的 worktree"""
        worktree_path = self.base_path / issue_id

        if worktree_path.exists():
            print(f"Worktree for {issue_id} already exists at {worktree_path}")
            return worktree_path

        # 创建 worktree
        cmd = [
            "git", "worktree", "add",
            "-b", f"issue/{issue_id.lower()}",
            str(worktree_path),
            base_branch
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")

        print(f"Created worktree for {issue_id} at {worktree_path}")
        return worktree_path

    def remove_worktree(self, issue_id: str, force: bool = False) -> bool:
        """删除 Issue 的 worktree"""
        worktree_path = self.base_path / issue_id

        if not worktree_path.exists():
            return True

        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(worktree_path))

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 同时删除分支
        if result.returncode == 0:
            subprocess.run(
                ["git", "branch", "-D", f"issue/{issue_id.lower()}"],
                capture_output=True
            )

        return result.returncode == 0

    def list_worktrees(self) -> List[Tuple[str, Path]]:
        """列出所有管理的 worktrees"""
        result = []
        for item in self.base_path.iterdir():
            if item.is_dir():
                result.append((item.name, item))
        return result

    def cleanup_all(self, keep_active: bool = True) -> int:
        """清理所有 worktrees"""
        removed = 0
        for issue_id, path in self.list_worktrees():
            if self.remove_worktree(issue_id, force=True):
                removed += 1
        return removed


class AgentFactory:
    """创建和管理 Claude Code Agent"""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.active_agents: Dict[str, asyncio.subprocess.Process] = {}

    async def start_agent(self, issue: Issue, worktree_path: Path) -> asyncio.subprocess.Process:
        """启动一个 Claude Code Agent 来开发 Issue"""

        # 构建 Agent 提示词
        prompt = self._build_agent_prompt(issue)

        # 创建 Agent 启动脚本
        agent_script = self._create_agent_script(issue, worktree_path, prompt)

        # 启动 Agent 进程
        process = await asyncio.create_subprocess_shell(
            agent_script,
            cwd=str(worktree_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.active_agents[issue.id] = process
        issue.agent_pid = process.pid
        issue.started_at = datetime.now()

        print(f"Started agent for {issue.id} (PID: {process.pid})")
        return process

    def _build_agent_prompt(self, issue: Issue) -> str:
        """构建给 Agent 的提示词"""
        return f"""You are tasked with implementing Issue: {issue.id}

Title: {issue.title}

Please follow these steps:
1. Read the Issue YAML file at: {issue.yaml_path}
2. Read the CheckTree.md to understand the project context
3. Create a Task file in the issue's tasks/ directory
4. Implement the Issue according to the acceptance criteria
5. Run any unit tests defined in the Issue
6. Update the Issue status to "completed" when done
7. Create a summary of changes made

Remember to:
- Work within this worktree only
- Follow the project's coding standards
- Write tests as specified in the acceptance criteria
- Update the Task YAML with results

Start by reading the Issue YAML and understanding the requirements.
"""

    def _create_agent_script(self, issue: Issue, worktree_path: Path, prompt: str) -> str:
        """创建 Agent 启动脚本"""
        # 这里使用 Claude Code CLI 或 Agent SDK
        # 示例使用 claude 命令行工具
        return f'cd "{worktree_path}" && claude --dangerously-skip-permissions "{prompt.replace(chr(34), chr(92) + chr(34))}"'

    async def wait_for_agent(self, issue_id: str) -> Tuple[int, str, str]:
        """等待 Agent 完成并返回结果"""
        if issue_id not in self.active_agents:
            return -1, "", "Agent not found"

        process = self.active_agents[issue_id]
        stdout, stderr = await process.communicate()

        del self.active_agents[issue_id]

        return (
            process.returncode,
            stdout.decode('utf-8') if stdout else "",
            stderr.decode('utf-8') if stderr else ""
        )

    def get_active_count(self) -> int:
        """获取当前运行的 Agent 数量"""
        return len(self.active_agents)

    async def terminate_agent(self, issue_id: str) -> bool:
        """终止正在运行的 Agent"""
        if issue_id not in self.active_agents:
            return False

        process = self.active_agents[issue_id]
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            process.kill()

        del self.active_agents[issue_id]
        return True


class IssueLoader:
    """加载和保存 Issue 数据"""

    ISSUES_DIR = Path(".clawboss/checktree/issues")

    @classmethod
    def load_all_issues(cls) -> Dict[str, Issue]:
        """加载所有 Issue YAML 文件"""
        issues = {}

        if not cls.ISSUES_DIR.exists():
            print(f"Issues directory not found: {cls.ISSUES_DIR}")
            return issues

        for issue_dir in cls.ISSUES_DIR.iterdir():
            if not issue_dir.is_dir():
                continue

            yaml_file = issue_dir / f"{issue_dir.name}~{cls._get_slug(issue_dir)}.yaml"
            if not yaml_file.exists():
                # 尝试找到任何 yaml 文件
                yaml_files = list(issue_dir.glob("*.yaml"))
                if yaml_files:
                    yaml_file = yaml_files[0]
                else:
                    continue

            issue = cls._load_issue_yaml(yaml_file)
            if issue:
                issues[issue.id] = issue

        return issues

    @classmethod
    def _get_slug(cls, issue_dir: Path) -> str:
        """从目录名解析 slug"""
        # ISSUE-CORE-001 -> 从 yaml 文件读取 slug
        return "*"

    @classmethod
    def _load_issue_yaml(cls, path: Path) -> Optional[Issue]:
        """加载单个 Issue YAML 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                return None

            # 解析 ID
            issue_id = data.get('id', '')
            parts = issue_id.split('-')
            module = parts[1] if len(parts) > 1 else ''
            number = parts[2] if len(parts) > 2 else ''

            return Issue(
                id=issue_id,
                module=module,
                number=number,
                title=data.get('title', ''),
                slug=data.get('slug', ''),
                status=IssueStatus(data.get('status', 'pending')),
                prerequisites=data.get('prerequisites', []),
                sub_issues=data.get('sub_issues', []),
                is_parent=data.get('is_parent', False),
                yaml_path=path,
            )
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None

    @classmethod
    def save_issue(cls, issue: Issue) -> bool:
        """保存 Issue 状态到 YAML 文件"""
        try:
            with open(issue.yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            data['status'] = issue.status.value
            data['started_at'] = issue.started_at.isoformat() if issue.started_at else None
            data['completed_at'] = issue.completed_at.isoformat() if issue.completed_at else None

            with open(issue.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)

            return True
        except Exception as e:
            print(f"Error saving {issue.yaml_path}: {e}")
            return False


class Orchestrator:
    """主编排器类"""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.issues: Dict[str, Issue] = {}
        self.dependency_graph: Optional[DependencyGraph] = None
        self.worktree_manager = WorktreeManager(Path(config.worktree_base_path))
        self.agent_factory = AgentFactory(config)

    def load_issues(self):
        """加载所有 Issues"""
        print("Loading issues...")
        self.issues = IssueLoader.load_all_issues()
        print(f"Loaded {len(self.issues)} issues")

        # 解析依赖图
        self.dependency_graph = DependencyGraph(self.issues)

    def analyze(self):
        """分析依赖图并输出报告"""
        print("\n" + "=" * 60)
        print("DEPENDENCY ANALYSIS")
        print("=" * 60)

        # 统计
        status_counts = {}
        for issue in self.issues.values():
            status_counts[issue.status.value] = status_counts.get(issue.status.value, 0) + 1

        print("\nStatus Distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")

        # 可执行的 Issues
        ready = self.dependency_graph.get_ready_issues()
        print(f"\nReady to start ({len(ready)}):")
        for issue_id in ready[:10]:  # 只显示前10个
            issue = self.issues[issue_id]
            print(f"  - {issue_id}: {issue.title}")
        if len(ready) > 10:
            print(f"  ... and {len(ready) - 10} more")

        # 被阻塞的 Issues
        blocked = self.dependency_graph.get_blocked_issues()
        print(f"\nBlocked ({len(blocked)}):")
        for issue_id in blocked[:5]:
            deps = self.dependency_graph.dependencies.get(issue_id, set())
            incomplete = [d for d in deps if d in self.issues and self.issues[d].status != IssueStatus.COMPLETED]
            print(f"  - {issue_id} (waiting for: {', '.join(incomplete)})")

        # 拓扑排序
        try:
            sorted_issues = self.dependency_graph.topological_sort()
            print(f"\nTopological order (first 10):")
            for issue_id in sorted_issues[:10]:
                print(f"  {issue_id}")
        except ValueError as e:
            print(f"\nError: {e}")

    async def run_auto(self, specific_issue: Optional[str] = None):
        """自动模式运行"""
        print("\n" + "=" * 60)
        print("AUTO MODE - Starting parallel development")
        print("=" * 60)
        print(f"Max parallel agents: {self.config.max_agents}")
        print(f"Max retries: {self.config.max_retries}")
        print()

        if specific_issue:
            if specific_issue not in self.issues:
                print(f"Error: Issue {specific_issue} not found")
                return
            await self._process_single_issue(specific_issue)
        else:
            await self._process_all_issues()

    async def _process_all_issues(self):
        """处理所有 Issues"""
        completed_count = 0
        failed_count = 0

        while True:
            # 更新状态
            ready_issues = self.dependency_graph.get_ready_issues()
            pending_issues = [
                i for i in self.issues.values()
                if i.status == IssueStatus.PENDING
            ]

            if not ready_issues and self.agent_factory.get_active_count() == 0:
                print("\n" + "=" * 60)
                print("ALL ISSUES PROCESSED")
                print("=" * 60)
                print(f"Completed: {completed_count}")
                print(f"Failed: {failed_count}")
                break

            # 启动新的 Agents（如果还有空位）
            active_count = self.agent_factory.get_active_count()
            available_slots = self.config.max_agents - active_count

            for issue_id in ready_issues[:available_slots]:
                await self._start_issue(issue_id)

            # 等待任意 Agent 完成
            if self.agent_factory.get_active_count() > 0:
                result = await self._wait_for_any_agent()
                if result:
                    issue_id, returncode, stdout, stderr = result
                    if returncode == 0:
                        await self._complete_issue(issue_id)
                        completed_count += 1
                    else:
                        await self._fail_issue(issue_id, stderr)
                        failed_count += 1
            else:
                # 没有运行的 agent，等待一下
                await asyncio.sleep(1)

    async def _process_single_issue(self, issue_id: str):
        """处理单个 Issue"""
        await self._start_issue(issue_id)
        returncode, stdout, stderr = await self.agent_factory.wait_for_agent(issue_id)

        if returncode == 0:
            await self._complete_issue(issue_id)
            print(f"\n✓ Issue {issue_id} completed successfully")
        else:
            await self._fail_issue(issue_id, stderr)
            print(f"\n✗ Issue {issue_id} failed")
            print(f"Error: {stderr}")

    async def _start_issue(self, issue_id: str):
        """开始处理 Issue"""
        issue = self.issues[issue_id]
        print(f"\n▶ Starting {issue_id}: {issue.title}")

        # 创建 worktree
        try:
            worktree_path = self.worktree_manager.create_worktree(issue_id)
            issue.worktree_path = worktree_path
        except Exception as e:
            print(f"  Failed to create worktree: {e}")
            issue.status = IssueStatus.FAILED
            return

        # 更新状态
        issue.status = IssueStatus.IN_PROGRESS
        IssueLoader.save_issue(issue)

        # 启动 Agent
        try:
            await self.agent_factory.start_agent(issue, worktree_path)
        except Exception as e:
            print(f"  Failed to start agent: {e}")
            issue.status = IssueStatus.FAILED
            IssueLoader.save_issue(issue)

    async def _wait_for_any_agent(self) -> Optional[Tuple[str, int, str, str]]:
        """等待任意一个 Agent 完成"""
        if not self.agent_factory.active_agents:
            return None

        # 使用 asyncio.wait 等待任意一个完成
        tasks = [
            asyncio.create_task(self._wait_with_id(issue_id, process))
            for issue_id, process in self.agent_factory.active_agents.items()
        ]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # 取消其他等待任务
        for task in pending:
            task.cancel()

        # 返回完成的那个结果
        if done:
            return await list(done)[0]
        return None

    async def _wait_with_id(self, issue_id: str, process: asyncio.subprocess.Process):
        """等待特定进程并返回带 ID 的结果"""
        stdout, stderr = await process.communicate()
        return (
            issue_id,
            process.returncode,
            stdout.decode('utf-8') if stdout else "",
            stderr.decode('utf-8') if stderr else ""
        )

    async def _complete_issue(self, issue_id: str):
        """标记 Issue 为完成"""
        issue = self.issues[issue_id]
        issue.status = IssueStatus.COMPLETED
        issue.completed_at = datetime.now()
        IssueLoader.save_issue(issue)

        print(f"\n✓ {issue_id} completed")

        # 清理 worktree（如果配置）
        if self.config.auto_cleanup_worktree:
            self.worktree_manager.remove_worktree(issue_id)

    async def _fail_issue(self, issue_id: str, error: str):
        """标记 Issue 为失败"""
        issue = self.issues[issue_id]
        issue.retry_count += 1

        if issue.retry_count < self.config.max_retries:
            print(f"\n⚠ {issue_id} failed (attempt {issue.retry_count}), will retry")
            issue.status = IssueStatus.READY
            # 稍后重试
        else:
            print(f"\n✗ {issue_id} failed after {issue.retry_count} attempts")
            issue.status = IssueStatus.FAILED
            if not self.config.keep_on_failure:
                self.worktree_manager.remove_worktree(issue_id)

        IssueLoader.save_issue(issue)

    def status(self):
        """显示当前状态"""
        print("\n" + "=" * 60)
        print("CURRENT STATUS")
        print("=" * 60)

        # 按状态分组
        by_status = {}
        for issue in self.issues.values():
            status = issue.status.value
            by_status.setdefault(status, []).append(issue)

        for status in ['completed', 'in_progress', 'ready', 'pending', 'failed', 'blocked']:
            if status in by_status:
                issues = by_status[status]
                print(f"\n{status.upper()} ({len(issues)}):")
                for issue in issues[:5]:
                    print(f"  - {issue.id}: {issue.title}")
                if len(issues) > 5:
                    print(f"  ... and {len(issues) - 5} more")

        # Worktrees
        worktrees = self.worktree_manager.list_worktrees()
        if worktrees:
            print(f"\nActive worktrees ({len(worktrees)}):")
            for issue_id, path in worktrees[:5]:
                print(f"  - {issue_id}: {path}")

    def cleanup(self):
        """清理所有 worktrees"""
        print("Cleaning up worktrees...")
        removed = self.worktree_manager.cleanup_all()
        print(f"Removed {removed} worktrees")


async def main():
    parser = argparse.ArgumentParser(description="CheckTree Orchestrator")
    parser.add_argument(
        "command",
        choices=["run", "analyze", "status", "cleanup"],
        help="Command to execute"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "interactive"],
        default="auto",
        help="Run mode"
    )
    parser.add_argument(
        "--max-agents",
        type=int,
        default=None,
        help="Maximum parallel agents"
    )
    parser.add_argument(
        "--issue",
        type=str,
        default=None,
        help="Specific issue to run"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=".clawboss/config/orchestrator.yaml",
        help="Config file path"
    )

    args = parser.parse_args()

    # 加载配置
    config = OrchestratorConfig.from_yaml(Path(args.config))
    if args.max_agents:
        config.max_agents = args.max_agents

    # 创建编排器
    orchestrator = Orchestrator(config)
    orchestrator.load_issues()

    # 执行命令
    if args.command == "run":
        if args.mode == "auto":
            await orchestrator.run_auto(args.issue)
        else:
            print("Interactive mode not yet implemented")
    elif args.command == "analyze":
        orchestrator.analyze()
    elif args.command == "status":
        orchestrator.status()
    elif args.command == "cleanup":
        orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
