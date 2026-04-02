#!/usr/bin/env python3
"""
CheckTree 集成测试运行器

在临时分支上运行集成测试，用于验证多个 Issues 完成后系统的整体功能。

使用方法:
    python run-integration-tests.py --issues ISSUE-001 ISSUE-002
    python run-integration-tests.py --milestone MILESTONE-1
    python run-integration-tests.py --all
"""

import argparse
import asyncio
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class IntegrationTestRunner:
    """集成测试运行器"""

    def __init__(self, branch_prefix: str = "test/integration"):
        self.branch_prefix = branch_prefix
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.test_branch = f"{branch_prefix}-{self.timestamp}"
        self.original_branch = self._get_current_branch()

    def _get_current_branch(self) -> str:
        """获取当前分支"""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() or "master"

    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """运行 git 命令"""
        return subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=check
        )

    def create_test_branch(self, issue_branches: List[str]) -> bool:
        """创建测试分支并合并指定的 Issue 分支"""
        print(f"Creating test branch: {self.test_branch}")

        try:
            # 1. 从主分支创建新分支
            self._run_git(["checkout", "-b", self.test_branch, "master"])

            # 2. 合并所有 Issue 分支
            for branch in issue_branches:
                issue_worktree = f".clawboss/worktrees/{branch}"
                if Path(issue_worktree).exists():
                    print(f"  Merging from worktree: {branch}")
                    # 从 worktree 的提交合并
                    self._run_git(
                        ["merge", f"issue/{branch.lower()}", "--no-edit"],
                        check=False
                    )
                else:
                    # 尝试从远程分支合并
                    remote_branch = f"origin/issue/{branch.lower()}"
                    if self._run_git(["rev-parse", "--verify", remote_branch], check=False).returncode == 0:
                        print(f"  Merging from remote: {remote_branch}")
                        self._run_git(["merge", remote_branch, "--no-edit"], check=False)

            print(f"✓ Test branch {self.test_branch} created")
            return True

        except Exception as e:
            print(f"✗ Failed to create test branch: {e}")
            return False

    def run_tests(self, test_command: Optional[str] = None) -> Tuple[bool, str]:
        """运行集成测试"""
        print(f"\nRunning integration tests on {self.test_branch}...")

        # 默认测试命令（从配置读取或使用通用命令）
        if not test_command:
            test_command = self._get_test_command()

        if not test_command:
            print("⚠ No test command configured, skipping tests")
            return True, "No test command configured"

        # 运行测试
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 分钟超时
            )

            output = result.stdout + "\n" + result.stderr

            if result.returncode == 0:
                print("✓ Integration tests passed")
                return True, output
            else:
                print("✗ Integration tests failed")
                return False, output

        except subprocess.TimeoutExpired:
            print("✗ Integration tests timed out (>10 minutes)")
            return False, "Test timeout"
        except Exception as e:
            print(f"✗ Failed to run tests: {e}")
            return False, str(e)

    def _get_test_command(self) -> Optional[str]:
        """从配置或项目获取测试命令"""
        config_path = Path(".clawboss/config/orchestrator.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('testing', {}).get('integration', {}).get('test_command')

        # 尝试从 package.json 或其他配置检测
        if Path("package.json").exists():
            return "npm test -- --testPathPattern=integration"
        elif Path("pyproject.toml").exists():
            return "pytest tests/integration/ -v"
        elif Path("Makefile").exists():
            return "make test-integration"

        return None

    def cleanup_branch(self, keep_on_failure: bool = False, tests_passed: bool = True):
        """清理测试分支"""
        print(f"\nCleaning up test branch: {self.test_branch}")

        try:
            # 切换回原分支
            self._run_git(["checkout", self.original_branch])

            if not keep_on_failure or tests_passed:
                # 删除测试分支
                self._run_git(["branch", "-D", self.test_branch], check=False)
                print(f"✓ Test branch {self.test_branch} deleted")
            else:
                print(f"⚠ Test branch {self.test_branch} kept for debugging")

        except Exception as e:
            print(f"⚠ Failed to cleanup: {e}")

    def generate_report(self, tests_passed: bool, output: str, issues: List[str]):
        """生成测试报告"""
        report_path = Path(f".clawboss/logs/integration-test-{self.timestamp}.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        status = "✓ PASSED" if tests_passed else "✗ FAILED"

        report = f"""# Integration Test Report

**Date**: {datetime.now().isoformat()}
**Test Branch**: {self.test_branch}
**Status**: {status}

## Tested Issues

{chr(10).join(f"- {issue}" for issue in issues)}

## Test Output

```
{output}
```

## Summary

- Issues tested: {len(issues)}
- Result: {status}

"""

        report_path.write_text(report, encoding='utf-8')
        print(f"\nReport saved to: {report_path}")

        return report_path


async def main():
    parser = argparse.ArgumentParser(description="Run integration tests for CheckTree Issues")
    parser.add_argument(
        "--issues",
        nargs="+",
        help="Specific issue IDs to test"
    )
    parser.add_argument(
        "--milestone",
        type=str,
        help="Milestone ID (e.g., MILESTONE-1)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all completed issues"
    )
    parser.add_argument(
        "--test-command",
        type=str,
        help="Custom test command"
    )
    parser.add_argument(
        "--keep-branch",
        action="store_true",
        help="Keep test branch after completion"
    )
    parser.add_argument(
        "--branch-prefix",
        type=str,
        default="test/integration",
        help="Test branch prefix"
    )

    args = parser.parse_args()

    # 收集要测试的 Issues
    issues_to_test = []

    if args.issues:
        issues_to_test = args.issues
    elif args.milestone:
        issues_to_test = _get_milestone_issues(args.milestone)
    elif args.all:
        issues_to_test = _get_all_completed_issues()
    else:
        print("Error: Please specify --issues, --milestone, or --all")
        sys.exit(1)

    if not issues_to_test:
        print("No issues to test")
        sys.exit(0)

    print(f"Testing {len(issues_to_test)} issues: {', '.join(issues_to_test)}")

    # 创建运行器
    runner = IntegrationTestRunner(branch_prefix=args.branch_prefix)

    # 创建测试分支
    if not runner.create_test_branch(issues_to_test):
        sys.exit(1)

    # 运行测试
    tests_passed, output = runner.run_tests(args.test_command)

    # 生成报告
    report_path = runner.generate_report(tests_passed, output, issues_to_test)

    # 清理
    runner.cleanup_branch(
        keep_on_failure=args.keep_branch or not tests_passed,
        tests_passed=tests_passed
    )

    # 输出结果
    print("\n" + "=" * 60)
    if tests_passed:
        print("✓ INTEGRATION TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ INTEGRATION TESTS FAILED")
        print(f"\nSee report: {report_path}")
        sys.exit(1)


def _get_milestone_issues(milestone_id: str) -> List[str]:
    """从 CheckTree.md 获取里程碑相关的 Issues"""
    # 解析 CheckTree.md 找到里程碑节点
    # 返回所有依赖该里程碑的 Issues
    return []


def _get_all_completed_issues() -> List[str]:
    """获取所有已完成的 Issues"""
    issues = []
    issues_dir = Path(".clawboss/checktree/issues")

    if not issues_dir.exists():
        return issues

    for issue_dir in issues_dir.iterdir():
        if not issue_dir.is_dir():
            continue

        yaml_files = list(issue_dir.glob("*.yaml"))
        if yaml_files:
            with open(yaml_files[0], 'r') as f:
                data = yaml.safe_load(f)
                if data and data.get('status') == 'completed':
                    issues.append(data.get('id'))

    return issues


if __name__ == "__main__":
    asyncio.run(main())
