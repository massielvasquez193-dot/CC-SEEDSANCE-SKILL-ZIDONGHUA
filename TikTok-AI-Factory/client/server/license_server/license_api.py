"""
License Server — FastAPI REST API
===================================
POST /api/license/check     — Validate a license key
POST /api/license/register  — Register a new client
POST /api/license/revoke    — Revoke a license
GET  /api/license/stats     — Server statistics
GET  /api/license/clients   — List clients
GET  /api/health            — Health check
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

# Support both `python -m server.license_server.license_api` and direct execution
try:
    from .database import Database
except ImportError:
    from database import Database


# ================================================================
# Pydantic Models
# ================================================================

class CheckRequest(BaseModel):
    license_key: str = Field(..., min_length=8, description="License key (e.g. TKAIF-XXXX-XXXX-XXXX-XXXX)")
    machine_id: str = Field(..., min_length=4, description="Hardware machine fingerprint")

class CheckResponse(BaseModel):
    valid: bool
    expire: Optional[str] = None
    plan: Optional[str] = None
    company: Optional[str] = None
    device_limit: Optional[int] = None
    devices_registered: Optional[int] = None
    days_remaining: Optional[int] = None
    reason: Optional[str] = None
    message: Optional[str] = None

class RegisterRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    contact: str = ""
    email: str = ""
    plan: str = "PRO"
    expire_days: int = Field(default=365, ge=1, le=3650)
    device_limit: int = Field(default=1, ge=1, le=100)
    notes: str = ""

class RegisterResponse(BaseModel):
    success: bool
    license_key: Optional[str] = None
    expire_date: Optional[str] = None
    message: Optional[str] = None

class RevokeRequest(BaseModel):
    license_key: str = Field(..., min_length=8)

class RevokeResponse(BaseModel):
    success: bool
    message: str

class StatsResponse(BaseModel):
    total_clients: int
    active_clients: int
    expiring_soon: int
    total_devices: int
    checks_today: int

class ClientInfo(BaseModel):
    id: int
    company_name: str
    contact: str
    email: str
    license_key: str
    plan: str
    expire_date: str
    device_limit: int
    status: str
    created_at: str


# ================================================================
# App Factory
# ================================================================

API_KEY = os.getenv("LICENSE_SERVER_API_KEY", "admin-secret-key-change-me")


def create_app() -> FastAPI:
    app = FastAPI(
        title="TikTok AI Factory Pro — License Server",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db = Database()

    # ---- Auth dependency ----
    def verify_admin(request: Request):
        """Verify admin API key for management endpoints."""
        key = request.headers.get("X-API-Key", "")
        if key != API_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: invalid API key")
        return True

    # ================================================================
    # Public endpoints
    # ================================================================

    @app.get("/api/health")
    async def health():
        stats = db.get_stats()
        return {
            "status": "ok",
            "server": "TikTok AI Factory Pro — License Server",
            "version": "3.0.0",
            "clients": stats["total_clients"],
            "checks_today": stats["checks_today"],
            "timestamp": datetime.now().isoformat(),
        }

    @app.post("/api/license/check", response_model=CheckResponse)
    async def check_license(req: CheckRequest, request: Request):
        """
        Validate a license key and machine ID.

        Called by the client on every startup.
        Returns valid=True/False with plan and expiry info.
        """
        ip = request.client.host if request.client else ""
        result = db.check_license(req.license_key.strip(), req.machine_id.strip(), ip)
        return CheckResponse(**result)

    # ================================================================
    # Admin endpoints (require X-API-Key header)
    # ================================================================

    @app.post("/api/license/register", response_model=RegisterResponse)
    async def register_license(req: RegisterRequest, request: Request):
        """Register a new client and generate a license key. Requires X-API-Key."""
        verify_admin(request)

        try:
            client = db.register_client(
                company_name=req.company_name,
                contact=req.contact,
                email=req.email,
                plan=req.plan,
                expire_days=req.expire_days,
                device_limit=req.device_limit,
                notes=req.notes,
            )
            return RegisterResponse(
                success=True,
                license_key=client["license_key"],
                expire_date=client["expire_date"],
                message=f"授权已生成 · {req.company_name}",
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/license/revoke", response_model=RevokeResponse)
    async def revoke_license(req: RevokeRequest, request: Request):
        """Revoke a license. Requires X-API-Key."""
        verify_admin(request)

        ok = db.revoke_client(req.license_key.strip())
        if not ok:
            raise HTTPException(status_code=404, detail="License key not found")
        return RevokeResponse(success=True, message="授权已禁用")

    @app.get("/api/license/stats", response_model=StatsResponse)
    async def get_stats(request: Request):
        """Get server statistics. Requires X-API-Key."""
        verify_admin(request)
        return StatsResponse(**db.get_stats())

    @app.get("/api/license/clients")
    async def list_clients(
        request: Request,
        status: str = Query(None),
        search: str = Query(""),
    ):
        """List all clients. Requires X-API-Key."""
        verify_admin(request)
        clients = db.list_clients(status=status, search=search)
        return {"count": len(clients), "clients": clients}

    @app.get("/api/license/clients/{client_id}")
    async def get_client(client_id: int, request: Request):
        """Get a single client. Requires X-API-Key."""
        verify_admin(request)
        client = db.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

    @app.put("/api/license/clients/{client_id}")
    async def update_client(client_id: int, request: Request):
        """Update a client. Requires X-API-Key."""
        verify_admin(request)
        body = await request.json()
        ok = db.update_client(client_id, **body)
        if not ok:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        return {"success": True}

    @app.delete("/api/license/clients/{client_id}")
    async def delete_client(client_id: int, request: Request):
        """Delete a client and all associated data. Requires X-API-Key."""
        verify_admin(request)
        db.delete_client(client_id)
        return {"success": True}

    @app.get("/api/license/devices")
    async def list_devices(request: Request, client_id: int = Query(None)):
        """List registered devices. Requires X-API-Key."""
        verify_admin(request)
        devices = db.list_devices(client_id=client_id)
        return {"count": len(devices), "devices": devices}

    @app.post("/api/license/devices/{device_id}/deactivate")
    async def deactivate_device(device_id: int, request: Request):
        """Deactivate a device. Requires X-API-Key."""
        verify_admin(request)
        db.deactivate_device(device_id)
        return {"success": True}

    @app.get("/api/license/logs")
    async def get_logs(
        request: Request,
        license_key: str = Query(None),
        limit: int = Query(default=100, le=1000),
    ):
        """Get license check logs. Requires X-API-Key."""
        verify_admin(request)
        logs = db.get_logs(license_key=license_key, limit=limit)
        return {"count": len(logs), "logs": logs}

    @app.get("/api/license/expiring")
    async def get_expiring(request: Request, days: int = Query(default=30)):
        """Get clients expiring soon. Requires X-API-Key."""
        verify_admin(request)
        clients = db.get_expiring_clients(days=days)
        return {"count": len(clients), "clients": clients}

    # ---- Admin Dashboard HTML ----
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard():
        """Serve the admin dashboard HTML page."""
        return _admin_html()

    @app.get("/admin/", response_class=HTMLResponse)
    async def admin_dashboard_slash():
        return _admin_html()

    return app


# ================================================================
# Admin Dashboard HTML
# ================================================================

def _admin_html() -> str:
    """Embedded admin dashboard HTML."""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TikTok AI Factory Pro — License Admin</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, 'Microsoft YaHei', sans-serif; background:#0d1117; color:#c9d1d9; }
.header { background:#161b22; padding:16px 24px; border-bottom:1px solid #30363d; display:flex; align-items:center; gap:16px; }
.header h1 { font-size:18px; color:#e94560; }
.header .stat { font-size:12px; color:#8b949e; background:#21262d; padding:4px 12px; border-radius:12px; }
.container { max-width:1400px; margin:0 auto; padding:20px; }
.tabs { display:flex; gap:4px; margin-bottom:20px; }
.tab { padding:10px 24px; background:#21262d; border:none; color:#8b949e; cursor:pointer; border-radius:6px 6px 0 0; font-size:13px; font-weight:bold; }
.tab.active { background:#161b22; color:#e94560; border-bottom:3px solid #e94560; }
.panel { background:#161b22; border:1px solid #30363d; border-radius:0 8px 8px 8px; padding:20px; }
table { width:100%; border-collapse:collapse; }
th { text-align:left; padding:10px 12px; font-size:12px; color:#8b949e; border-bottom:1px solid #30363d; }
td { padding:10px 12px; font-size:13px; border-bottom:1px solid #21262d; }
tr:hover td { background:#1a1a2e; }
.badge { padding:2px 10px; border-radius:10px; font-size:11px; font-weight:bold; }
.badge-active { background:#23863622; color:#238636; }
.badge-expired { background:#da363322; color:#da3633; }
.badge-revoked { background:#8b949e22; color:#8b949e; }
.badge-expiring { background:#d2992222; color:#d29922; }
.btn { padding:8px 16px; border:none; border-radius:6px; cursor:pointer; font-size:12px; font-weight:bold; }
.btn-primary { background:#238636; color:white; }
.btn-primary:hover { background:#2ea043; }
.btn-danger { background:#da3633; color:white; }
.btn-danger:hover { background:#f85149; }
.btn-outline { background:transparent; border:1px solid #30363d; color:#8b949e; }
.btn-outline:hover { background:#21262d; }
input,select { background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:8px 12px; color:#c9d1d9; font-size:13px; }
input:focus,select:focus { border-color:#58a6ff; outline:none; }
.modal { display:none; position:fixed; top:0;left:0;right:0;bottom:0; background:#000000aa; z-index:100; align-items:center;justify-content:center; }
.modal.show { display:flex; }
.modal-content { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:24px; max-width:480px; width:90%; }
.form-group { margin-bottom:12px; }
.form-group label { display:block; font-size:12px; color:#8b949e; margin-bottom:4px; }
.toast { position:fixed; top:20px; right:20px; padding:12px 20px; border-radius:8px; z-index:200; font-size:13px; display:none; }
.toast.success { background:#238636; color:white; }
.toast.error { background:#da3633; color:white; }
.grid-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:20px; }
.card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; text-align:center; }
.card .num { font-size:28px; font-weight:bold; }
.card .label { font-size:11px; color:#8b949e; margin-top:4px; }
</style>
</head>
<body>
<div class="header">
    <h1>TikTok AI Factory Pro</h1>
    <span style="color:#8b949e;font-size:14px;">License Server Admin</span>
    <span style="flex:1"></span>
    <span class="stat" id="statChecks">Checks today: --</span>
</div>

<div class="container">
    <div class="grid-3" id="statsGrid">
        <div class="card"><div class="num" style="color:#58a6ff" id="statTotal">--</div><div class="label">Total Clients</div></div>
        <div class="card"><div class="num" style="color:#238636" id="statActive">--</div><div class="label">Active</div></div>
        <div class="card"><div class="num" style="color:#d29922" id="statExpiring">--</div><div class="label">Expiring ≤ 30d</div></div>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="switchTab('clients')">👥 客户列表</button>
        <button class="tab" onclick="switchTab('devices')">📱 设备列表</button>
        <button class="tab" onclick="switchTab('logs')">📋 验证日志</button>
        <button class="tab" onclick="switchTab('expiring')">⚠️ 到期提醒</button>
        <span style="flex:1"></span>
        <button class="btn btn-primary" onclick="showRegister()" style="align-self:center;">+ 注册新客户</button>
    </div>

    <div class="panel">
        <div id="panel-clients">
            <input id="searchInput" placeholder="🔍 搜索客户/公司/Key..." style="width:300px;margin-bottom:12px;" oninput="loadClients()">
            <table><thead><tr>
                <th>公司</th><th>联系人</th><th>License Key</th><th>计划</th><th>到期</th><th>设备</th><th>状态</th><th>操作</th>
            </tr></thead><tbody id="clientsBody"><tr><td colspan="8" style="text-align:center;color:#484f58;">Loading...</td></tr></tbody></table>
        </div>
        <div id="panel-devices" style="display:none;">
            <table><thead><tr><th>设备ID</th><th>客户</th><th>License Key</th><th>首次连接</th><th>最近连接</th><th>操作</th></tr></thead>
            <tbody id="devicesBody"></tbody></table>
        </div>
        <div id="panel-logs" style="display:none;">
            <table><thead><tr><th>时间</th><th>License Key</th><th>设备</th><th>操作</th><th>结果</th><th>详情</th></tr></thead>
            <tbody id="logsBody"></tbody></table>
        </div>
        <div id="panel-expiring" style="display:none;">
            <table><thead><tr><th>公司</th><th>License Key</th><th>到期</th><th>剩余天数</th><th>操作</th></tr></thead>
            <tbody id="expiringBody"></tbody></table>
        </div>
    </div>
</div>

<!-- Register Modal -->
<div class="modal" id="registerModal">
<div class="modal-content">
<h3 style="margin-bottom:16px;color:#e94560;">📝 注册新客户</h3>
<div class="form-group"><label>公司名称 *</label><input id="regCompany" style="width:100%"></div>
<div class="form-group"><label>联系人</label><input id="regContact" style="width:100%"></div>
<div class="form-group"><label>邮箱</label><input id="regEmail" style="width:100%"></div>
<div style="display:flex;gap:12px;">
    <div class="form-group" style="flex:1"><label>计划</label><select id="regPlan"><option>PRO</option><option>ENTERPRISE</option><option>STARTER</option></select></div>
    <div class="form-group" style="flex:1"><label>有效期(天)</label><input id="regDays" value="365" type="number" style="width:100%"></div>
    <div class="form-group" style="flex:1"><label>设备限制</label><input id="regDevices" value="1" type="number" style="width:100%"></div>
</div>
<div class="form-group"><label>备注</label><input id="regNotes" style="width:100%"></div>
<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
    <button class="btn btn-outline" onclick="closeModal()">取消</button>
    <button class="btn btn-primary" onclick="doRegister()">注册</button>
</div></div></div>

<div class="toast" id="toast"></div>

<script>
const API = '';
const KEY = 'admin-secret-key-change-me';

async function api(path, opts={}) {
    const res = await fetch(API + path, {headers:{'X-API-Key':KEY,'Content-Type':'application/json'},...opts});
    if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.detail||res.statusText); }
    return res.json();
}

let currentTab = 'clients';

function switchTab(t) {
    currentTab = t;
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('[id^="panel-"]').forEach(el => el.style.display='none');
    document.getElementById('panel-'+t).style.display='';
    if(t==='clients') loadClients();
    if(t==='devices') loadDevices();
    if(t==='logs') loadLogs();
    if(t==='expiring') loadExpiring();
}

async function loadStats() {
    try { const s = await api('/api/license/stats');
        document.getElementById('statTotal').textContent = s.total_clients;
        document.getElementById('statActive').textContent = s.active_clients;
        document.getElementById('statExpiring').textContent = s.expiring_soon;
        document.getElementById('statChecks').textContent = 'Checks today: '+s.checks_today;
    } catch(e) { console.error(e); }
}

async function loadClients() {
    const s = document.getElementById('searchInput').value;
    const data = await api('/api/license/clients?search='+encodeURIComponent(s));
    const tbody = document.getElementById('clientsBody');
    tbody.innerHTML = data.clients.map(c => {
        const now = new Date(); const exp = new Date(c.expire_date);
        const days = Math.ceil((exp-now)/(86400000));
        let badge = 'badge-active'; let statusText = 'Active';
        if (c.status === 'revoked') { badge = 'badge-revoked'; statusText = 'Revoked'; }
        else if (days < 0) { badge = 'badge-expired'; statusText = 'Expired'; }
        else if (days <= 30) { badge = 'badge-expiring'; statusText = days+'d left'; }
        else { statusText = days+'d left'; }
        return `<tr>
            <td><b>${esc(c.company_name)}</b></td>
            <td>${esc(c.contact)}</td>
            <td><code style="font-size:11px;">${esc(c.license_key)}</code></td>
            <td>${esc(c.plan)}</td>
            <td>${c.expire_date}</td>
            <td>${c.device_limit}</td>
            <td><span class="badge ${badge}">${statusText}</span></td>
            <td>
                ${c.status==='active' ? `<button class="btn btn-danger" style="padding:4px 10px;font-size:11px;" onclick="doRevoke('${c.license_key}')">禁用</button>` : ''}
            </td></tr>`;
    }).join('');
}

async function loadDevices() {
    const data = await api('/api/license/devices');
    document.getElementById('devicesBody').innerHTML = data.devices.map(d => `<tr>
        <td><code>${esc(d.machine_id)}</code></td>
        <td>${esc(d.company_name)}</td>
        <td><code style="font-size:10px;">${esc(d.license_key)}</code></td>
        <td>${d.first_seen}</td>
        <td>${d.last_seen}</td>
        <td>${d.is_active?`<button class="btn btn-outline" style="padding:4px 10px;font-size:11px;" onclick="deactivateDevice(${d.id})">停用</button>`:'Inactive'}</td>
    </tr>`).join('');
}

async function loadLogs() {
    const data = await api('/api/license/logs?limit=200');
    document.getElementById('logsBody').innerHTML = data.logs.map(l => `<tr>
        <td style="font-size:11px;">${l.created_at}</td>
        <td><code style="font-size:10px;">${esc((l.license_key||'').substring(0,16)+'...')}</code></td>
        <td><code style="font-size:10px;">${esc((l.machine_id||'').substring(0,10))}</code></td>
        <td>${l.action}</td>
        <td style="color:${l.result==='success'?'#238636':'#da3633'}">${l.result}</td>
        <td style="font-size:11px;">${esc(l.detail||'')}</td>
    </tr>`).join('');
}

async function loadExpiring() {
    const data = await api('/api/license/expiring?days=30');
    document.getElementById('expiringBody').innerHTML = data.clients.map(c => {
        const days = Math.ceil((new Date(c.expire_date)-new Date())/(86400000));
        return `<tr>
            <td><b>${esc(c.company_name)}</b></td>
            <td><code>${esc(c.license_key)}</code></td>
            <td>${c.expire_date}</td>
            <td><span class="badge badge-expiring">${days} 天</span></td>
            <td><button class="btn btn-outline" style="padding:4px 10px;font-size:11px;" onclick="renewClient(${c.id})">续期</button></td>
        </tr>`;
    }).join('');
}

function showRegister() { document.getElementById('registerModal').classList.add('show'); }
function closeModal() { document.getElementById('registerModal').classList.remove('show'); }

async function doRegister() {
    try {
        const r = await api('/api/license/register',{method:'POST',body:JSON.stringify({
            company_name: document.getElementById('regCompany').value,
            contact: document.getElementById('regContact').value,
            email: document.getElementById('regEmail').value,
            plan: document.getElementById('regPlan').value,
            expire_days: parseInt(document.getElementById('regDays').value),
            device_limit: parseInt(document.getElementById('regDevices').value),
            notes: document.getElementById('regNotes').value,
        })});
        toast('✅ 授权已生成: '+r.license_key, 'success');
        closeModal(); loadClients(); loadStats();
        // Clear form
        ['regCompany','regContact','regEmail','regNotes'].forEach(id => document.getElementById(id).value='');
    } catch(e) { toast('❌ '+e.message, 'error'); }
}

async function doRevoke(key) {
    if (!confirm('确定禁用此授权？\\n'+key)) return;
    try { await api('/api/license/revoke',{method:'POST',body:JSON.stringify({license_key:key})}); loadClients(); loadStats(); }
    catch(e) { toast('Error: '+e.message, 'error'); }
}

async function deactivateDevice(id) {
    try { await api('/api/license/devices/'+id+'/deactivate',{method:'POST'}); loadDevices(); }
    catch(e) { toast('Error: '+e.message, 'error'); }
}

async function renewClient(id) {
    const days = prompt('续期天数:', '365');
    if (!days) return;
    try {
        const c = await api('/api/license/clients/'+id);
        const newExp = new Date(); newExp.setDate(newExp.getDate()+parseInt(days));
        await api('/api/license/clients/'+id, {method:'PUT',body:JSON.stringify({expire_date:newExp.toISOString().split('T')[0]})});
        loadClients(); loadExpiring(); loadStats();
        toast('✅ 已续期 '+days+' 天', 'success');
    } catch(e) { toast('Error: '+e.message, 'error'); }
}

function toast(msg, type) {
    const t = document.getElementById('toast');
    t.textContent = msg; t.className = 'toast '+type+' show';
    setTimeout(() => t.classList.remove('show'), 3000);
}

function esc(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

loadStats(); loadClients();
</script>
</body></html>"""


# ================================================================
# Main — run with: python -m server.license_server.license_api
# ================================================================

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8199
    print(f"""
╔══════════════════════════════════════════╗
║  TikTok AI Factory Pro — License Server  ║
╠══════════════════════════════════════════╣
║  API:  http://0.0.0.0:{port}              ║
║  Docs: http://0.0.0.0:{port}/docs         ║
║  Admin: http://0.0.0.0:{port}/admin       ║
╠══════════════════════════════════════════╣
║  API Key: {API_KEY:<28} ║
╚══════════════════════════════════════════╝
""")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
