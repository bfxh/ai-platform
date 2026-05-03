#!/usr/bin/env python
"""TRAE Pipeline Engine v6.0 - 五阶段强制管道架构

设计原则:
  所有项目在执行任何开发工作之前，必须按顺序通过五个阶段。
  每个阶段完成后产生 Gate Report，作为进入下一阶段的通行证。

管道顺序 (不可跳过):
  Phase 1: Preliminary Analysis   (架构分析、依赖映射、特性识别)
  Phase 2: Security Audit         (漏洞扫描、密钥检测、依赖审计)
  Phase 3: Reverse Engineering    (许可证检测、开源验证、反编译)
  Phase 4: Deep Analysis          (交叉分析、风险重评、可行性)
  Phase 5: Development            (编码、建模、测试、部署)

Gate 机制:
  - 每阶段必须生成报告才能进入下一阶段
  - Phase 3 的许可证结果决定 Phase 5 的处理方式
  - 任何 HIGH/CRITICAL 安全发现自动阻塞 Phase 5
  - 所有报告自动存入 Brain 知识库
"""

import json
import sys
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).parent.parent  # \python\
PIPELINE_DIR = ROOT / "core" / "pipeline"
PIPELINE_DIR.mkdir(parents=True, exist_ok=True)

# 将 Brain 加入路径
BRAIN_PATH = ROOT / "storage" / "Brain"
if str(BRAIN_PATH) not in sys.path:
    sys.path.insert(0, str(BRAIN_PATH))


class Phase(Enum):
    """五阶段枚举"""

    ANALYSIS = (1, "Preliminary Analysis", "架构分析、代码结构扫描、依赖映射、特性识别")
    SECURITY = (2, "Security Audit", "漏洞扫描、密钥检测、依赖漏洞检查、配置审计")
    REVERSE = (3, "Reverse Engineering", "许可证检测、开源验证、二进制分析、反编译")
    DEEP = (4, "Deep Analysis", "交叉分析前三个阶段结果、风险重评估、可行性判断")
    DEV = (5, "Development", "编码实施、3D建模、测试验证、部署发布")

    def __init__(self, order: int, display: str, description: str):
        self.order = order
        self.display = display
        self.description = description


class GateStatus(Enum):
    PASSED = "passed"  # 通过，可进入下一阶段
    BLOCKED = "blocked"  # 阻塞，必须解决问题
    WARNING = "warning"  # 通过但有警告
    SKIPPED = "skipped"  # 跳过（如：无需反编译）
    FAILED = "failed"  # 失败，不可继续


class GateReport:
    """阶段关卡报告"""

    def __init__(
        self, phase: Phase, status: GateStatus, summary: str = "", details: dict = None, risk_level: str = "low"
    ):
        self.phase = phase
        self.status = status
        self.summary = summary
        self.details = details or {}
        self.risk_level = risk_level  # low, medium, high, critical
        self.timestamp = datetime.now().isoformat()
        self.gate_id = f"gate_{phase.name}_{int(time.time())}"

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "phase": self.phase.name,
            "phase_order": self.phase.order,
            "phase_display": self.phase.display,
            "status": self.status.value,
            "summary": self.summary,
            "details": self.details,
            "risk_level": self.risk_level,
            "timestamp": self.timestamp,
        }

    def can_proceed(self) -> bool:
        """是否可以进入下一阶段"""
        return self.status in (GateStatus.PASSED, GateStatus.WARNING, GateStatus.SKIPPED)


