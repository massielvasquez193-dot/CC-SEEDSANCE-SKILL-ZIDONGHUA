"""
SaaS License Server — Database Layer
======================================
Tables: clients, plans, devices, renewals, upgrades, sessions, logs

Full SaaS features:
  - Tiered plans (STARTER/PRO/ENTERPRISE)
  - Device binding with heartbeat
  - Renewal & upgrade tracking
  - Online device monitoring
  - Audit trail
"""

import hashlib
import secrets
import sqlite3
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).resolve().parent / "license.db"

PLANS = {
    "STARTER":  {"price_monthly": 29,   "device_limit": 1,  "video_limit": 50,   "features": ["one_click", "manual_mode"]},
    "PRO":      {"price_monthly": 99,   "device_limit": 3,  "video_limit": 500,  "features": ["one_click", "manual_mode", "batch_factory", "customer_portal"]},
    "ENTERPRISE":{"price_monthly": 299, "device_limit": 10, "video_limit": -1,   "features": ["one_click", "manual_mode", "batch_factory", "customer_portal", "settings_center", "priority_support", "white_label"]},
}

def generate_license_key() -> str:
    chars = string.ascii_uppercase + string.digits
    segs = [''.join(secrets.choice(chars) for _ in range(5)) for _ in range(4)]
    return "TKAIF-" + "-".join(segs)

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


