#!/usr/bin/env python
"""Unified Test Database - 统一测试结果数据库

SQLite数据库管理所有测试结果，支持:
- 多框架结果聚合 (Cypress, Playwright, GameTest, K6, Pytest)
- 测试运行记录
- 测试用例历史
- Flake模式检测
- 趋势分析查询
- 统一报告生成
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).parent.parent / "storage" / "data" / "test_results.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS test_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    framework TEXT NOT NULL,           -- cypress, playwright, gametest, k6, pytest
    project_name TEXT,
    branch TEXT,
    commit_hash TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    total_tests INTEGER DEFAULT 0,
    passed INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    flaky_detected INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',     -- pending, running, passed, failed, error
    report_path TEXT,
    metadata TEXT                      -- JSON extra data
);

CREATE TABLE IF NOT EXISTS test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,             -- unique across frameworks
    framework TEXT NOT NULL,
    suite_name TEXT,
    test_name TEXT NOT NULL,
    file_path TEXT,
    tags TEXT,                         -- comma-separated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    status TEXT NOT NULL,              -- passed, failed, skipped, flaky
    duration_ms INTEGER DEFAULT 0,
    error_message TEXT,
    error_stack TEXT,
    retry_count INTEGER DEFAULT 0,
    is_flaky INTEGER DEFAULT 0,
    screenshot_path TEXT,
    video_path TEXT,
    log_output TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES test_runs(run_id)
);

CREATE TABLE IF NOT EXISTS flake_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    total_runs INTEGER DEFAULT 0,
    failures INTEGER DEFAULT 0,
    fail_rate REAL DEFAULT 0.0,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    is_confirmed_flaky INTEGER DEFAULT 0,
    suspected_cause TEXT,
    resolution TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                -- YYYY-MM-DD
    framework TEXT,
    total_runs INTEGER DEFAULT 0,
    total_tests INTEGER DEFAULT 0,
    pass_rate REAL DEFAULT 0.0,
    avg_duration_ms INTEGER DEFAULT 0,
    flake_count INTEGER DEFAULT 0,
    new_failures INTEGER DEFAULT 0,
    new_flakes INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_test_runs_started ON test_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs(status);
CREATE INDEX IF NOT EXISTS idx_test_runs_framework ON test_runs(framework);
CREATE INDEX IF NOT EXISTS idx_test_results_run ON test_results(run_id);
CREATE INDEX IF NOT EXISTS idx_test_results_case ON test_results(case_id);
CREATE INDEX IF NOT EXISTS idx_flake_case ON flake_patterns(case_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON test_metrics(date);
"""