class Pipeline:
    """TRAE 五阶段强制管道引擎"""

    def __init__(self, project_name: str = "default", project_path: str = None, auto_integrate_brain: bool = True):
        self.project_name = project_name
        self.project_path = Path(project_path) if project_path else ROOT
        self.run_id = f"pipeline_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 阶段处理器注册
        self._phase_handlers: dict[Phase, Callable] = {}
        self._reports: dict[Phase, GateReport] = {}
        self._lock = threading.Lock()

        # Brain 集成
        self._brain = None
        if auto_integrate_brain:
            self._try_integrate_brain()

        # 注册默认处理器
        self._register_default_handlers()

        print(f"\n{'='*60}")
        print(f"  TRAE Pipeline v6.0")
        print(f"  Project: {project_name}")
        print(f"  Path: {self.project_path}")
        print(f"  Run ID: {self.run_id}")
        print(f"  Brain: {'Connected' if self._brain else 'Standalone'}")
        print(f"{'='*60}\n")

    def _try_integrate_brain(self):
        """尝试集成 Brain 系统"""
        try:
            from Brain import get_brain

            self._brain = get_brain()
        except ImportError:
            pass

    def _register_default_handlers(self):
        """注册默认阶段处理器"""
        from core.pipeline.phase_analyzer import analyze_phase
        from core.pipeline.phase_deep import deep_analyze_phase
        from core.pipeline.phase_dev import dev_phase
        from core.pipeline.phase_reverse import reverse_phase
        from core.pipeline.phase_security import audit_phase

        self.register_handler(Phase.ANALYSIS, analyze_phase)
        self.register_handler(Phase.SECURITY, audit_phase)
        self.register_handler(Phase.REVERSE, reverse_phase)
        self.register_handler(Phase.DEEP, deep_analyze_phase)
        self.register_handler(Phase.DEV, dev_phase)

    def register_handler(self, phase: Phase, handler: Callable):
        """注册自定义阶段处理器"""
        self._phase_handlers[phase] = handler

    # ─── 管道执行 ──────────────────────────────────────

    def run_phase(self, phase: Phase, force: bool = False, **kwargs) -> GateReport:
        """执行单个阶段

        Args:
            phase: 目标阶段
            force: 强制执行（忽略前置依赖）
            kwargs: 传递给处理器的额外参数
        """
        # 检查前置依赖
        if not force and phase.order > 1:
            prev_phase = self._get_prev_phase(phase)
            if prev_phase not in self._reports:
                raise RuntimeError(f"Phase {prev_phase.display} 尚未完成！" f"必须先通过 Phase {prev_phase.order}")
            prev_report = self._reports[prev_phase]
            if not prev_report.can_proceed():
                raise RuntimeError(
                    f"Phase {prev_phase.display} 未通过 (status={prev_report.status.value})！"
                    f"阻塞原因: {prev_report.summary}"
                )

        # 检查安全阻塞
        if not force and phase.order > Phase.SECURITY.order:
            sec_report = self._reports.get(Phase.SECURITY)
            if sec_report and sec_report.risk_level in ("critical",):
                raise RuntimeError(f"安全审计发现 CRITICAL 级别风险，开发已锁定！\n" f"风险摘要: {sec_report.summary}")

        handler = self._phase_handlers.get(phase)
        if not handler:
            raise RuntimeError(f"Phase {phase.display} 未注册处理器")

        print(f"\n{'─'*50}")
        print(f"[Phase {phase.order}/5] {phase.display}")
        print(f"  {phase.description}")
        print(f"{'─'*50}")

        start = time.time()

        # 传递前序报告给处理器
        prev_reports = {p.name: r.to_dict() for p, r in self._reports.items() if p.order < phase.order}

        # 执行阶段处理器
        try:
            report = handler(
                project_path=self.project_path,
                project_name=self.project_name,
                run_id=self.run_id,
                prev_reports=prev_reports,
                **kwargs,
            )

            # 确保返回的是 GateReport
            if not isinstance(report, GateReport):
                report = GateReport(
                    phase=phase,
                    status=GateStatus.PASSED,
                    summary=str(report.get("summary", "")),
                    details=report,
                    risk_level=report.get("risk_level", "low"),
                )
        except Exception as e:
            report = GateReport(
                phase=phase,
                status=GateStatus.FAILED,
                summary=f"阶段执行异常: {str(e)}",
                risk_level="high",
            )

        elapsed = time.time() - start

        # 存储报告
        with self._lock:
            self._reports[phase] = report

        # 同步到 Brain
        if self._brain:
            try:
                self._brain.learn(
                    title=f"[{self.run_id}] Phase {phase.order}: {phase.display}",
                    content=json.dumps(report.to_dict(), ensure_ascii=False),
                    category="domain_knowledge",
                    tags=["pipeline", f"phase_{phase.order}", phase.name.lower()],
                    importance=8,
                )
            except Exception:
                pass

        # 同步到 Cross-Agent Shared Context
        try:
            from core.shared_context import get_shared_context

            ctx = get_shared_context(auto_start=False)
            if ctx and ctx._started:
                ctx.broadcast_context(
                    summary=f"[Pipeline] Phase {phase.order}/5 {phase.display} on {self.project_name}: {report.status.value}",
                    key_files=[str(self.project_path)],
                    key_decisions=[
                        f"Phase {phase.order}: {report.status.value}",
                        f"Risk: {report.risk_level}",
                        f"Summary: {report.summary[:200]}",
                    ],
                )
                ctx.log_file_operation(
                    event="file_created",
                    file_path=str(ROOT / "storage" / "data" / "pipeline_reports" / f"{self.run_id}.json"),
                    operation="write",
                )
        except ImportError:
            pass
        except Exception:
            pass

        # 打印结果
        print(f"\n  Gate {phase.name}: {report.status.value.upper()}")
        print(f"  Risk: {report.risk_level}")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Summary: {report.summary[:200]}")
        if report.status == GateStatus.BLOCKED:
            print(f"\n  [BLOCKED] Cannot proceed to Phase {phase.order + 1}")
        elif report.status == GateStatus.FAILED:
            print(f"\n  [FAILED] Phase {phase.order} failed")

        return report

    def run_all(self, stop_on_block: bool = True) -> dict:
        """运行完整五阶段管道

        Args:
            stop_on_block: 遇到阻塞时是否停止
        """
        all_reports = {}
        stopped_early = False

        for phase in Phase:
            try:
                report = self.run_phase(phase)
                all_reports[phase.name] = report.to_dict()

                if not report.can_proceed() and stop_on_block:
                    stopped_early = True
                    print(f"\n[BLOCKED] Pipeline stopped at Phase {phase.order} ({phase.display})")
                    print(f"   Status: {report.status.value}")
                    break
            except RuntimeError as e:
                all_reports[phase.name] = {
                    "status": "blocked",
                    "error": str(e),
                }
                stopped_early = True
                break

        # 生成管道总报告
        pipeline_report = self._generate_pipeline_report(all_reports, stopped_early)

        # 保存报告
        report_path = ROOT / "storage" / "data" / "pipeline_reports" / f"{self.run_id}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(pipeline_report, ensure_ascii=False, indent=2), encoding="utf-8")

        return pipeline_report

    def _generate_pipeline_report(self, all_reports: dict, stopped_early: bool) -> dict:
        """生成管道总报告"""
        phases_completed = len([r for r in all_reports.values() if r.get("status") not in ("blocked",)])
        dev_allowed = False

        # 检查是否可以开发
        if Phase.DEV.name in all_reports:
            dev_report = all_reports[Phase.DEV.name]
            dev_allowed = dev_report.get("status") == "passed"
        elif Phase.REVERSE.name in all_reports:
            rev_report = all_reports[Phase.REVERSE.name]
            if rev_report.get("status") in ("passed", "skipped"):
                dev_allowed = True

        # 确定整体状态
        if stopped_early:
            overall = "stopped"
        elif phases_completed == 5:
            overall = "completed"
        else:
            overall = "partial"

        return {
            "pipeline_version": "6.0",
            "run_id": self.run_id,
            "project": self.project_name,
            "overall_status": overall,
            "phases_completed": phases_completed,
            "stopped_early": stopped_early,
            "development_allowed": dev_allowed,
            "phases": all_reports,
            "generated_at": datetime.now().isoformat(),
        }

    # ─── 查询 ──────────────────────────────────────────

    def get_report(self, phase: Phase) -> Optional[GateReport]:
        """获取某个阶段的报告"""
        return self._reports.get(phase)

    def get_all_reports(self) -> dict:
        """获取所有报告"""
        return {phase.name: report.to_dict() for phase, report in self._reports.items()}

    def current_phase(self) -> Optional[Phase]:
        """获取当前应该执行的阶段"""
        for phase in Phase:
            if phase not in self._reports:
                return phase
            if not self._reports[phase].can_proceed():
                return phase
        return None  # 全部完成

    def can_develop(self) -> bool:
        """检查是否可以开始开发"""
        for phase in Phase:
            if phase == Phase.DEV:
                break
            report = self._reports.get(phase)
            if not report or not report.can_proceed():
                return False
        sec_report = self._reports.get(Phase.SECURITY)
        if sec_report and sec_report.risk_level == "critical":
            return False
        return True

    @staticmethod
    def _get_prev_phase(phase: Phase) -> Optional[Phase]:
        """获取前一个阶段"""
        prev_order = phase.order - 1
        for p in Phase:
            if p.order == prev_order:
                return p
        return None


