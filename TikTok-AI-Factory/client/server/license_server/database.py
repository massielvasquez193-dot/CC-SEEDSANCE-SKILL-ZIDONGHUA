"""
License Server — SQLite Database Layer
========================================
Tables: clients, devices, license_logs
"""

import sqlite3
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any


DB_PATH = Path(__file__).resolve().parent / "license.db"


def generate_license_key(length: int = 24) -> str:
    """Generate a random license key like: TKAIF-XXXX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    segments = []
    for i in range(4):
        segment = ''.join(secrets.choice(chars) for _ in range(5))
        segments.append(segment)
    return "TKAIF-" + "-".join(segments)


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


class Database:
    """License server database manager."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with get_db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS clients (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name    TEXT NOT NULL,
                    contact         TEXT DEFAULT '',
                    email           TEXT DEFAULT '',
                    license_key     TEXT UNIQUE NOT NULL,
                    plan            TEXT DEFAULT 'PRO',
                    expire_date     TEXT NOT NULL,
                    device_limit    INTEGER DEFAULT 1,
                    status          TEXT DEFAULT 'active',
                    notes           TEXT DEFAULT '',
                    created_at      TEXT DEFAULT (datetime('now')),
                    updated_at      TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS devices (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id       INTEGER NOT NULL,
                    machine_id      TEXT NOT NULL,
                    machine_name    TEXT DEFAULT '',
                    ip_address      TEXT DEFAULT '',
                    first_seen      TEXT DEFAULT (datetime('now')),
                    last_seen       TEXT DEFAULT (datetime('now')),
                    is_active       INTEGER DEFAULT 1,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS license_logs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id       INTEGER,
                    license_key     TEXT,
                    machine_id      TEXT,
                    action          TEXT NOT NULL,
                    result          TEXT NOT NULL,
                    ip_address      TEXT DEFAULT '',
                    detail          TEXT DEFAULT '',
                    created_at      TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_clients_key ON clients(license_key);
                CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);
                CREATE INDEX IF NOT EXISTS idx_devices_machine ON devices(machine_id);
                CREATE INDEX IF NOT EXISTS idx_logs_key ON license_logs(license_key);
                CREATE INDEX IF NOT EXISTS idx_logs_created ON license_logs(created_at);
            """)

    # ================================================================
    # Client CRUD
    # ================================================================

    def register_client(
        self,
        company_name: str,
        contact: str = "",
        email: str = "",
        plan: str = "PRO",
        expire_days: int = 365,
        device_limit: int = 1,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Register a new client and generate a license key."""
        license_key = generate_license_key()
        expire_date = (datetime.now() + timedelta(days=expire_days)).strftime("%Y-%m-%d")

        with get_db() as conn:
            cursor = conn.execute(
                """INSERT INTO clients (company_name, contact, email, license_key, plan,
                   expire_date, device_limit, status, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)""",
                (company_name, contact, email, license_key, plan, expire_date, device_limit, notes),
            )
            client_id = cursor.lastrowid

            # Log
            conn.execute(
                "INSERT INTO license_logs (client_id, license_key, action, result, detail) VALUES (?, ?, 'register', 'success', ?)",
                (client_id, license_key, f"Registered {company_name} — {plan} — {expire_days}d"),
            )

        return self.get_client_by_key(license_key)

    def get_client_by_key(self, license_key: str) -> Optional[Dict]:
        """Look up a client by license key."""
        with get_db() as conn:
            row = conn.execute("SELECT * FROM clients WHERE license_key = ?", (license_key,)).fetchone()
        return dict(row) if row else None

    def get_client_by_id(self, client_id: int) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None

    def list_clients(self, status: str = None, search: str = "") -> List[Dict]:
        """List all clients, optionally filtered."""
        query = "SELECT * FROM clients WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if search:
            query += " AND (company_name LIKE ? OR contact LIKE ? OR email LIKE ? OR license_key LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s, s])
        query += " ORDER BY created_at DESC"

        with get_db() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def update_client(self, client_id: int, **kwargs) -> bool:
        """Update client fields."""
        allowed = {"company_name", "contact", "email", "plan", "expire_date",
                   "device_limit", "status", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [client_id]

        with get_db() as conn:
            conn.execute(f"UPDATE clients SET {set_clause} WHERE id = ?", values)
        return True

    def revoke_client(self, license_key: str) -> bool:
        """Revoke a license (set status = 'revoked')."""
        client = self.get_client_by_key(license_key)
        if not client:
            return False

        with get_db() as conn:
            conn.execute("UPDATE clients SET status = 'revoked', updated_at = ? WHERE license_key = ?",
                         (datetime.now().isoformat(), license_key))
            conn.execute(
                "INSERT INTO license_logs (client_id, license_key, action, result, detail) VALUES (?, ?, 'revoke', 'success', ?)",
                (client["id"], license_key, f"Revoked license for {client['company_name']}"),
            )
        return True

    def delete_client(self, client_id: int) -> bool:
        with get_db() as conn:
            conn.execute("DELETE FROM devices WHERE client_id = ?", (client_id,))
            conn.execute("DELETE FROM license_logs WHERE client_id = ?", (client_id,))
            conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        return True

    # ================================================================
    # License Validation
    # ================================================================

    def check_license(self, license_key: str, machine_id: str, ip_address: str = "") -> Dict[str, Any]:
        """
        Validate a license and register/update the device.

        Returns:
            {"valid": True/False, "expire": "2027-01-01", "plan": "PRO", ...}
        """
        client = self.get_client_by_key(license_key)

        if not client:
            self._log(None, license_key, machine_id, "check", "invalid", ip_address, "Key not found")
            return {"valid": False, "reason": "invalid_key", "message": "授权码无效"}

        if client["status"] != "active":
            self._log(client["id"], license_key, machine_id, "check", "denied", ip_address,
                      f"Status: {client['status']}")
            return {"valid": False, "reason": client["status"], "message": f"授权已{client['status']}"}

        # Check expiry
        expire_date = datetime.strptime(client["expire_date"], "%Y-%m-%d")
        if datetime.now() > expire_date:
            self._log(client["id"], license_key, machine_id, "check", "denied", ip_address, "Expired")
            return {"valid": False, "reason": "expired", "message": "授权已过期"}

        # Check device limit
        device_count = self._count_active_devices(client["id"], machine_id)
        if device_count > client["device_limit"]:
            self._log(client["id"], license_key, machine_id, "check", "denied", ip_address,
                      f"Device limit exceeded: {device_count}/{client['device_limit']}")
            return {"valid": False, "reason": "device_limit", "message": "设备数量超限"}

        # Register/update device
        self._upsert_device(client["id"], machine_id, ip_address)

        days_remaining = (expire_date - datetime.now()).days

        self._log(client["id"], license_key, machine_id, "check", "success", ip_address,
                  f"Valid — {days_remaining}d remaining")

        return {
            "valid": True,
            "expire": client["expire_date"],
            "plan": client["plan"],
            "company": client["company_name"],
            "device_limit": client["device_limit"],
            "devices_registered": device_count,
            "days_remaining": days_remaining,
        }

    # ================================================================
    # Device Management
    # ================================================================

    def _count_active_devices(self, client_id: int, current_machine: str) -> int:
        """Count unique active devices (including current machine if new)."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT machine_id) FROM devices WHERE client_id = ? AND is_active = 1",
                (client_id,),
            ).fetchone()
            count = row[0] if row else 0
            # Also check if current machine is already registered
            existing = conn.execute(
                "SELECT id FROM devices WHERE client_id = ? AND machine_id = ? AND is_active = 1",
                (client_id, current_machine),
            ).fetchone()
            if not existing:
                count += 1  # This would be a new device
        return count

    def _upsert_device(self, client_id: int, machine_id: str, ip_address: str):
        """Register a device or update its last_seen timestamp."""
        with get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM devices WHERE client_id = ? AND machine_id = ?",
                (client_id, machine_id),
            ).fetchone()

            if existing:
                conn.execute(
                    "UPDATE devices SET last_seen = ?, ip_address = ?, is_active = 1 WHERE id = ?",
                    (datetime.now().isoformat(), ip_address, existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO devices (client_id, machine_id, machine_name, ip_address, first_seen, last_seen)
                       VALUES (?, ?, '', ?, datetime('now'), datetime('now'))""",
                    (client_id, machine_id, ip_address),
                )

    def list_devices(self, client_id: int = None) -> List[Dict]:
        query = """SELECT d.*, c.company_name, c.license_key
                   FROM devices d JOIN clients c ON d.client_id = c.id"""
        params = []
        if client_id:
            query += " WHERE d.client_id = ?"
            params.append(client_id)
        query += " ORDER BY d.last_seen DESC"

        with get_db() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def deactivate_device(self, device_id: int) -> bool:
        with get_db() as conn:
            conn.execute("UPDATE devices SET is_active = 0 WHERE id = ?", (device_id,))
        return True

    # ================================================================
    # Logs & Stats
    # ================================================================

    def _log(self, client_id, license_key, machine_id, action, result, ip="", detail=""):
        with get_db() as conn:
            conn.execute(
                """INSERT INTO license_logs (client_id, license_key, machine_id, action, result, ip_address, detail)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (client_id, license_key, machine_id, action, result, ip, detail),
            )

    def get_logs(self, license_key: str = None, limit: int = 100) -> List[Dict]:
        query = "SELECT * FROM license_logs"
        params = []
        if license_key:
            query += " WHERE license_key = ?"
            params.append(license_key)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_db() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM clients").fetchone()["c"]
            active = conn.execute("SELECT COUNT(*) as c FROM clients WHERE status = 'active'").fetchone()["c"]
            expiring = conn.execute(
                "SELECT COUNT(*) as c FROM clients WHERE status = 'active' AND expire_date <= date('now', '+30 days')"
            ).fetchone()["c"]
            total_devices = conn.execute("SELECT COUNT(*) as c FROM devices WHERE is_active = 1").fetchone()["c"]
            checks_today = conn.execute(
                "SELECT COUNT(*) as c FROM license_logs WHERE action = 'check' AND date(created_at) = date('now')"
            ).fetchone()["c"]

        return {
            "total_clients": total,
            "active_clients": active,
            "expiring_soon": expiring,
            "total_devices": total_devices,
            "checks_today": checks_today,
        }

    def get_expiring_clients(self, days: int = 30) -> List[Dict]:
        cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM clients WHERE status = 'active' AND expire_date <= ? ORDER BY expire_date ASC",
                (cutoff,),
            ).fetchall()
        return [dict(r) for r in rows]