class UnifiedTestDB:
    """统一测试数据库管理器"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    # ─── Test Runs ──────────────────────────────────────

    def create_run(
        self,
        framework: str,
        project_name: str = None,
        branch: str = None,
        commit_hash: str = None,
        metadata: dict = None,
    ) -> str:
        """创建新的测试运行"""
        import uuid

        run_id = f"{framework}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO test_runs (run_id, framework, project_name, branch,
                        commit_hash, started_at, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, 'running', ?)
                """,
                    (
                        run_id,
                        framework,
                        project_name,
                        branch,
                        commit_hash,
                        datetime.now().isoformat(),
                        json.dumps(metadata or {}),
                    ),
                )
                conn.commit()
        return run_id

    def finish_run(self, run_id: str, status: str = None, report_path: str = None):
        """标记测试运行完成"""
        with self._lock:
            with self._get_conn() as conn:
                # 重新计算统计数据
                stats = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN status='passed' THEN 1 ELSE 0 END) as passed,
                        SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) as skipped,
                        SUM(CASE WHEN is_flaky=1 THEN 1 ELSE 0 END) as flaky,
                        SUM(duration_ms) as total_ms
                    FROM test_results WHERE run_id = ?
                """,
                    (run_id,),
                ).fetchone()

                auto_status = status
                if not auto_status:
                    if stats["failed"] == 0 and stats["total"] > 0:
                        auto_status = "passed"
                    elif stats["failed"] and stats["failed"] > 0:
                        auto_status = "failed"
                    else:
                        auto_status = "passed"

                conn.execute(
                    """
                    UPDATE test_runs
                    SET finished_at = ?, status = ?,
                        total_tests = ?, passed = ?, failed = ?,
                        skipped = ?, flaky_detected = ?, duration_ms = ?,
                        report_path = COALESCE(?, report_path)
                    WHERE run_id = ?
                """,
                    (
                        datetime.now().isoformat(),
                        auto_status,
                        stats["total"] or 0,
                        stats["passed"] or 0,
                        stats["failed"] or 0,
                        stats["skipped"] or 0,
                        stats["flaky"] or 0,
                        stats["total_ms"] or 0,
                        report_path,
                        run_id,
                    ),
                )
                conn.commit()

    def get_run(self, run_id: str) -> Optional[dict]:
        """获取测试运行详情"""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM test_runs WHERE run_id = ?", (run_id,)).fetchone()
            return dict(row) if row else None

    def list_runs(self, framework: str = None, limit: int = 20, offset: int = 0) -> list:
        """列出测试运行"""
        query = "SELECT * FROM test_runs WHERE 1=1"
        params = []
        if framework:
            query += " AND framework = ?"
            params.append(framework)
        query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    # ─── Test Cases ─────────────────────────────────────

    def ensure_case(
        self, case_id: str, framework: str, suite_name: str, test_name: str, file_path: str = None, tags: list = None
    ) -> str:
        """确保测试用例存在 (upsert)"""
        with self._lock:
            with self._get_conn() as conn:
                existing = conn.execute("SELECT case_id FROM test_cases WHERE case_id = ?", (case_id,)).fetchone()
                if existing:
                    conn.execute(
                        """
                        UPDATE test_cases
                        SET framework = ?, suite_name = ?, test_name = ?,
                            file_path = ?, tags = ?
                        WHERE case_id = ?
                    """,
                        (framework, suite_name, test_name, file_path, ",".join(tags or []), case_id),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO test_cases (case_id, framework, suite_name,
                            test_name, file_path, tags)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (case_id, framework, suite_name, test_name, file_path, ",".join(tags or [])),
                    )
                conn.commit()
        return case_id

    # ─── Test Results ───────────────────────────────────

    def add_result(
        self,
        run_id: str,
        case_id: str,
        status: str,
        duration_ms: int = 0,
        error_message: str = None,
        error_stack: str = None,
        retry_count: int = 0,
        is_flaky: bool = False,
        screenshot_path: str = None,
        video_path: str = None,
        log_output: str = None,
    ):
        """添加单个测试结果"""
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO test_results (run_id, case_id, status,
                        duration_ms, error_message, error_stack,
                        retry_count, is_flaky, screenshot_path,
                        video_path, log_output)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        run_id,
                        case_id,
                        status,
                        duration_ms,
                        error_message,
                        error_stack,
                        retry_count,
                        1 if is_flaky else 0,
                        screenshot_path,
                        video_path,
                        log_output,
                    ),
                )
                conn.commit()

                # 更新flake模式表
                self._update_flake_pattern(conn, case_id, status)

    def add_results_batch(self, results: list):
        """批量添加结果 [(run_id, case_id, status, duration_ms, ...)]"""
        with self._lock:
            with self._get_conn() as conn:
                conn.executemany(
                    """
                    INSERT INTO test_results (run_id, case_id, status,
                        duration_ms, error_message, error_stack,
                        retry_count, is_flaky)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    results,
                )
                conn.commit()

    def get_results_for_run(self, run_id: str, status: str = None) -> list:
        """获取某个运行的所有结果"""
        query = "SELECT * FROM test_results WHERE run_id = ?"
        params = [run_id]
        if status:
            query += " AND status = ?"
            params.append(status)

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_case_history(self, case_id: str, limit: int = 50) -> list:
        """获取测试用例的历史结果"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT r.run_id, r.status, r.duration_ms, r.error_message,
                       r.is_flaky, r.executed_at,
                       tr.framework, tr.branch
                FROM test_results r
                JOIN test_runs tr ON r.run_id = tr.run_id
                WHERE r.case_id = ?
                ORDER BY r.executed_at DESC
                LIMIT ?
            """,
                (case_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── Flake Detection ────────────────────────────────

    def _update_flake_pattern(self, conn, case_id: str, status: str):
        """更新flake模式统计"""
        existing = conn.execute("SELECT * FROM flake_patterns WHERE case_id = ?", (case_id,)).fetchone()

        if existing:
            new_total = existing["total_runs"] + 1
            new_failures = existing["failures"] + (1 if status == "failed" else 0)
            conn.execute(
                """
                UPDATE flake_patterns
                SET total_runs = ?, failures = ?,
                    fail_rate = CASE WHEN ? > 0 THEN CAST(? AS REAL) / ? ELSE 0 END,
                    last_seen = ?,
                    is_confirmed_flaky = CASE
                        WHEN ? >= 10 AND CAST(? AS REAL) / ? BETWEEN 0.1 AND 0.9 THEN 1
                        ELSE is_confirmed_flaky
                    END,
                    updated_at = ?
                WHERE case_id = ?
            """,
                (
                    new_total,
                    new_failures,
                    new_total,
                    new_failures,
                    new_total,
                    datetime.now().isoformat(),
                    new_total,
                    new_failures,
                    new_total,
                    datetime.now().isoformat(),
                    case_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO flake_patterns (case_id, total_runs, failures,
                    fail_rate, first_seen, last_seen, is_confirmed_flaky)
                VALUES (?, 1, ?, CASE WHEN 1 > 0 THEN CAST(? AS REAL) / 1 ELSE 0 END,
                    ?, ?, 0)
            """,
                (
                    case_id,
                    1 if status == "failed" else 0,
                    1 if status == "failed" else 0,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

    def detect_flakes(self, min_runs: int = 5, fail_rate_low: float = 0.1, fail_rate_high: float = 0.9) -> list:
        """检测所有不稳定的测试 (flake tests)"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT fp.*, tc.test_name, tc.suite_name, tc.framework
                FROM flake_patterns fp
                JOIN test_cases tc ON fp.case_id = tc.case_id
                WHERE fp.total_runs >= ?
                  AND fp.fail_rate > ?
                  AND fp.fail_rate < ?
                ORDER BY fp.fail_rate DESC
            """,
                (min_runs, fail_rate_low, fail_rate_high),
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_flaky(self, case_id: str, suspected_cause: str = None, resolution: str = None):
        """标记测试为flaky"""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE flake_patterns
                SET is_confirmed_flaky = 1,
                    suspected_cause = COALESCE(?, suspected_cause),
                    resolution = COALESCE(?, resolution),
                    updated_at = ?
                WHERE case_id = ?
            """,
                (suspected_cause, resolution, datetime.now().isoformat(), case_id),
            )
            conn.commit()

    # ─── Metrics & Trends ───────────────────────────────

    def compute_daily_metrics(self, date: str = None):
        """计算某一天的指标"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        with self._lock:
            with self._get_conn() as conn:
                # 按框架计算
                for framework in ["cypress", "playwright", "gametest", "k6", "pytest"]:
                    stats = conn.execute(
                        """
                        SELECT
                            COUNT(DISTINCT tr.run_id) as total_runs,
                            COUNT(trs.id) as total_tests,
                            CASE WHEN COUNT(trs.id) > 0
                                THEN CAST(SUM(CASE WHEN trs.status='passed' THEN 1 ELSE 0 END) AS REAL) / COUNT(trs.id)
                                ELSE 0 END as pass_rate,
                            COALESCE(AVG(trs.duration_ms), 0) as avg_duration,
                            SUM(CASE WHEN trs.is_flaky=1 THEN 1 ELSE 0 END) as flake_count
                        FROM test_results trs
                        JOIN test_runs tr ON trs.run_id = tr.run_id
                        WHERE date(tr.finished_at) = ?
                          AND tr.framework = ?
                    """,
                        (date, framework),
                    ).fetchone()

                    if stats and stats["total_runs"] > 0:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO test_metrics
                                (date, framework, total_runs, total_tests,
                                 pass_rate, avg_duration_ms, flake_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                date,
                                framework,
                                stats["total_runs"],
                                stats["total_tests"],
                                stats["pass_rate"],
                                int(stats["avg_duration"]),
                                stats["flake_count"],
                            ),
                        )
                conn.commit()

    def get_trends(self, days: int = 7, framework: str = None) -> list:
        """获取测试趋势数据"""
        query = """
            SELECT date, framework,
                   SUM(total_runs) as runs,
                   SUM(total_tests) as tests,
                   AVG(pass_rate) as pass_rate,
                   AVG(avg_duration_ms) as avg_duration,
                   SUM(flake_count) as flakes
            FROM test_metrics
            WHERE date >= ?
        """
        params = [(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")]
        if framework:
            query += " AND framework = ?"
            params.append(framework)
        query += " GROUP BY date, framework ORDER BY date DESC"

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_summary(self, days: int = 7) -> dict:
        """获取测试摘要"""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        with self._get_conn() as conn:
            overall = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT tr.run_id) as total_runs,
                    COUNT(DISTINCT trs.case_id) as unique_tests,
                    SUM(CASE WHEN trs.status='passed' THEN 1 ELSE 0 END) as total_passed,
                    SUM(CASE WHEN trs.status='failed' THEN 1 ELSE 0 END) as total_failed,
                    COUNT(DISTINCT CASE WHEN trs.is_flaky=1 THEN trs.case_id END) as flaky_tests
                FROM test_results trs
                JOIN test_runs tr ON trs.run_id = tr.run_id
                WHERE date(tr.finished_at) >= ?
            """,
                (start_date,),
            ).fetchone()

            by_framework = conn.execute(
                """
                SELECT tr.framework, COUNT(DISTINCT tr.run_id) as runs,
                       COUNT(*) as results,
                       CASE WHEN COUNT(*) > 0
                           THEN CAST(SUM(CASE WHEN trs.status='passed' THEN 1 ELSE 0 END) AS REAL) / COUNT(*)
                           ELSE 0 END as pass_rate
                FROM test_results trs
                JOIN test_runs tr ON trs.run_id = tr.run_id
                WHERE date(tr.finished_at) >= ?
                GROUP BY tr.framework
            """,
                (start_date,),
            ).fetchall()

            top_flakes = conn.execute("""
                SELECT fp.case_id, tc.test_name, tc.framework,
                       fp.fail_rate, fp.total_runs
                FROM flake_patterns fp
                JOIN test_cases tc ON fp.case_id = tc.case_id
                WHERE fp.is_confirmed_flaky = 1 OR (fp.total_runs >= 5 AND fp.fail_rate > 0.1)
                ORDER BY fp.fail_rate DESC
                LIMIT 10
            """).fetchall()

            return {
                "period_days": days,
                "total_runs": overall["total_runs"] or 0,
                "unique_tests": overall["unique_tests"] or 0,
                "total_passed": overall["total_passed"] or 0,
                "total_failed": overall["total_failed"] or 0,
                "flaky_tests": overall["flaky_tests"] or 0,
                "by_framework": [dict(r) for r in by_framework],
                "top_flakes": [dict(r) for r in top_flakes],
            }

    # ─── Importers ──────────────────────────────────────

    def import_cypress_mochawesome(self, run_id: str, report_path: Path):
        """从Mochawesome JSON导入Cypress结果"""
        if not isinstance(report_path, Path):
            report_path = Path(report_path)

        # 支持单个文件或目录
        json_files = []
        if report_path.is_dir():
            json_files = list(report_path.glob("*.json"))
        elif report_path.suffix == ".json":
            json_files = [report_path]

        for jf in json_files:
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
                self._import_mochawesome_data(run_id, data, str(jf))
            except Exception as e:
                print(f"  [WARN] 导入失败 {jf}: {e}")

    def _import_mochawesome_data(self, run_id: str, data: dict, source: str):
        """递归导入Mochawesome数据"""
        results = data.get("results", [data])
        for suite in results:
            suite_name = suite.get("fullTitle", suite.get("title", "unknown"))
            for test in suite.get("suites", []) or suite.get("tests", []):
                if isinstance(test, dict) and "tests" in test:
                    # 嵌套suite
                    self._import_mochawesome_data(run_id, test, source)
                    continue

                test_name = test.get("title", test.get("fullTitle", "unknown"))
                case_id = f"cypress::{suite_name}::{test_name}"
                status = "passed" if test.get("pass", False) else "failed"
                duration = test.get("duration", 0)
                err = test.get("err", {})
                error_msg = err.get("message", "") if err else ""

                self.ensure_case(case_id, "cypress", suite_name, test_name)
                self.add_result(
                    run_id,
                    case_id,
                    status,
                    duration_ms=int(duration),
                    error_message=error_msg[:1000] if error_msg else None,
                )

    def import_playwright_json(self, run_id: str, report_path: Path):
        """从Playwright JSON报告导入"""
        if not isinstance(report_path, Path):
            report_path = Path(report_path)

        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            for suite in data.get("suites", []):
                suite_name = suite.get("title", "unknown")
                for spec in suite.get("specs", []):
                    for test in spec.get("tests", []):
                        test_name = test.get("title", "unknown")
                        case_id = f"playwright::{suite_name}::{test_name}"
                        status = test.get("status", "unknown")
                        if status == "expected":
                            status = "passed"
                        elif status == "unexpected":
                            status = "failed"

                        results_list = test.get("results", [])
                        duration = sum(r.get("duration", 0) for r in results_list)
                        error = ""
                        for r in results_list:
                            if r.get("error"):
                                error = str(r["error"])[:1000]
                                break

                        self.ensure_case(case_id, "playwright", suite_name, test_name)
                        self.add_result(
                            run_id, case_id, status, duration_ms=int(duration), error_message=error if error else None
                        )
        except Exception as e:
            print(f"  [WARN] Playwright导入失败: {e}")

    def import_gametest_json(self, run_id: str, report_path: Path):
        """从GameTest JSON报告导入"""
        if not isinstance(report_path, Path):
            report_path = Path(report_path)

        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            tests = data.get("tests", []) or data.get("results", [data])

            for test in tests:
                test_name = test.get("name", test.get("test_name", "unknown"))
                phase = test.get("phase", "unknown")
                case_id = f"gametest::{phase}::{test_name}"
                status = test.get("status", "unknown")
                duration = test.get("duration_seconds", 0) * 1000
                error = test.get("error", "")

                self.ensure_case(case_id, "gametest", phase, test_name)
                self.add_result(
                    run_id,
                    case_id,
                    status,
                    duration_ms=int(duration),
                    error_message=str(error)[:1000] if error else None,
                )
        except Exception as e:
            print(f"  [WARN] GameTest导入失败: {e}")


# ─── 全局单例 ───────────────────────────────────────────
_db_instance: Optional[UnifiedTestDB] = None


def get_test_db() -> UnifiedTestDB:
    global _db_instance
    if _db_instance is None:
        _db_instance = UnifiedTestDB()
    return _db_instance


# ─── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    db = get_test_db()
    print("=== Unified Test DB Status ===")
    summary = db.get_summary(30)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
