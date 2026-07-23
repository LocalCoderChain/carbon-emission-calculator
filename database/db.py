"""
database/db.py — DatabaseManager + ProductManager + UserManager + ConfigManager
================================================================================
Tables:
  calculations  — existing
  products      — product templates
  users         — authenticated users (Google SSO)
  config        — admin-editable emission factors and app settings
"""

from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timedelta

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


# ═════════════════════════════════════════════════════════════════════════════
# DatabaseManager — calculations
# ═════════════════════════════════════════════════════════════════════════════

class DatabaseManager:
    def __init__(self, config: dict):
        self.config    = config
        self.use_mysql = config.get("use_mysql", False)
        self.db_path   = config.get("sqlite_path", "carbon_calculator.db")
        self._init_db()

    def _get_connection(self):
        if self.use_mysql and MYSQL_AVAILABLE:
            return mysql.connector.connect(
                host     = self.config.get("host", "localhost"),
                port     = self.config.get("port", 3306),
                database = self.config.get("database", "carbon_db"),
                user     = self.config.get("user", "root"),
                password = self.config.get("password", ""),
            )
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS calculations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                inputs      TEXT    NOT NULL,
                outputs     TEXT    NOT NULL,
                description TEXT,
                user_id     INTEGER REFERENCES users(id)
            )
        """)
        try:
            cur.execute("ALTER TABLE calculations ADD COLUMN user_id INTEGER REFERENCES users(id)")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE calculations ADD COLUMN deleted_at TEXT")
        except Exception:
            pass
        conn.commit()
        conn.close()

    def test_connection(self) -> tuple[bool, str]:
        try:
            conn = self._get_connection()
            conn.close()
            mode = "MySQL" if (self.use_mysql and MYSQL_AVAILABLE) else "SQLite"
            return True, f"{mode} OK"
        except Exception as e:
            return False, str(e)

    def save_calculation(self, inputs: dict, outputs: dict,
                         description: str = "", user_id: int | None = None) -> int:
        conn = self._get_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO calculations (timestamp, inputs, outputs, description, user_id) VALUES (?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             json.dumps(inputs), json.dumps(outputs), description, user_id),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    def get_all_calculations(self, user_id: int | None = None,
                              include_deleted: bool = False) -> list[dict]:
        conn = self._get_connection()
        cur  = conn.cursor()
        where, params = [], []
        if user_id is not None:
            where.append("user_id=?")
            params.append(user_id)
        if not include_deleted:
            where.append("deleted_at IS NULL")
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        cur.execute(
            f"SELECT id, timestamp, inputs, outputs, description, user_id, deleted_at "
            f"FROM calculations {clause} ORDER BY id DESC",
            params,
        )
        rows = cur.fetchall()
        conn.close()
        return [
            {"id": r[0], "timestamp": r[1], "inputs": json.loads(r[2]),
             "outputs": json.loads(r[3]), "description": r[4], "user_id": r[5],
             "deleted_at": r[6]}
            for r in rows
        ]

    def delete_calculation(self, record_id: int):
        """Soft delete — the row is hidden from normal views but kept for admins."""
        conn = self._get_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE calculations SET deleted_at=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), record_id),
        )
        conn.commit()
        conn.close()

    def restore_calculation(self, record_id: int):
        conn = self._get_connection()
        cur  = conn.cursor()
        cur.execute("UPDATE calculations SET deleted_at=NULL WHERE id=?", (record_id,))
        conn.commit()
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# ProductManager — product templates
# ═════════════════════════════════════════════════════════════════════════════

_PRODUCT_FIELDS = [
    "pc_name", "product_name",
    "length_mm", "width_mm", "height_mm",
    "box_choice", "fefco_type", "ply", "thickness_mm", "wood_type_box", "pallet_overrides",
    "transport_design", "product_weight_kg",
    "phys_corrugated_kg", "phys_wooden_kg", "phys_pallet_kg", "phys_plastic_kg",
    "phys_plastic_type", "phys_wood_type",
    "phys_pkg_combo", "transport_physical", "phys_product_weight_kg",
]


class ProductManager:
    def __init__(self, db_path: str = "carbon_calculator.db"):
        self.db_path = db_path
        self._init_table()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT    NOT NULL UNIQUE,
                pc_name      TEXT,
                created_at   TEXT    NOT NULL,
                updated_at   TEXT    NOT NULL,
                data         TEXT    NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_product(self, display_name: str, fields: dict) -> tuple[bool, str]:
        if not display_name.strip():
            return False, "Product name cannot be empty."
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = json.dumps({k: fields.get(k) for k in _PRODUCT_FIELDS})
        conn = self._conn()
        try:
            cur = conn.execute(
                "UPDATE products SET data=?, updated_at=?, pc_name=? WHERE name=?",
                (data, now, fields.get("pc_name", ""), display_name.strip()),
            )
            if cur.rowcount == 0:
                conn.execute(
                    "INSERT INTO products (name, pc_name, created_at, updated_at, data) VALUES (?,?,?,?,?)",
                    (display_name.strip(), fields.get("pc_name", ""), now, now, data),
                )
            conn.commit()
            return True, f"Product '{display_name}' saved."
        except Exception as e:
            return False, f"Could not save product: {e}"
        finally:
            conn.close()

    def list_products(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, name, pc_name, updated_at FROM products ORDER BY name"
        ).fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "pc_name": r[2], "updated_at": r[3]} for r in rows]

    def load_product(self, display_name: str) -> dict | None:
        conn = self._conn()
        row  = conn.execute("SELECT data FROM products WHERE name=?", (display_name,)).fetchone()
        conn.close()
        return json.loads(row[0]) if row else None

    def delete_product(self, display_name: str) -> tuple[bool, str]:
        conn = self._conn()
        cur  = conn.execute("DELETE FROM products WHERE name=?", (display_name,))
        conn.commit()
        conn.close()
        return (True, f"Product '{display_name}' deleted.") if cur.rowcount else (False, "Not found.")

    def rename_product(self, old_name: str, new_name: str) -> tuple[bool, str]:
        if not new_name.strip():
            return False, "New name cannot be empty."
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._conn()
        try:
            cur = conn.execute(
                "UPDATE products SET name=?, updated_at=? WHERE name=?",
                (new_name.strip(), now, old_name),
            )
            conn.commit()
            return (True, f"Renamed to '{new_name}'.") if cur.rowcount else (False, "Not found.")
        except Exception as e:
            return False, f"Rename failed: {e}"
        finally:
            conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# UserManager — Google SSO users (NEW)
# ═════════════════════════════════════════════════════════════════════════════

class UserManager:
    def __init__(self, db_path: str = "carbon_calculator.db"):
        self.db_path = db_path
        self._init_table()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                email        TEXT    NOT NULL UNIQUE,
                name         TEXT,
                picture      TEXT,
                role         TEXT    NOT NULL DEFAULT 'user',
                created_at   TEXT    NOT NULL,
                last_login   TEXT
            )
        """)
        conn.commit()
        conn.close()

    def upsert_user(self, email: str, name: str, picture: str,
                    admin_emails: list[str]) -> dict:
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        role = "admin" if email.lower() in [e.lower() for e in admin_emails] else "user"
        conn = self._conn()
        try:
            existing = conn.execute(
                "SELECT id, role FROM users WHERE email=?", (email,)
            ).fetchone()
            if existing:
                final_role = "admin" if role == "admin" else existing[1]
                conn.execute(
                    "UPDATE users SET name=?, picture=?, last_login=?, role=? WHERE email=?",
                    (name, picture, now, final_role, email),
                )
                user_id = existing[0]
            else:
                cur = conn.execute(
                    "INSERT INTO users (email, name, picture, role, created_at, last_login) VALUES (?,?,?,?,?,?)",
                    (email, name, picture, role, now, now),
                )
                user_id = cur.lastrowid
            conn.commit()
            row = conn.execute(
                "SELECT id, email, name, picture, role, created_at, last_login FROM users WHERE id=?",
                (user_id,)
            ).fetchone()
            return {"id": row[0], "email": row[1], "name": row[2],
                    "picture": row[3], "role": row[4],
                    "created_at": row[5], "last_login": row[6]}
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> dict | None:
        conn = self._conn()
        row  = conn.execute(
            "SELECT id, email, name, picture, role, created_at, last_login FROM users WHERE id=?",
            (user_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "email": row[1], "name": row[2],
                "picture": row[3], "role": row[4],
                "created_at": row[5], "last_login": row[6]}

    def get_all_users(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, email, name, role, created_at, last_login FROM users ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [{"id": r[0], "email": r[1], "name": r[2],
                 "role": r[3], "created_at": r[4], "last_login": r[5]} for r in rows]

    def set_role(self, email: str, role: str) -> tuple[bool, str]:
        if role not in ("user", "admin"):
            return False, "Role must be 'user' or 'admin'."
        conn = self._conn()
        cur  = conn.execute("UPDATE users SET role=? WHERE email=?", (role, email))
        conn.commit()
        conn.close()
        return (True, f"{email} is now '{role}'.") if cur.rowcount else (False, "User not found.")

    def delete_user(self, email: str) -> tuple[bool, str]:
        conn = self._conn()
        cur  = conn.execute("DELETE FROM users WHERE email=?", (email,))
        conn.commit()
        conn.close()
        return (True, f"User '{email}' deleted.") if cur.rowcount else (False, "User not found.")


# ═════════════════════════════════════════════════════════════════════════════
# SessionManager — persistent login sessions (survive refresh, admin-revocable)
# ═════════════════════════════════════════════════════════════════════════════

class SessionManager:
    def __init__(self, db_path: str = "carbon_calculator.db"):
        self.db_path = db_path
        self._init_table()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT    PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT    NOT NULL,
                last_seen  TEXT    NOT NULL,
                revoked    INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def create_session(self, user_id: int) -> str:
        import secrets
        token = secrets.token_urlsafe(32)
        now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn  = self._conn()
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, last_seen, revoked) VALUES (?,?,?,?,0)",
            (token, user_id, now, now),
        )
        conn.commit()
        conn.close()
        return token

    def touch(self, token: str):
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._conn()
        conn.execute("UPDATE sessions SET last_seen=? WHERE token=?", (now, token))
        conn.commit()
        conn.close()

    def get_session(self, token: str) -> dict | None:
        conn = self._conn()
        row  = conn.execute(
            "SELECT token, user_id, created_at, last_seen, revoked FROM sessions WHERE token=?",
            (token,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {"token": row[0], "user_id": row[1], "created_at": row[2],
                "last_seen": row[3], "revoked": bool(row[4])}

    def revoke(self, token: str):
        conn = self._conn()
        conn.execute("UPDATE sessions SET revoked=1 WHERE token=?", (token,))
        conn.commit()
        conn.close()

    def delete_session(self, token: str):
        conn = self._conn()
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
        conn.close()

    def get_active_sessions(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT s.token, s.user_id, u.email, u.name, s.created_at, s.last_seen "
            "FROM sessions s LEFT JOIN users u ON u.id = s.user_id "
            "WHERE s.revoked = 0 ORDER BY s.last_seen DESC"
        ).fetchall()
        conn.close()
        return [
            {"token": r[0], "user_id": r[1], "email": r[2] or "—", "name": r[3] or "—",
             "created_at": r[4], "last_seen": r[5]}
            for r in rows
        ]


# ═════════════════════════════════════════════════════════════════════════════
# OAuthStateManager — pending Google OAuth CSRF state tokens
# ═════════════════════════════════════════════════════════════════════════════
# A full page reload (which is exactly what Google's redirect back to the app
# is) wipes st.session_state, so the CSRF `state` value can't be trusted to
# survive there — it has to be persisted somewhere durable instead, the same
# way login sessions already are.

class OAuthStateManager:
    _TTL_MINUTES = 10

    def __init__(self, db_path: str = "carbon_calculator.db"):
        self.db_path = db_path
        self._init_table()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS oauth_states (
                state      TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def create(self, state: str):
        """Record a newly-minted state as pending, and sweep out expired ones."""
        now    = datetime.now()
        cutoff = (now - timedelta(minutes=self._TTL_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
        conn = self._conn()
        conn.execute("DELETE FROM oauth_states WHERE created_at < ?", (cutoff,))
        conn.execute(
            "INSERT OR REPLACE INTO oauth_states (state, created_at) VALUES (?, ?)",
            (state, now.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()

    def consume(self, state: str) -> bool:
        """
        One-time check: True if `state` was pending and not expired.
        Deletes the row either way so a state can never be replayed.
        """
        conn = self._conn()
        row = conn.execute(
            "SELECT created_at FROM oauth_states WHERE state=?", (state,)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM oauth_states WHERE state=?", (state,))
            conn.commit()
        conn.close()

        if not row:
            return False
        created = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - created) <= timedelta(minutes=self._TTL_MINUTES)


# ═════════════════════════════════════════════════════════════════════════════
# ConfigManager — admin-editable emission factors (NEW)
# ═════════════════════════════════════════════════════════════════════════════

_DEFAULT_CONFIG = [
    ("emission_corrugation", "0.491",  "Corrugation Emission Factor (kgCO₂/kg)"),
    ("emission_solidwood",   "0.31",   "Solidwood Emission Factor (kgCO₂/kg)"),
    ("emission_plywood",     "0.68",   "Plywood Emission Factor (kgCO₂/kg)"),
    ("emission_ldpe",        "2.792",  "LDPE Emission Factor (kgCO₂/kg)"),
    ("emission_hdpe",        "2.506",  "HDPE Emission Factor (kgCO₂/kg)"),
    ("emission_pp",          "3.576",  "PP Emission Factor (kgCO₂/kg)"),
    ("emission_lldpe",       "2.587",  "LLDPE Emission Factor (kgCO₂/kg)"),
    ("emission_ps",          "2.982",  "PS Emission Factor (kgCO₂/kg)"),
    ("transport_road",       "0.062",  "Road Transport Factor (kgCO₂/tonne·km)"),
    ("transport_rail",       "0.022",  "Rail Transport Factor (kgCO₂/tonne·km)"),
    ("transport_sea",        "0.016",  "Sea Transport Factor (kgCO₂/tonne·km)"),
    ("transport_air",        "0.61",   "Air Transport Factor (kgCO₂/tonne·km)"),
    ("ply_options",          "[3, 5, 7]", "Available Box Ply Options (JSON list)"),
    ("plastic_types",        '["LDPE","HDPE","PP","LLDPE","PS"]', "Plastic Types (JSON list)"),
    ("pallet_deck_h",        "36",     "Pallet Deck Height (mm)"),
    ("pallet_runner_l",      "125",    "Pallet Runner Length (mm)"),
    ("pallet_runner_w",      "110",    "Pallet Runner Width (mm)"),
    ("pallet_runner_h",      "90",     "Pallet Runner Height (mm)"),
    ("pallet_runner_count",  "9",      "Pallet Runner Count"),
    ("pallet_plank_w",       "90",     "Pallet Plank Width (mm)"),
    ("pallet_plank_h",       "20",     "Pallet Plank Height (mm)"),
    ("pallet_plank_count",   "3",      "Pallet Plank Count"),
    ("pallet_density",       "500",    "Pallet Wood Density (kg/m³)"),
    ("box_clearance",        "40",     "Box Clearance Added to Dims (mm)"),
]


class ConfigManager:
    def __init__(self, db_path: str = "carbon_calculator.db"):
        self.db_path = db_path
        self._init_table()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                label      TEXT,
                updated_at TEXT
            )
        """)
        for key, value, label in _DEFAULT_CONFIG:
            conn.execute(
                "INSERT OR IGNORE INTO config (key, value, label, updated_at) VALUES (?,?,?,?)",
                (key, value, label, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
        conn.commit()
        conn.close()

    def get(self, key: str, fallback=None):
        conn = self._conn()
        row  = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        conn.close()
        return row[0] if row else fallback

    def get_float(self, key: str, fallback: float = 0.0) -> float:
        try:
            return float(self.get(key))
        except (TypeError, ValueError):
            return fallback

    def get_int(self, key: str, fallback: int = 0) -> int:
        try:
            return int(self.get(key))
        except (TypeError, ValueError):
            return fallback

    def get_json(self, key: str, fallback=None):
        try:
            return json.loads(self.get(key))
        except Exception:
            return fallback

    def get_all(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT key, value, label, updated_at FROM config ORDER BY key"
        ).fetchall()
        conn.close()
        return [{"key": r[0], "value": r[1], "label": r[2], "updated_at": r[3]} for r in rows]

    def set(self, key: str, value: str) -> tuple[bool, str]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._conn()
        try:
            conn.execute("UPDATE config SET value=?, updated_at=? WHERE key=?", (str(value), now, key))
            conn.commit()
            return True, f"Config '{key}' updated."
        except Exception as e:
            return False, f"Could not update: {e}"
        finally:
            conn.close()

    def build_emission_factors(self) -> dict:
        return {
            "Corrugation": self.get_float("emission_corrugation", 0.491),
            "Solidwood":   self.get_float("emission_solidwood",   0.31),
            "Plywood":     self.get_float("emission_plywood",     0.68),
        }

    def build_plastic_factors(self) -> dict:
        types = self.get_json("plastic_types", ["LDPE","HDPE","PP","LLDPE","PS"])
        keys  = {"LDPE": "emission_ldpe", "HDPE": "emission_hdpe",
                 "PP": "emission_pp", "LLDPE": "emission_lldpe", "PS": "emission_ps"}
        return {t: self.get_float(keys.get(t, ""), 0.0) for t in types}

    def build_transport_factors(self) -> dict:
        return {
            "Road":        self.get_float("transport_road", 0.062),
            "Rail":        self.get_float("transport_rail", 0.022),
            "Sea (Ocean)": self.get_float("transport_sea",  0.016),
            "Air":         self.get_float("transport_air",  0.61),
        }
