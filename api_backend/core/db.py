from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import logging
from contextlib import contextmanager
import time

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import OperationalError, InterfaceError, ProgrammingError
except ImportError:
    psycopg2 = None
    OperationalError = Exception
    InterfaceError = Exception
    ProgrammingError = Exception

logger = logging.getLogger("db")


class Database:
    def __init__(self, min_conn: int = 2, max_conn: int = 10) -> None:
        if psycopg2 is None:
            raise ImportError("psycopg2-binary not installed. Run: pip install psycopg2-binary")
        self.dsn = (
            f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
            f"port={os.getenv('POSTGRES_PORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB', 'surveillance_db')} "
            f"user={os.getenv('POSTGRES_USER', 'surveillance_user')} "
            f"password={os.getenv('POSTGRES_PASSWORD', 'surveillance_pass_2026')} "
            f"sslmode={os.getenv('POSTGRES_SSLMODE', 'disable')} "
            f"connect_timeout={os.getenv('POSTGRES_CONNECT_TIMEOUT', '2')}"
        )
        self._conn: Optional[Any] = None
        self._last_connect_attempt: float = 0.0
        self._retry_backoff: float = 1.0
        self._connect_timeout_s: float = float(os.getenv("POSTGRES_CONNECT_TIMEOUT", "2"))

    def _connect(self, force: bool = False) -> Any:
        now = time.time()
        if self._conn is not None and not force:
            try:
                cur = self._conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
                return self._conn
            except (OperationalError, InterfaceError):
                self._conn = None
        if now - self._last_connect_attempt < self._retry_backoff and not force:
            raise OperationalError("Connection retry backoff active")
        self._last_connect_attempt = now
        try:
            self._conn = psycopg2.connect(self.dsn)
            self._conn.autocommit = False
            self._retry_backoff = 1.0
            logger.info("Database connection established")
            return self._conn
        except OperationalError as e:
            self._retry_backoff = min(self._retry_backoff * 2, 15.0)
            logger.warning(f"DB connection failed, backoff {self._retry_backoff:.1f}s: {e}")
            raise

    @contextmanager
    def cursor(self, dict_cursor: bool = True):
        conn = self._connect()
        cur_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cur_factory)
        try:
            yield cursor
            conn.commit()
        except (OperationalError, InterfaceError) as e:
            logger.warning(f"DB error during query, reconnecting: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
            self._conn = None
            raise
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"DB query error: {e}")
            raise
        finally:
            cursor.close()

    def execute_with_retry(self, sql: str, params: tuple = (), max_attempts: int = 3):
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                with self.cursor() as cur:
                    cur.execute(sql, params)
                    return cur
            except (OperationalError, InterfaceError) as e:
                last_error = e
                logger.warning(f"DB retry {attempt}/{max_attempts}: {e}")
                time.sleep(0.3 * attempt)
            except ProgrammingError as e:
                raise
        raise last_error or OperationalError("Max DB retry attempts reached")

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        cur = self.execute_with_retry(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cur = self.execute_with_retry(sql, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def ping(self, timeout_s: Optional[float] = None) -> bool:
        if psycopg2 is None:
            return False
        timeout = timeout_s if timeout_s is not None else self._connect_timeout_s
        if self._conn is not None:
            try:
                t = self._conn.get_transaction_status()  # no-op check
                cur = self._conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
                return True
            except (OperationalError, InterfaceError):
                self._conn = None
        now = time.time()
        wait_left = now - self._last_connect_attempt
        if wait_left < 0.1:  # small quick backoff for ping-only to avoid hammering
            return False
        self._last_connect_attempt = now
        try:
            quick_dsn = self.dsn
            conn = psycopg2.connect(quick_dsn)
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
            finally:
                conn.close()
            return True
        except (OperationalError, InterfaceError):
            return False
        except Exception:
            return False


db = Database()
