from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import logging
import time
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import (
        OperationalError,
        InterfaceError,
        ProgrammingError,
    )
except ImportError:
    psycopg2 = None
    OperationalError = Exception
    InterfaceError = Exception
    ProgrammingError = Exception


logger = logging.getLogger("db")


class Database:

    def __init__(
        self,
        min_conn: int = 2,
        max_conn: int = 10,
    ) -> None:

        if psycopg2 is None:
            raise ImportError(
                "psycopg2-binary not installed. "
                "Run: pip install psycopg2-binary"
            )

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

        self._connect_timeout_s: float = float(
            os.getenv(
                "POSTGRES_CONNECT_TIMEOUT",
                "2",
            )
        )


    # =====================================================
    # CONNECTION
    # =====================================================

    def _connect(
        self,
        force: bool = False,
    ) -> Any:

        now = time.time()


        # Existing connection health check
        if (
            self._conn is not None
            and not force
        ):

            try:

                cur = self._conn.cursor()

                cur.execute(
                    "SELECT 1"
                )

                cur.close()

                return self._conn

            except (
                OperationalError,
                InterfaceError,
            ):

                try:
                    self._conn.close()
                except Exception:
                    pass

                self._conn = None


        # Avoid hammering PostgreSQL
        if (
            now - self._last_connect_attempt
            < self._retry_backoff
            and not force
        ):

            raise OperationalError(
                "Connection retry backoff active"
            )


        self._last_connect_attempt = now


        try:

            self._conn = psycopg2.connect(
                self.dsn
            )

            self._conn.autocommit = False

            self._retry_backoff = 1.0

            logger.info(
                "Database connection established"
            )

            return self._conn


        except OperationalError as e:

            self._retry_backoff = min(
                self._retry_backoff * 2,
                15.0,
            )

            logger.warning(
                f"DB connection failed, "
                f"backoff "
                f"{self._retry_backoff:.1f}s: "
                f"{e}"
            )

            raise


    # =====================================================
    # CURSOR CONTEXT
    # =====================================================

    @contextmanager
    def cursor(
        self,
        dict_cursor: bool = True,
    ):

        conn = self._connect()

        cur_factory = (
            psycopg2.extras.RealDictCursor
            if dict_cursor
            else None
        )

        cursor = conn.cursor(
            cursor_factory=cur_factory
        )


        try:

            yield cursor

            conn.commit()


        except (
            OperationalError,
            InterfaceError,
        ) as e:

            logger.warning(
                f"DB error during query, "
                f"reconnecting: {e}"
            )

            try:
                conn.rollback()
            except Exception:
                pass

            try:
                conn.close()
            except Exception:
                pass

            self._conn = None

            raise


        except Exception as e:

            try:
                conn.rollback()
            except Exception:
                pass

            logger.error(
                f"DB query error: {e}"
            )

            raise


        finally:

            try:
                cursor.close()
            except Exception:
                pass


    # =====================================================
    # EXECUTE
    # =====================================================

    def execute_with_retry(
        self,
        sql: str,
        params: tuple = (),
        max_attempts: int = 3,
    ) -> bool:

        last_error = None


        for attempt in range(
            1,
            max_attempts + 1,
        ):

            try:

                with self.cursor() as cur:

                    cur.execute(
                        sql,
                        params,
                    )

                return True


            except (
                OperationalError,
                InterfaceError,
            ) as e:

                last_error = e

                logger.warning(
                    f"DB execute retry "
                    f"{attempt}/"
                    f"{max_attempts}: "
                    f"{e}"
                )

                time.sleep(
                    0.3 * attempt
                )


            except ProgrammingError:

                raise


        raise (
            last_error
            or OperationalError(
                "Max DB retry attempts reached"
            )
        )


    # =====================================================
    # FETCH ONE
    # =====================================================

    def fetchone(
        self,
        sql: str,
        params: tuple = (),
        max_attempts: int = 3,
    ) -> Optional[Dict[str, Any]]:

        last_error = None


        for attempt in range(
            1,
            max_attempts + 1,
        ):

            try:

                with self.cursor() as cur:

                    cur.execute(
                        sql,
                        params,
                    )

                    row = cur.fetchone()

                    if not row:
                        return None

                    return dict(row)


            except (
                OperationalError,
                InterfaceError,
            ) as e:

                last_error = e

                logger.warning(
                    f"DB fetchone retry "
                    f"{attempt}/"
                    f"{max_attempts}: "
                    f"{e}"
                )

                time.sleep(
                    0.3 * attempt
                )


            except ProgrammingError:

                raise


        raise (
            last_error
            or OperationalError(
                "fetchone failed"
            )
        )


    # =====================================================
    # FETCH ALL
    # =====================================================

    def fetchall(
        self,
        sql: str,
        params: tuple = (),
        max_attempts: int = 3,
    ) -> List[Dict[str, Any]]:

        last_error = None


        for attempt in range(
            1,
            max_attempts + 1,
        ):

            try:

                with self.cursor() as cur:

                    cur.execute(
                        sql,
                        params,
                    )

                    rows = cur.fetchall()

                    return [
                        dict(row)
                        for row in rows
                    ]


            except (
                OperationalError,
                InterfaceError,
            ) as e:

                last_error = e

                logger.warning(
                    f"DB fetchall retry "
                    f"{attempt}/"
                    f"{max_attempts}: "
                    f"{e}"
                )

                time.sleep(
                    0.3 * attempt
                )


            except ProgrammingError:

                raise


        raise (
            last_error
            or OperationalError(
                "fetchall failed"
            )
        )


    # =====================================================
    # HEALTH CHECK
    # =====================================================

    def ping(
        self,
        timeout_s: Optional[float] = None,
    ) -> bool:

        if psycopg2 is None:
            return False


        if self._conn is not None:

            try:

                cur = self._conn.cursor()

                cur.execute(
                    "SELECT 1"
                )

                cur.close()

                return True


            except (
                OperationalError,
                InterfaceError,
            ):

                try:
                    self._conn.close()
                except Exception:
                    pass

                self._conn = None


        try:

            conn = psycopg2.connect(
                self.dsn
            )

            try:

                cur = conn.cursor()

                cur.execute(
                    "SELECT 1"
                )

                cur.close()

            finally:

                conn.close()


            return True


        except (
            OperationalError,
            InterfaceError,
        ):

            return False


        except Exception:

            return False


db = Database()