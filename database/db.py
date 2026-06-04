"""
database/db.py
==============
MySQL database handler for Carbon Emission Calculator.
Falls back to SQLite if MySQL is unavailable (for portable EXE).
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# Try MySQL, fall back to SQLite
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


class DatabaseManager:
    """Handles all database operations with MySQL primary / SQLite fallback."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.use_mysql = self.config.get("use_mysql", False) and MYSQL_AVAILABLE
        self._sqlite_path = self.config.get(
            "sqlite_path",
            os.path.join(os.path.expanduser("~"), "carbon_calculator.db")
        )
        self._init_db()

    # ── CONNECTION ─────────────────────────────────────────────────────────

    def _get_mysql_connection(self):
        return mysql.connector.connect(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 3306),
            user=self.config.get("user", "root"),
            password=self.config.get("password", ""),
            database=self.config.get("database", "carbon_calculator"),
        )

    def _get_sqlite_connection(self):
        return sqlite3.connect(self._sqlite_path)

    def _init_db(self):
        """Create table if it doesn't exist."""
        create_sql = """
            CREATE TABLE IF NOT EXISTS calculations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                input_json  TEXT    NOT NULL,
                output_json TEXT    NOT NULL,
                description TEXT,
                timestamp   TEXT    NOT NULL
            )
        """
        if self.use_mysql:
            create_sql_mysql = """
                CREATE TABLE IF NOT EXISTS calculations (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    input_json  LONGTEXT NOT NULL,
                    output_json LONGTEXT NOT NULL,
                    description TEXT,
                    timestamp   DATETIME NOT NULL
                )
            """
            try:
                # Ensure database exists
                conn = mysql.connector.connect(
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 3306),
                    user=self.config.get("user", "root"),
                    password=self.config.get("password", ""),
                )
                cur = conn.cursor()
                db_name = self.config.get("database", "carbon_calculator")
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                cur.execute(f"USE `{db_name}`")
                cur.execute(create_sql_mysql)
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[DB] MySQL init failed, falling back to SQLite: {e}")
                self.use_mysql = False
                self._init_sqlite(create_sql)
        else:
            self._init_sqlite(create_sql)

    def _init_sqlite(self, create_sql: str):
        conn = self._get_sqlite_connection()
        conn.execute(create_sql)
        conn.commit() 
        try:
            conn.execute("ALTER TABLE calculations ADD COLUMN business_area TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass  # Column already exists — safe to ignore
        conn.close()
        

    # ── CRUD ───────────────────────────────────────────────────────────────

    def save_calculation(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        description: str = ""
    ) -> int:
        """Save a calculation record. Returns inserted row id."""
        input_json  = json.dumps(inputs, default=str)
        output_json = json.dumps(outputs, default=str)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.use_mysql:
            try:
                conn = self._get_mysql_connection()
                cur  = conn.cursor()
                cur.execute(
                    "INSERT INTO calculations (input_json, output_json, description, timestamp)"
                    " VALUES (%s, %s, %s, %s)",
                    (input_json, output_json, description, ts)
                )
                conn.commit()
                row_id = cur.lastrowid
                conn.close()
                return row_id
            except Exception as e:
                print(f"[DB] MySQL save failed: {e}")

        # SQLite fallback
        conn = self._get_sqlite_connection()
        cur  = conn.execute(
            "INSERT INTO calculations (input_json, output_json, description, timestamp)"
            " VALUES (?, ?, ?, ?)",
            (input_json, output_json, description, ts)
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    def get_all_calculations(self) -> List[Dict[str, Any]]:
        """Retrieve all saved calculations, newest first."""
        rows = []
        if self.use_mysql:
            try:
                conn = self._get_mysql_connection()
                cur  = conn.cursor(dictionary=True)
                cur.execute(
                    "SELECT * FROM calculations ORDER BY timestamp DESC"
                )
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    r["inputs"]  = json.loads(r.pop("input_json", "{}"))
                    r["outputs"] = json.loads(r.pop("output_json", "{}"))
                return rows
            except Exception as e:
                print(f"[DB] MySQL fetch failed: {e}")

        conn = self._get_sqlite_connection()
        conn.row_factory = sqlite3.Row
        cur  = conn.execute(
            "SELECT * FROM calculations ORDER BY timestamp DESC"
        )
        for row in cur.fetchall():
            d = dict(row)
            d["inputs"]  = json.loads(d.pop("input_json", "{}"))
            d["outputs"] = json.loads(d.pop("output_json", "{}"))
            rows.append(d)
        conn.close()
        return rows

    def delete_calculation(self, calc_id: int) -> bool:
        """Delete a calculation by id."""
        if self.use_mysql:
            try:
                conn = self._get_mysql_connection()
                cur  = conn.cursor()
                cur.execute("DELETE FROM calculations WHERE id=%s", (calc_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] MySQL delete failed: {e}")

        conn = self._get_sqlite_connection()
        conn.execute("DELETE FROM calculations WHERE id=?", (calc_id,))
        conn.commit()
        conn.close()
        return True

    def test_connection(self) -> tuple:
        """Returns (success: bool, message: str)."""
        if self.use_mysql:
            try:
                conn = self._get_mysql_connection()
                conn.close()
                return True, "MySQL connected successfully"
            except Exception as e:
                return False, f"MySQL error: {e}"
        try:
            conn = self._get_sqlite_connection()
            conn.close()
            return True, f"SQLite database at {self._sqlite_path}"
        except Exception as e:
            return False, f"SQLite error: {e}"
