"""SQLite 数据访问层：建表与增删改查。

三张表：
    cases    评测用例（支持版本号）
    runs     每次评测的结果
    reviews  人工复核回流
"""

import json
import sqlite3
from datetime import datetime

from core.config import DB_PATH


def get_conn() -> sqlite3.Connection:
    """创建数据库连接。

    每次操作单独开连接，避免 Streamlit 多线程共用连接出错。
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 让查询结果可以按字段名取值
    return conn


def init_db() -> None:
    """初始化数据库表（不存在才创建）。"""
    conn = get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type       TEXT NOT NULL,
                question        TEXT NOT NULL,
                expected_answer TEXT DEFAULT '',
                contexts        TEXT DEFAULT '[]',
                expected_tools  TEXT DEFAULT '[]',
                version         INTEGER DEFAULT 1,
                status          TEXT DEFAULT 'active',
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id     INTEGER NOT NULL,
                task_type   TEXT NOT NULL,
                model       TEXT NOT NULL,
                pred_answer TEXT DEFAULT '',
                tool_calls  TEXT DEFAULT '[]',
                scores      TEXT DEFAULT '{}',
                latency     REAL DEFAULT 0,
                status      TEXT DEFAULT 'success',
                error       TEXT DEFAULT '',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id       INTEGER NOT NULL,
                reviewer     TEXT NOT NULL,
                human_scores TEXT DEFAULT '{}',
                comment      TEXT DEFAULT '',
                created_at   TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    """当前时间字符串。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==================== 用例 ====================

def add_case(task_type: str, question: str, expected_answer: str = "",
             contexts: list[str] | None = None,
             expected_tools: list[str] | None = None) -> int:
    """新增用例，返回用例 ID。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO cases
               (task_type, question, expected_answer, contexts, expected_tools, version, status, created_at)
               VALUES (?, ?, ?, ?, ?, 1, 'active', ?)""",
            (
                task_type,
                question,
                expected_answer,
                json.dumps(contexts or [], ensure_ascii=False),
                json.dumps(expected_tools or [], ensure_ascii=False),
                _now(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_cases(task_type: str | None = None, status: str | None = "active") -> list[dict]:
    """查询用例列表，可按类型和状态过滤。"""
    conn = get_conn()
    try:
        sql = "SELECT * FROM cases WHERE 1=1"
        params: list = []
        if task_type:
            sql += " AND task_type = ?"
            params.append(task_type)
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY id DESC"

        rows = conn.execute(sql, params).fetchall()
        return [_row_to_case(r) for r in rows]
    finally:
        conn.close()


def get_case(case_id: int) -> dict | None:
    """按 ID 查询单条用例。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        return _row_to_case(row) if row else None
    finally:
        conn.close()


def update_case(case_id: int, **fields) -> bool:
    """更新用例。

    如果传了 version_up=True，就把版本号加一，用于版本管理。
    """
    version_up = fields.pop("version_up", False)

    allowed = {"task_type", "question", "expected_answer", "contexts",
               "expected_tools", "status"}
    updates = {}
    for key, value in fields.items():
        if key not in allowed:
            continue
        # 列表字段转 JSON 存储
        if key in ("contexts", "expected_tools") and isinstance(value, list):
            value = json.dumps(value, ensure_ascii=False)
        updates[key] = value

    if not updates and not version_up:
        return False

    conn = get_conn()
    try:
        sets = [f"{k} = ?" for k in updates]
        params = list(updates.values())

        if version_up:
            sets.append("version = version + 1")

        params.append(case_id)
        conn.execute(f"UPDATE cases SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        return True
    finally:
        conn.close()


def delete_case(case_id: int) -> bool:
    """软删除用例：把状态改为 deleted（保留历史评测记录）。"""
    return update_case(case_id, status="deleted")


def _row_to_case(row) -> dict:
    """把数据库行转成字典，并解析 JSON 字段。"""
    return {
        "id": row["id"],
        "task_type": row["task_type"],
        "question": row["question"],
        "expected_answer": row["expected_answer"],
        "contexts": json.loads(row["contexts"] or "[]"),
        "expected_tools": json.loads(row["expected_tools"] or "[]"),
        "version": row["version"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


# ==================== 评测结果 ====================

def add_run(case_id: int, task_type: str, model: str, pred_answer: str,
            tool_calls: list[str], scores: dict, latency: float,
            status: str = "success", error: str = "") -> int:
    """保存一条评测结果，返回 run ID。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO runs
               (case_id, task_type, model, pred_answer, tool_calls, scores,
                latency, status, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case_id,
                task_type,
                model,
                pred_answer,
                json.dumps(tool_calls, ensure_ascii=False),
                json.dumps(scores, ensure_ascii=False),
                latency,
                status,
                error,
                _now(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_runs(task_type: str | None = None, limit: int = 200) -> list[dict]:
    """查询评测结果，按时间倒序。"""
    conn = get_conn()
    try:
        sql = "SELECT * FROM runs WHERE 1=1"
        params: list = []
        if task_type:
            sql += " AND task_type = ?"
            params.append(task_type)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [_row_to_run(r) for r in rows]
    finally:
        conn.close()


def get_run(run_id: int) -> dict | None:
    """按 ID 查询单条评测结果。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return _row_to_run(row) if row else None
    finally:
        conn.close()


def _row_to_run(row) -> dict:
    """把 runs 行转成字典。"""
    return {
        "id": row["id"],
        "case_id": row["case_id"],
        "task_type": row["task_type"],
        "model": row["model"],
        "pred_answer": row["pred_answer"],
        "tool_calls": json.loads(row["tool_calls"] or "[]"),
        "scores": json.loads(row["scores"] or "{}"),
        "latency": row["latency"],
        "status": row["status"],
        "error": row["error"],
        "created_at": row["created_at"],
    }


# ==================== 人工复核 ====================

def add_review(run_id: int, reviewer: str, human_scores: dict, comment: str = "") -> int:
    """保存人工复核结果，返回 review ID。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO reviews (run_id, reviewer, human_scores, comment, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                run_id,
                reviewer,
                json.dumps(human_scores, ensure_ascii=False),
                comment,
                _now(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_reviews(run_id: int | None = None, limit: int = 200) -> list[dict]:
    """查询复核记录。"""
    conn = get_conn()
    try:
        sql = "SELECT * FROM reviews WHERE 1=1"
        params: list = []
        if run_id:
            sql += " AND run_id = ?"
            params.append(run_id)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [
            {
                "id": r["id"],
                "run_id": r["run_id"],
                "reviewer": r["reviewer"],
                "human_scores": json.loads(r["human_scores"] or "{}"),
                "comment": r["comment"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_stats() -> dict:
    """统计概览：用例数、评测数、平均分。"""
    conn = get_conn()
    try:
        case_count = conn.execute(
            "SELECT COUNT(*) AS c FROM cases WHERE status = 'active'"
        ).fetchone()["c"]

        run_count = conn.execute("SELECT COUNT(*) AS c FROM runs").fetchone()["c"]

        review_count = conn.execute("SELECT COUNT(*) AS c FROM reviews").fetchone()["c"]

        return {
            "cases": case_count,
            "runs": run_count,
            "reviews": review_count,
        }
    finally:
        conn.close()
