import sqlite3
import json
import time
from typing import Dict, List, Optional, Any


class Database:
    """SQLite persistence layer for experiments, rounds, triage reviews, and regression snapshots."""

    def __init__(self, db_path: str = "cyberranger.db") -> None:
        self.db_path = db_path
        self._init_tables()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_rounds INTEGER NOT NULL,
                    current_round INTEGER NOT NULL DEFAULT 0,
                    seed INTEGER,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    config_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    round_number INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    injection_point TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    transformations TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status_code INTEGER,
                    duration_ms REAL,
                    target_compromised INTEGER NOT NULL,
                    detector_outcome TEXT NOT NULL,
                    rule_fired TEXT,
                    ml_confidence REAL,
                    one_line_reason TEXT,
                    novelty_reward REAL,
                    fitness_score REAL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS triage_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    round_number INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    detector_verdict TEXT NOT NULL,
                    target_evidence TEXT,
                    human_status TEXT NOT NULL DEFAULT 'Pending',
                    reviewer_note TEXT,
                    reviewed_at REAL,
                    created_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    version_tag TEXT NOT NULL,
                    round_number INTEGER NOT NULL,
                    training_samples INTEGER NOT NULL,
                    val_accuracy REAL,
                    val_precision REAL,
                    val_recall REAL,
                    created_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regression_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    round_number INTEGER NOT NULL,
                    detector_version TEXT NOT NULL,
                    test_count INTEGER NOT NULL,
                    detection_rate REAL NOT NULL,
                    false_positive_rate REAL NOT NULL,
                    false_negative_rate REAL NOT NULL,
                    evaluated_at REAL NOT NULL
                )
            """)
            conn.commit()

    def create_experiment(self, exp_id: str, name: str, total_rounds: int, seed: Optional[int] = None, config: Optional[Dict] = None) -> None:
        now = time.time()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO experiments (id, name, status, total_rounds, current_round, seed, created_at, updated_at, config_json)
                VALUES (?, ?, 'running', ?, 0, ?, ?, ?, ?)
                """,
                (exp_id, name, total_rounds, seed, now, now, json.dumps(config or {}))
            )
            conn.commit()

    def update_experiment_status(self, exp_id: str, status: str, current_round: int) -> None:
        now = time.time()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE experiments SET status = ?, current_round = ?, updated_at = ? WHERE id = ?",
                (status, current_round, now, exp_id)
            )
            conn.commit()

    def insert_round(self, data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO rounds (
                    experiment_id, round_number, category, injection_point, strategy,
                    transformations, payload, status_code, duration_ms, target_compromised,
                    detector_outcome, rule_fired, ml_confidence, one_line_reason,
                    novelty_reward, fitness_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["experiment_id"],
                    data["round_number"],
                    data["category"],
                    data["injection_point"],
                    data["strategy"],
                    json.dumps(data.get("transformations", [])),
                    data["payload"],
                    data.get("status_code", 0),
                    data.get("duration_ms", 0.0),
                    1 if data.get("target_compromised") else 0,
                    data["detector_outcome"],
                    data.get("rule_fired"),
                    data.get("ml_confidence", 0.0),
                    data.get("one_line_reason", ""),
                    data.get("novelty_reward", 0.0),
                    data.get("fitness_score", 0.0),
                    time.time(),
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_rounds(self, exp_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM rounds WHERE experiment_id = ? ORDER BY round_number ASC",
                (exp_id,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def insert_triage_item(
        self,
        exp_id: str,
        round_number: int,
        category: str,
        payload: str,
        detector_verdict: str,
        target_evidence: str,
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO triage_reviews (
                    experiment_id, round_number, category, payload,
                    detector_verdict, target_evidence, human_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)
                """,
                (exp_id, round_number, category, payload, detector_verdict, target_evidence, time.time())
            )
            conn.commit()
            return cursor.lastrowid

    def get_triage_items(self, exp_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if exp_id:
                cursor = conn.execute(
                    "SELECT * FROM triage_reviews WHERE experiment_id = ? ORDER BY id DESC",
                    (exp_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM triage_reviews ORDER BY id DESC")
            return [dict(r) for r in cursor.fetchall()]

    def update_triage_status(self, review_id: int, status: str, note: Optional[str] = None) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE triage_reviews
                SET human_status = ?, reviewer_note = ?, reviewed_at = ?
                WHERE id = ?
                """,
                (status, note or "", time.time(), review_id)
            )
            conn.commit()

    def record_model_snapshot(self, exp_id: str, version: str, round_num: int, samples: int, metrics: Dict[str, float]) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO model_snapshots (experiment_id, version_tag, round_number, training_samples, val_accuracy, val_precision, val_recall, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exp_id,
                    version,
                    round_num,
                    samples,
                    metrics.get("val_accuracy", 1.0),
                    metrics.get("val_precision", 1.0),
                    metrics.get("val_recall", 1.0),
                    time.time(),
                )
            )
            conn.commit()

    def record_regression_result(self, exp_id: str, round_num: int, detector_version: str, test_count: int, det_rate: float, fpr: float, fnr: float) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO regression_runs (experiment_id, round_number, detector_version, test_count, detection_rate, false_positive_rate, false_negative_rate, evaluated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (exp_id, round_num, detector_version, test_count, det_rate, fpr, fnr, time.time())
            )
            conn.commit()