# ─── 便捷函数 ──────────────────────────────────────────


def quick_pipeline(project_path: str, project_name: str = None, auto_run: bool = True) -> dict:
    """快速启动管道分析"""
    if project_name is None:
        project_name = Path(project_path).name

    pipeline = Pipeline(project_name=project_name, project_path=project_path)
    if auto_run:
        return pipeline.run_all()
    return {"pipeline": pipeline, "status": "ready"}


# ─── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TRAE Pipeline v6.0")
    parser.add_argument("--project", "-p", default=".", help="项目路径")
    parser.add_argument("--name", "-n", default=None, help="项目名称")
    parser.add_argument("--phase", type=int, default=0, help="仅运行指定阶段 (1-5)")
    parser.add_argument("--force", action="store_true", help="强制执行（跳过前置检查）")

    args = parser.parse_args()

    project_path = args.project
    project_name = args.name or Path(project_path).resolve().name

    pipeline = Pipeline(project_name=project_name, project_path=project_path)

    if args.phase > 0:
        # 运行单个阶段
        target = None
        for p in Phase:
            if p.order == args.phase:
                target = p
                break
        if target:
            report = pipeline.run_phase(target, force=args.force)
            print("\n" + json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"无效阶段: {args.phase}")
    else:
        # 运行完整管道
        result = pipeline.run_all()
        print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
