"""
SaaS License Server — FastAPI + Admin Dashboard
=================================================
Full SaaS REST API: check, register, renew, upgrade, revoke,
devices, heartbeat, stats, revenue.

Run: python -m server.license_server.license_api [port]
"""

import os, sys, json, secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from .database import Database, PLANS
except ImportError:
    from database import Database, PLANS

# ================================================================
# Config
# ================================================================
API_KEY = os.getenv("LICENSE_SERVER_API_KEY", "admin-secret-key-change-me")
db = Database()

# ================================================================
# Models
# ================================================================
class CheckReq(BaseModel):
    license_key: str = Field(..., min_length=8)
    machine_id: str = Field(..., min_length=4)

class RegisterReq(BaseModel):
    company_name: str; contact: str = ""; email: str = ""
    plan: str = "PRO"; expire_days: int = Field(default=365, ge=1, le=3650)
    device_limit: int = None; notes: str = ""

class RenewReq(BaseModel):
    license_key: str; days: int = Field(..., ge=1, le=3650); amount: float = 0

class UpgradeReq(BaseModel):
    license_key: str; new_plan: str

class RevokeReq(BaseModel):
    license_key: str

class HeartbeatReq(BaseModel):
    machine_id: str

# ================================================================
# App
# ================================================================
def create_app() -> FastAPI:
    app = FastAPI(title="TikTok AI Factory Pro — SaaS License Server", version="3.0.0",
                  docs_url="/docs", redoc_url="/redoc")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])

    def admin(request: Request):
        if request.headers.get("X-API-Key", "") != API_KEY:
            raise HTTPException(403, "Forbidden")

    # === Public ===
    @app.get("/api/health")
    async def health():
        s = db.get_stats()
        return {"status": "ok", "server": "SaaS License Server v3.0", "clients": s["total_clients"],
                "devices_online": s["online_devices"], "checks_today": s["checks_today"],
                "timestamp": datetime.now().isoformat()}

    @app.post("/api/license/check")
    async def check(req: CheckReq, request: Request):
        ip = request.client.host if request.client else ""
        return db.check_license(req.license_key.strip(), req.machine_id.strip(), ip)

    @app.post("/api/license/heartbeat")
    async def heartbeat(req: HeartbeatReq):
        ok = db.heartbeat(req.machine_id.strip())
        db.mark_offline_devices(10)
        return {"alive": ok}

    @app.get("/api/plans")
    async def plans():
        return {"plans": [{"name": k, **v} for k, v in PLANS.items()]}

    # === Admin: Client Management ===
    @app.post("/api/admin/register")
    async def register(req: RegisterReq, request: Request):
        admin(request)
        c = db.register_client(req.company_name, req.contact, req.email,
                               req.plan, req.expire_days, req.device_limit, req.notes)
        return {"success": True, "license_key": c["license_key"], "expire_date": c["expire_date"],
                "plan": c["plan_name"], "company": c["company_name"]}

    @app.get("/api/admin/clients")
    async def list_clients(request: Request, status: str = None, plan: str = None, search: str = ""):
        admin(request)
        clients = db.list_clients(status, plan, search)
        return {"count": len(clients), "clients": clients}

    @app.get("/api/admin/clients/{cid}")
    async def get_client(cid: int, request: Request):
        admin(request)
        c = db.get_client_by_id(cid)
        if not c: raise HTTPException(404, "Not found")
        c["renewals"] = db.get_renewal_history(cid)
        c["upgrades"] = db.get_upgrade_history(cid)
        c["devices"] = db.list_devices(client_id=cid)
        return c

    @app.put("/api/admin/clients/{cid}")
    async def update_client(cid: int, request: Request):
        admin(request)
        body = await request.json()
        db.update_client(cid, **body)
        return {"success": True}

    @app.delete("/api/admin/clients/{cid}")
    async def delete_client(cid: int, request: Request):
        admin(request)
        db.delete_client(cid)
        return {"success": True}

    @app.post("/api/admin/revoke")
    async def revoke(req: RevokeReq, request: Request):
        admin(request)
        ok = db.revoke_client(req.license_key.strip())
        if not ok: raise HTTPException(404, "Not found")
        return {"success": True, "message": "授权已禁用"}

    @app.post("/api/admin/renew")
    async def renew(req: RenewReq, request: Request):
        admin(request)
        c = db.renew_license(req.license_key, req.days, req.amount)
        return {"success": True, "new_expire": c["expire_date"],
                "days_added": req.days, "company": c["company_name"]}

    @app.post("/api/admin/upgrade")
    async def upgrade(req: UpgradeReq, request: Request):
        admin(request)
        if req.new_plan not in PLANS:
            raise HTTPException(400, f"Invalid plan. Available: {list(PLANS.keys())}")
        c = db.upgrade_plan(req.license_key, req.new_plan)
        return {"success": True, "new_plan": c["plan_name"],
                "device_limit": c["device_limit"], "company": c["company_name"]}

    # === Admin: Devices ===
    @app.get("/api/admin/devices")
    async def list_devices(request: Request, client_id: int = None, online_only: bool = False):
        admin(request)
        devices = db.list_devices(client_id, online_only)
        return {"count": len(devices), "devices": devices}

    @app.post("/api/admin/devices/{did}/deactivate")
    async def deactivate_device(did: int, request: Request):
        admin(request); db.deactivate_device(did); return {"success": True}

    # === Admin: Stats & Logs ===
    @app.get("/api/admin/stats")
    async def stats(request: Request):
        admin(request)
        s = db.get_stats(); s["revenue"] = db.get_revenue_stats(); s["plans"] = list(PLANS.keys())
        return s

    @app.get("/api/admin/logs")
    async def logs(request: Request, license_key: str = None, action: str = None, limit: int = 200):
        admin(request)
        l = db.get_logs(license_key, action, limit)
        return {"count": len(l), "logs": l}

    @app.get("/api/admin/expiring")
    async def expiring(request: Request, days: int = 30):
        admin(request)
        c = db.get_expiring_clients(days)
        return {"count": len(c), "clients": c}

    # === Admin Dashboard HTML ===
    @app.get("/admin", response_class=HTMLResponse)
    @app.get("/admin/", response_class=HTMLResponse)
    async def dashboard():
        return ADMIN_HTML

    return app