class Database:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self):
        with get_db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS plans (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name    TEXT UNIQUE NOT NULL,
                    price   REAL NOT NULL,
                    device_limit INTEGER DEFAULT 1,
                    video_limit  INTEGER DEFAULT 50,
                    features     TEXT DEFAULT '[]',
                    is_active    INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS clients (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name    TEXT NOT NULL,
                    contact         TEXT DEFAULT '',
                    email           TEXT DEFAULT '',
                    license_key     TEXT UNIQUE NOT NULL,
                    plan_name       TEXT DEFAULT 'PRO',
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
                    last_heartbeat  TEXT DEFAULT (datetime('now')),
                    is_active       INTEGER DEFAULT 1,
                    is_online       INTEGER DEFAULT 0,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS renewals (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id       INTEGER NOT NULL,
                    old_expire      TEXT NOT NULL,
                    new_expire      TEXT NOT NULL,
                    days_added      INTEGER NOT NULL,
                    amount          REAL DEFAULT 0,
                    created_at      TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS upgrades (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id       INTEGER NOT NULL,
                    old_plan        TEXT NOT NULL,
                    new_plan        TEXT NOT NULL,
                    created_at      TEXT DEFAULT (datetime('now')),
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

                CREATE INDEX IF NOT EXISTS idx_clients_key    ON clients(license_key);
                CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);
                CREATE INDEX IF NOT EXISTS idx_devices_machine ON devices(machine_id);
                CREATE INDEX IF NOT EXISTS idx_devices_client ON devices(client_id);
                CREATE INDEX IF NOT EXISTS idx_logs_key       ON license_logs(license_key);
                CREATE INDEX IF NOT EXISTS idx_logs_time      ON license_logs(created_at);
            """)

            # Seed plans
            for name, cfg in PLANS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO plans (name, price, device_limit, video_limit, features) VALUES (?,?,?,?,?)",
                    (name, cfg["price_monthly"], cfg["device_limit"], cfg["video_limit"], str(cfg["features"])),
                )

    # ================================================================
    # Plans
    # ================================================================
    def get_plans(self) -> List[Dict]:
        with get_db() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM plans WHERE is_active=1").fetchall()]

    def get_plan(self, name: str) -> Optional[Dict]:
        with get_db() as conn:
            r = conn.execute("SELECT * FROM plans WHERE name=?", (name,)).fetchone()
        return dict(r) if r else None

    # ================================================================
    # Clients
    # ================================================================
    def register_client(self, company_name: str, contact: str = "", email: str = "",
                        plan: str = "PRO", expire_days: int = 365, device_limit: int = None,
                        notes: str = "") -> Dict:
        license_key = generate_license_key()
        plan_cfg = self.get_plan(plan) or PLANS.get(plan, PLANS["PRO"])
        dl = device_limit or plan_cfg["device_limit"]
        expire_date = (datetime.now() + timedelta(days=expire_days)).strftime("%Y-%m-%d")

        with get_db() as conn:
            c = conn.execute(
                """INSERT INTO clients (company_name, contact, email, license_key, plan_name,
                   expire_date, device_limit, notes) VALUES (?,?,?,?,?,?,?,?)""",
                (company_name, contact, email, license_key, plan, expire_date, dl, notes),
            )
            conn.execute(
                "INSERT INTO license_logs (client_id, license_key, action, result, detail) VALUES (?,?,?,?,?)",
                (c.lastrowid, license_key, "register", "success", f"{company_name} — {plan} — {expire_days}d"),
            )
        return self.get_client_by_key(license_key)

    def get_client_by_key(self, key: str) -> Optional[Dict]:
        with get_db() as conn:
            r = conn.execute("SELECT * FROM clients WHERE license_key=?", (key,)).fetchone()
        return dict(r) if r else None

    def get_client_by_id(self, cid: int) -> Optional[Dict]:
        with get_db() as conn:
            r = conn.execute("SELECT * FROM clients WHERE id=?", (cid,)).fetchone()
        return dict(r) if r else None

    def list_clients(self, status: str = None, plan: str = None, search: str = "") -> List[Dict]:
        q, params = "SELECT * FROM clients WHERE 1=1", []
        if status:
            q += " AND status=?"; params.append(status)
        if plan:
            q += " AND plan_name=?"; params.append(plan)
        if search:
            q += " AND (company_name LIKE ? OR contact LIKE ? OR email LIKE ? OR license_key LIKE ?)"
            s = f"%{search}%"; params.extend([s, s, s, s])
        q += " ORDER BY created_at DESC"
        with get_db() as conn:
            return [dict(r) for r in conn.execute(q, params).fetchall()]

    def update_client(self, cid: int, **kw) -> bool:
        allowed = {"company_name", "contact", "email", "plan_name", "expire_date",
                   "device_limit", "status", "notes"}
        updates = {k: v for k, v in kw.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.now().isoformat()
        sets = ", ".join(f"{k}=?" for k in updates)
        with get_db() as conn:
            conn.execute(f"UPDATE clients SET {sets} WHERE id=?", list(updates.values()) + [cid])
        return True

    def revoke_client(self, key: str) -> bool:
        c = self.get_client_by_key(key)
        if not c: return False
        with get_db() as conn:
            conn.execute("UPDATE clients SET status='revoked',updated_at=? WHERE license_key=?",
                         (datetime.now().isoformat(), key))
            conn.execute("INSERT INTO license_logs (client_id,license_key,action,result,detail) VALUES (?,?,?,?,?)",
                         (c["id"], key, "revoke", "success", f"Revoked {c['company_name']}"))
        return True

    def delete_client(self, cid: int) -> bool:
        with get_db() as conn:
            for t in ["devices", "renewals", "upgrades", "license_logs"]:
                conn.execute(f"DELETE FROM {t} WHERE client_id=?", (cid,))
            conn.execute("DELETE FROM clients WHERE id=?", (cid,))
        return True

    # ================================================================
    # License Validation
    # ================================================================
    def check_license(self, license_key: str, machine_id: str, ip: str = "") -> Dict:
        c = self.get_client_by_key(license_key)
        if not c:
            self._log(None, license_key, machine_id, "check", "invalid", ip, "Key not found")
            return {"valid": False, "reason": "invalid_key", "message": "授权码无效"}

        if c["status"] != "active":
            self._log(c["id"], license_key, machine_id, "check", "denied", ip, f"Status:{c['status']}")
            return {"valid": False, "reason": c["status"], "message": f"授权已{c['status']}"}

        exp = datetime.strptime(c["expire_date"], "%Y-%m-%d")
        if datetime.now() > exp:
            self._log(c["id"], license_key, machine_id, "check", "denied", ip, "Expired")
            return {"valid": False, "reason": "expired", "message": "授权已过期"}

        # Device check
        existing = self._count_active_devices(c["id"], machine_id)
        if existing > c["device_limit"]:
            self._log(c["id"], license_key, machine_id, "check", "denied", ip, f"Device limit: {existing}/{c['device_limit']}")
            return {"valid": False, "reason": "device_limit", "message": f"设备超限 ({existing}/{c['device_limit']})"}

        self._upsert_device(c["id"], machine_id, ip)
        days = (exp - datetime.now()).days
        plan_cfg = PLANS.get(c["plan_name"], PLANS["PRO"])

        self._log(c["id"], license_key, machine_id, "check", "success", ip, f"Valid — {days}d")

        return {
            "valid": True, "expire": c["expire_date"], "plan": c["plan_name"],
            "company": c["company_name"], "device_limit": c["device_limit"],
            "devices_registered": existing, "days_remaining": days,
            "features": plan_cfg["features"], "video_limit": plan_cfg["video_limit"],
        }

    # ================================================================
    # Renewals
    # ================================================================
    def renew_license(self, license_key: str, days: int, amount: float = 0) -> Dict:
        c = self.get_client_by_key(license_key)
        if not c:
            raise ValueError("License key not found")

        old = c["expire_date"]
        old_dt = max(datetime.strptime(old, "%Y-%m-%d"), datetime.now())
        new_dt = old_dt + timedelta(days=days)
        new = new_dt.strftime("%Y-%m-%d")

        with get_db() as conn:
            conn.execute("UPDATE clients SET expire_date=?,updated_at=? WHERE license_key=?",
                         (new, datetime.now().isoformat(), license_key))
            conn.execute("INSERT INTO renewals (client_id,old_expire,new_expire,days_added,amount) VALUES (?,?,?,?,?)",
                         (c["id"], old, new, days, amount))
            conn.execute("INSERT INTO license_logs (client_id,license_key,action,result,detail) VALUES (?,?,?,?,?)",
                         (c["id"], license_key, "renew", "success", f"+{days}d → {new}"))

        return self.get_client_by_key(license_key)

    def get_renewal_history(self, client_id: int) -> List[Dict]:
        with get_db() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM renewals WHERE client_id=? ORDER BY created_at DESC", (client_id,)).fetchall()]

    # ================================================================
    # Upgrades
    # ================================================================
    def upgrade_plan(self, license_key: str, new_plan: str) -> Dict:
        c = self.get_client_by_key(license_key)
        if not c:
            raise ValueError("License key not found")

        old_plan = c["plan_name"]
        plan_cfg = PLANS.get(new_plan, PLANS["PRO"])

        with get_db() as conn:
            conn.execute("UPDATE clients SET plan_name=?,device_limit=?,updated_at=? WHERE license_key=?",
                         (new_plan, plan_cfg["device_limit"], datetime.now().isoformat(), license_key))
            conn.execute("INSERT INTO upgrades (client_id,old_plan,new_plan) VALUES (?,?,?)",
                         (c["id"], old_plan, new_plan))
            conn.execute("INSERT INTO license_logs (client_id,license_key,action,result,detail) VALUES (?,?,?,?,?)",
                         (c["id"], license_key, "upgrade", "success", f"{old_plan} → {new_plan}"))

        return self.get_client_by_key(license_key)

    def get_upgrade_history(self, client_id: int) -> List[Dict]:
        with get_db() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM upgrades WHERE client_id=? ORDER BY created_at DESC", (client_id,)).fetchall()]

    # ================================================================
    # Devices
    # ================================================================
    def _count_active_devices(self, cid: int, current_machine: str) -> int:
        with get_db() as conn:
            r = conn.execute("SELECT COUNT(DISTINCT machine_id) FROM devices WHERE client_id=? AND is_active=1",
                             (cid,)).fetchone()
            count = r[0] if r else 0
            ex = conn.execute("SELECT id FROM devices WHERE client_id=? AND machine_id=? AND is_active=1",
                              (cid, current_machine)).fetchone()
            return count if ex else count + 1

    def _upsert_device(self, cid: int, machine_id: str, ip: str):
        with get_db() as conn:
            ex = conn.execute("SELECT id FROM devices WHERE client_id=? AND machine_id=?",
                              (cid, machine_id)).fetchone()
            now = datetime.now().isoformat()
            if ex:
                conn.execute("UPDATE devices SET last_seen=?,last_heartbeat=?,ip_address=?,is_active=1,is_online=1 WHERE id=?",
                             (now, now, ip, ex["id"]))
            else:
                conn.execute("INSERT INTO devices (client_id,machine_id,ip_address,first_seen,last_seen,last_heartbeat,is_online) VALUES (?,?,?,?,?,?,1)",
                             (cid, machine_id, ip, now, now, now))

    def heartbeat(self, machine_id: str) -> bool:
        """Update device heartbeat. Returns True if device is still authorized."""
        with get_db() as conn:
            r = conn.execute("SELECT d.*, c.status, c.expire_date FROM devices d JOIN clients c ON d.client_id=c.id WHERE d.machine_id=? AND d.is_active=1",
                             (machine_id,)).fetchone()
            if not r:
                return False
            if r["status"] != "active" or datetime.strptime(r["expire_date"], "%Y-%m-%d") < datetime.now():
                return False
            conn.execute("UPDATE devices SET last_heartbeat=?,is_online=1 WHERE machine_id=?",
                         (datetime.now().isoformat(), machine_id))
        return True

    def list_devices(self, client_id: int = None, online_only: bool = False) -> List[Dict]:
        q = """SELECT d.*, c.company_name, c.license_key, c.plan_name
               FROM devices d JOIN clients c ON d.client_id=c.id WHERE 1=1"""
        params = []
        if client_id:
            q += " AND d.client_id=?"; params.append(client_id)
        if online_only:
            q += " AND d.is_online=1"
        q += " ORDER BY d.last_seen DESC"
        with get_db() as conn:
            return [dict(r) for r in conn.execute(q, params).fetchall()]

    def deactivate_device(self, device_id: int) -> bool:
        with get_db() as conn:
            conn.execute("UPDATE devices SET is_active=0,is_online=0 WHERE id=?", (device_id,))
        return True

    def mark_offline_devices(self, timeout_minutes: int = 10):
        """Mark devices as offline if no heartbeat within timeout."""
        cutoff = (datetime.now() - timedelta(minutes=timeout_minutes)).isoformat()
        with get_db() as conn:
            conn.execute("UPDATE devices SET is_online=0 WHERE last_heartbeat<? AND is_online=1", (cutoff,))

    # ================================================================
    # Stats & Logs
    # ================================================================
    def _log(self, cid, key, mid, action, result, ip="", detail=""):
        with get_db() as conn:
            conn.execute("INSERT INTO license_logs (client_id,license_key,machine_id,action,result,ip_address,detail) VALUES (?,?,?,?,?,?,?)",
                         (cid, key, mid, action, result, ip, detail))

    def get_logs(self, license_key: str = None, action: str = None, limit: int = 200) -> List[Dict]:
        q, params = "SELECT * FROM license_logs WHERE 1=1", []
        if license_key:
            q += " AND license_key=?"; params.append(license_key)
        if action:
            q += " AND action=?"; params.append(action)
        q += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
        with get_db() as conn:
            return [dict(r) for r in conn.execute(q, params).fetchall()]

    def get_stats(self) -> Dict:
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM clients").fetchone()["c"]
            active = conn.execute("SELECT COUNT(*) as c FROM clients WHERE status='active'").fetchone()["c"]
            expiring = conn.execute(
                "SELECT COUNT(*) as c FROM clients WHERE status='active' AND expire_date <= date('now','+30 days')").fetchone()["c"]
            devices = conn.execute("SELECT COUNT(*) as c FROM devices WHERE is_active=1").fetchone()["c"]
            online = conn.execute("SELECT COUNT(*) as c FROM devices WHERE is_online=1").fetchone()["c"]
            checks_today = conn.execute(
                "SELECT COUNT(*) as c FROM license_logs WHERE action='check' AND date(created_at)=date('now')").fetchone()["c"]
            mrr = conn.execute("SELECT SUM(p.price) FROM clients c JOIN plans p ON c.plan_name=p.name WHERE c.status='active'").fetchone()[0] or 0

        return {"total_clients": total, "active_clients": active, "expiring_soon": expiring,
                "total_devices": devices, "online_devices": online, "checks_today": checks_today,
                "mrr": round(mrr, 2), "timestamp": datetime.now().isoformat()}

    def get_revenue_stats(self) -> Dict:
        with get_db() as conn:
            this_month = datetime.now().strftime("%Y-%m")
            new_this_month = conn.execute(
                "SELECT COUNT(*) FROM clients WHERE created_at LIKE ?", (f"{this_month}%",)).fetchone()[0]
            renewals_this_month = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount),0) FROM renewals WHERE created_at LIKE ?",
                (f"{this_month}%",)).fetchone()
        return {"new_clients_this_month": new_this_month,
                "renewals_this_month": renewals_this_month[0],
                "renewal_revenue_this_month": round(renewals_this_month[1], 2)}

    def get_expiring_clients(self, days: int = 30) -> List[Dict]:
        cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        with get_db() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM clients WHERE status='active' AND expire_date<=? ORDER BY expire_date", (cutoff,)).fetchall()]