# ================================================================
# Admin Dashboard (Single-page app)
# ================================================================
ADMIN_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SaaS License Server — Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#0d1117;color:#c9d1d9}
.header{background:#161b22;padding:14px 24px;border-bottom:1px solid #30363d;display:flex;align-items:center;gap:14px}
.header h1{font-size:17px;color:#e94560}.header .pill{font-size:11px;color:#8b949e;background:#21262d;padding:4px 12px;border-radius:10px}
.container{max-width:1500px;margin:0 auto;padding:18px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;text-align:center}
.card .num{font-size:26px;font-weight:bold}.card .lbl{font-size:11px;color:#8b949e;margin-top:4px}
.tabs{display:flex;gap:4px;margin-bottom:16px}
.tab{padding:9px 22px;background:#21262d;border:none;color:#8b949e;cursor:pointer;border-radius:6px 6px 0 0;font-size:12px;font-weight:bold}
.tab.active{background:#161b22;color:#e94560;border-bottom:3px solid #e94560}
.panel{background:#161b22;border:1px solid #30363d;border-radius:0 8px 8px 8px;padding:18px}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:9px 10px;font-size:11px;color:#8b949e;border-bottom:1px solid #30363d}
td{padding:8px 10px;font-size:12px;border-bottom:1px solid #21262d}
tr:hover td{background:#1a1a2e}
.badge{padding:2px 10px;border-radius:10px;font-size:10px;font-weight:bold}
.bg-green{background:#23863622;color:#238636}.bg-red{background:#da363322;color:#da3633}
.bg-yellow{background:#d2992222;color:#d29922}.bg-gray{background:#8b949e22;color:#8b949e}
.btn{padding:7px 14px;border:none;border-radius:5px;cursor:pointer;font-size:11px;font-weight:bold}
.btn-primary{background:#238636;color:white}.btn-danger{background:#da3633;color:white}
.btn-outline{background:transparent;border:1px solid #30363d;color:#8b949e}
.btn-sm{padding:4px 10px;font-size:10px}
input,select{background:#0d1117;border:1px solid #30363d;border-radius:5px;padding:7px 10px;color:#c9d1d9;font-size:12px}
input:focus,select:focus{border-color:#58a6ff;outline:none}
.modal{display:none;position:fixed;inset:0;background:#000000aa;z-index:100;align-items:center;justify-content:center}
.modal.show{display:flex}
.modal-box{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:22px;max-width:500px;width:90%}
.modal-box h3{margin-bottom:14px;color:#e94560}
.fg{margin-bottom:10px}.fg label{display:block;font-size:11px;color:#8b949e;margin-bottom:3px}
.fg input,.fg select{width:100%}
.toast{position:fixed;top:16px;right:16px;padding:10px 18px;border-radius:7px;z-index:200;font-size:12px;display:none;color:white}
.toast.show{display:block}.t-success{background:#238636}.t-error{background:#da3633}
</style></head>
<body>
<div class="header">
<h1>🔐 SaaS License Server</h1><span style="color:#8b949e;font-size:12px">TikTok AI Factory Pro</span>
<span style="flex:1"></span>
<span class="pill" id="hdChecks">--</span>
<span class="pill" id="hdOnline">--</span>
<span class="pill" id="hdMRR">--</span>
</div>
<div class="container">
<div class="grid4">
<div class="card"><div class="num" style="color:#58a6ff" id="sTotal">--</div><div class="lbl">Total Clients</div></div>
<div class="card"><div class="num" style="color:#238636" id="sActive">--</div><div class="lbl">Active</div></div>
<div class="card"><div class="num" style="color:#d29922" id="sExpiring">--</div><div class="lbl">Expiring ≤30d</div></div>
<div class="card"><div class="num" style="color:#8b5cf6" id="sMRR">--</div><div class="lbl">MRR</div></div>
</div>
<div class="tabs">
<button class="tab active" onclick="tab('clients')">👥 Clients</button>
<button class="tab" onclick="tab('devices')">📱 Devices</button>
<button class="tab" onclick="tab('expiring')">⚠️ Expiring</button>
<button class="tab" onclick="tab('logs')">📋 Logs</button>
<span style="flex:1"></span>
<button class="btn btn-primary" onclick="showRegister()">+ Register</button>
</div>
<div class="panel">
<div id="p-clients">
<input id="search" placeholder="🔍 Search..." style="width:280px;margin-bottom:10px" oninput="loadClients()">
<select id="filterStatus" onchange="loadClients()" style="margin-left:8px"><option value="">All Status</option><option value="active">Active</option><option value="revoked">Revoked</option></select>
<select id="filterPlan" onchange="loadClients()" style="margin-left:8px"><option value="">All Plans</option><option value="STARTER">STARTER</option><option value="PRO">PRO</option><option value="ENTERPRISE">ENTERPRISE</option></select>
<table><thead><tr><th>Company</th><th>Contact</th><th>License Key</th><th>Plan</th><th>Expires</th><th>Devices</th><th>Status</th><th>Actions</th></tr></thead>
<tbody id="tbClients"><tr><td colspan="8" style="text-align:center;color:#484f58">Loading...</td></tr></tbody></table>
</div>
<div id="p-devices" style="display:none"><table><thead><tr><th>Machine ID</th><th>Client</th><th>Plan</th><th>IP</th><th>Last Seen</th><th>Online</th><th>Action</th></tr></thead>
<tbody id="tbDevices"></tbody></table></div>
<div id="p-expiring" style="display:none"><table><thead><tr><th>Company</th><th>Key</th><th>Plan</th><th>Expires</th><th>Days Left</th><th>Actions</th></tr></thead>
<tbody id="tbExpiring"></tbody></table></div>
<div id="p-logs" style="display:none"><table><thead><tr><th>Time</th><th>Key</th><th>Machine</th><th>Action</th><th>Result</th><th>Detail</th></tr></thead>
<tbody id="tbLogs"></tbody></table></div>
</div>
</div>

<div class="modal" id="modalReg"><div class="modal-box">
<h3>📝 Register Client</h3>
<div class="fg"><label>Company *</label><input id="fCompany"></div>
<div class="fg"><label>Contact</label><input id="fContact"></div>
<div class="fg"><label>Email</label><input id="fEmail"></div>
<div style="display:flex;gap:10px">
<div class="fg" style="flex:1"><label>Plan</label><select id="fPlan"><option>STARTER</option><option selected>PRO</option><option>ENTERPRISE</option></select></div>
<div class="fg" style="flex:1"><label>Days</label><input id="fDays" value="365" type="number"></div>
<div class="fg" style="flex:1"><label>Device Limit</label><input id="fDevLimit" value="3" type="number"></div>
</div>
<div class="fg"><label>Notes</label><input id="fNotes"></div>
<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:14px">
<button class="btn btn-outline" onclick="closeModal()">Cancel</button>
<button class="btn btn-primary" onclick="doRegister()">Register</button>
</div></div></div>

<div class="modal" id="modalDetail"><div class="modal-box" style="max-width:700px">
<h3>Client Detail</h3><div id="detailContent"></div>
<div style="text-align:right;margin-top:12px"><button class="btn btn-outline" onclick="closeDetail()">Close</button></div>
</div></div>

<div class="toast" id="toast"></div>

<script>
const API='',KEY='admin-secret-key-change-me';
async function api(p,o={}){
 const r=await fetch(API+p,{headers:{'X-API-Key':KEY,'Content-Type':'application/json'},...o});
 if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.detail||r.statusText)}
 return r.json()
}
let ct='clients';
function tab(t){ct=t;document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));event.target.classList.add('active');
document.querySelectorAll('[id^="p-"]').forEach(e=>e.style.display='none');document.getElementById('p-'+t).style.display='';
if(t=='clients')loadClients();if(t=='devices')loadDevices();if(t=='expiring')loadExpiring();if(t=='logs')loadLogs()}
async function loadStats(){
 const s=await api('/api/admin/stats');
 document.getElementById('sTotal').textContent=s.total_clients;
 document.getElementById('sActive').textContent=s.active_clients;
 document.getElementById('sExpiring').textContent=s.expiring_soon;
 document.getElementById('sMRR').textContent='$'+s.mrr;
 document.getElementById('hdChecks').textContent='Checks: '+s.checks_today;
 document.getElementById('hdOnline').textContent='Online: '+s.online_devices;
 document.getElementById('hdMRR').textContent='MRR: $'+s.mrr
}
async function loadClients(){
 const st=document.getElementById('filterStatus').value,pl=document.getElementById('filterPlan').value,s=document.getElementById('search').value;
 const d=await api('/api/admin/clients?status='+st+'&plan='+pl+'&search='+encodeURIComponent(s));
 const tb=document.getElementById('tbClients');
 tb.innerHTML=d.clients.map(c=>{
  const exp=new Date(c.expire_date),days=Math.ceil((exp-new Date())/86400000);
  let b='bg-green',txt='Active';
  if(c.status=='revoked'){b='bg-gray';txt='Revoked'}
  else if(days<0){b='bg-red';txt='Expired'}else if(days<=30){b='bg-yellow';txt=days+'d'}
  else{txt=days+'d'}
  return`<tr><td><b>${esc(c.company_name)}</b></td><td>${esc(c.contact)}</td><td><code style="font-size:10px">${esc(c.license_key)}</code></td><td>${c.plan_name}</td><td>${c.expire_date}</td><td>${c.device_limit}</td><td><span class="badge ${b}">${txt}</span></td>
  <td>
   <button class="btn btn-outline btn-sm" onclick="showDetail(${c.id})">🔍</button>
   ${c.status=='active'?`<button class="btn btn-outline btn-sm" onclick="doRenew('${c.license_key}')">+</button>
   <button class="btn btn-outline btn-sm" onclick="doUpgrade('${c.license_key}','${c.plan_name}')">⬆</button>
   <button class="btn btn-danger btn-sm" onclick="doRevoke('${c.license_key}')">✕</button>`:''}
  </td></tr>`
 }).join('')
}
async function loadDevices(){
 const d=await api('/api/admin/devices');db.mark_offline_devices(10);
 document.getElementById('tbDevices').innerHTML=d.devices.map(d=>`<tr>
  <td><code>${esc(d.machine_id)}</code></td><td>${esc(d.company_name)}</td><td>${d.plan_name}</td>
  <td>${d.ip_address}</td><td>${d.last_seen}</td>
  <td><span class="badge ${d.is_online?'bg-green':'bg-gray'}">${d.is_online?'🟢 Online':'⚫ Offline'}</span></td>
  <td>${d.is_active?`<button class="btn btn-outline btn-sm" onclick="deactDev(${d.id})">Deactivate</button>`:'Inactive'}</td>
 </tr>`).join('')
}
async function loadExpiring(){
 const d=await api('/api/admin/expiring?days=30');
 document.getElementById('tbExpiring').innerHTML=d.clients.map(c=>{
  const days=Math.ceil((new Date(c.expire_date)-new Date())/86400000);
  return`<tr><td><b>${esc(c.company_name)}</b></td><td><code>${esc(c.license_key)}</code></td><td>${c.plan_name}</td><td>${c.expire_date}</td><td><span class="badge bg-yellow">${days}d</span></td>
  <td><button class="btn btn-primary btn-sm" onclick="doRenew('${c.license_key}')">Renew</button></td></tr>`
 }).join('')
}
async function loadLogs(){
 const d=await api('/api/admin/logs?limit=200');
 document.getElementById('tbLogs').innerHTML=d.logs.map(l=>`<tr>
  <td style="font-size:10px">${l.created_at}</td><td><code style="font-size:10px">${esc((l.license_key||'').substr(0,18))}</code></td>
  <td><code style="font-size:10px">${esc((l.machine_id||'').substr(0,10))}</code></td><td>${l.action}</td>
  <td style="color:${l.result=='success'?'#238636':'#da3633'}">${l.result}</td><td style="font-size:10px">${esc(l.detail||'')}</td>
 </tr>`).join('')
}
function showRegister(){document.getElementById('modalReg').classList.add('show')}
function closeModal(){document.getElementById('modalReg').classList.remove('show')}
async function doRegister(){
 try{
  const r=await api('/api/admin/register',{method:'POST',body:JSON.stringify({
   company_name:document.getElementById('fCompany').value,contact:document.getElementById('fContact').value,
   email:document.getElementById('fEmail').value,plan:document.getElementById('fPlan').value,
   expire_days:parseInt(document.getElementById('fDays').value),
   device_limit:parseInt(document.getElementById('fDevLimit').value)||null,
   notes:document.getElementById('fNotes').value})});
  toast('✅ '+r.license_key,'success');closeModal();loadClients();loadStats();
  ['fCompany','fContact','fEmail','fNotes'].forEach(id=>document.getElementById(id).value='')
 }catch(e){toast('❌ '+e.message,'error')}
}
async function doRevoke(k){if(!confirm('Revoke '+k+'?'))return;await api('/api/admin/revoke',{method:'POST',body:JSON.stringify({license_key:k})});loadClients();loadStats()}
async function doRenew(k){const d=prompt('Days to add:','365');if(!d)return;
 await api('/api/admin/renew',{method:'POST',body:JSON.stringify({license_key:k,days:parseInt(d)})});loadClients();loadExpiring();loadStats();toast('✅ Renewed +'+d+'d','success')}
async function doUpgrade(k,old){const np=prompt('New plan (STARTER/PRO/ENTERPRISE):','PRO');if(!np||np==old)return;
 await api('/api/admin/upgrade',{method:'POST',body:JSON.stringify({license_key:k,new_plan:np})});loadClients();toast('✅ '+old+' → '+np,'success')}
async function deactDev(id){await api('/api/admin/devices/'+id+'/deactivate',{method:'POST'});loadDevices()}
async function showDetail(cid){
 const c=await api('/api/admin/clients/'+cid);
 document.getElementById('detailContent').innerHTML=`
  <p><b>${esc(c.company_name)}</b> | ${c.plan_name} | ${c.status} | Exp: ${c.expire_date}</p>
  <p style="font-size:11px;color:#8b949e">Key: ${esc(c.license_key)} | Devices: ${c.device_limit}</p>
  <hr style="border-color:#30363d;margin:8px 0">
  <p style="font-size:11px">Renewals: ${c.renewals.length} | Upgrades: ${c.upgrades.length} | Devices: ${c.devices.length}</p>`;
 document.getElementById('modalDetail').classList.add('show')
}
function closeDetail(){document.getElementById('modalDetail').classList.remove('show')}
function toast(m,t){const el=document.getElementById('toast');el.textContent=m;el.className='toast show t-'+t;setTimeout(()=>el.classList.remove('show'),3000)}
function esc(s){return(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
loadStats();loadClients()
</script>
</body></html>"""

# ================================================================
# Main
# ================================================================
app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8199
    print(f"""\n╔══════════════════════════════════════════╗
║  🔐 SaaS License Server v3.0              ║
╠══════════════════════════════════════════╣
║  API:   http://0.0.0.0:{port}              ║
║  Docs:  http://0.0.0.0:{port}/docs         ║
║  Admin: http://0.0.0.0:{port}/admin        ║
╠══════════════════════════════════════════╣
║  Plans: STARTER($29) PRO($99) ENT($299)  ║
╚══════════════════════════════════════════╝""")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
