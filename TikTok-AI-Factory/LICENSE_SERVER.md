# TikTok AI Factory Pro — License Server

## 概述

在线授权系统，集中管理所有客户的 License。FastAPI + SQLite，内嵌管理后台。

## 架构

```
客户端 (TikTok AI Factory Pro)
  │
  │  启动时 POST /api/license/check
  │  {license_key, machine_id}
  │
  ▼
License Server (FastAPI + SQLite)
  │
  ├─ 验证 license_key
  ├─ 检查状态 (active/revoked)
  ├─ 检查到期时间
  ├─ 检查设备数限制
  ├─ 记录设备 (machine_id)
  └─ 返回 {valid, plan, expire, ...}
  │
  ▼
管理员 → 浏览器 http://server:8199/admin
  ├─ 客户列表 + 搜索
  ├─ 注册新客户
  ├─ 禁用授权
  ├─ 设备管理
  └─ 到期提醒
```

## 快速启动

```bash
# 1. 安装依赖
pip install -r server/requirements.txt

# 2. 启动服务
python -m server.license_server.license_api

# 3. 访问
#    API:    http://localhost:8199
#    Docs:   http://localhost:8199/docs
#    Admin:  http://localhost:8199/admin
```

自定义端口：
```bash
python -m server.license_server.license_api 9090
```

## 环境变量

```bash
# Server
LICENSE_SERVER_API_KEY=admin-secret-key-change-me  # 管理 API 密钥
```

## API 文档

### 公开端点

#### POST /api/license/check
客户端启动时验证授权。

```json
// Request
{
  "license_key": "TKAIF-ABCDE-FGHIJ-KLMNO-PQRST",
  "machine_id": "8D2F97F796D35EBD"
}

// Response (成功)
{
  "valid": true,
  "expire": "2027-06-14",
  "plan": "PRO",
  "company": "某科技有限公司",
  "device_limit": 3,
  "devices_registered": 1,
  "days_remaining": 365
}

// Response (失败)
{
  "valid": false,
  "reason": "expired",
  "message": "授权已过期"
}
```

#### GET /api/health
服务器健康检查。

### 管理端点 (需要 `X-API-Key` 请求头)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | /api/license/register | 注册新客户，生成 License Key |
| POST | /api/license/revoke | 禁用授权 |
| GET | /api/license/stats | 服务器统计 |
| GET | /api/license/clients | 客户列表（支持 ?status=active&search=关键词） |
| GET | /api/license/clients/{id} | 单个客户详情 |
| PUT | /api/license/clients/{id} | 更新客户信息 |
| DELETE | /api/license/clients/{id} | 删除客户 |
| GET | /api/license/devices | 设备列表 |
| POST | /api/license/devices/{id}/deactivate | 停用设备 |
| GET | /api/license/logs | 验证日志 |
| GET | /api/license/expiring | 即将到期的客户（?days=30） |

## 管理后台

访问 `http://server:8199/admin` 进入 Web 管理界面。

功能：
- **客户列表**：搜索、筛选、查看详情
- **注册新客户**：填写公司信息，自动生成 License Key
- **到期提醒**：30 天内到期的客户高亮
- **设备管理**：查看每个客户注册的设备，可停用
- **验证日志**：所有 license check 请求的历史记录
- **一键禁用**：Revoke 授权
- **续期**：延长到期时间

## 数据库结构

### clients 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| company_name | TEXT | 公司名称 |
| contact | TEXT | 联系人 |
| email | TEXT | 邮箱 |
| license_key | TEXT (UNIQUE) | 授权码 (TKAIF-XXXX-XXXX-XXXX-XXXX) |
| plan | TEXT | 计划 (PRO/ENTERPRISE/STARTER) |
| expire_date | TEXT | 到期日期 (YYYY-MM-DD) |
| device_limit | INTEGER | 设备数量限制 |
| status | TEXT | active / revoked |
| notes | TEXT | 备注 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### devices 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| client_id | INTEGER | 关联 clients.id |
| machine_id | TEXT | 机器指纹 |
| machine_name | TEXT | 机器名称 |
| ip_address | TEXT | IP 地址 |
| first_seen | TEXT | 首次连接 |
| last_seen | TEXT | 最近连接 |
| is_active | INTEGER | 是否活跃 |

### license_logs 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| client_id | INTEGER | 客户 ID |
| license_key | TEXT | 授权码 |
| machine_id | TEXT | 机器 ID |
| action | TEXT | check / register / revoke |
| result | TEXT | success / denied / invalid |
| ip_address | TEXT | 请求 IP |
| detail | TEXT | 详情 |
| created_at | TEXT | 时间 |

## 客户端配置

在客户端 `.env` 中配置：

```bash
# License Server 地址
LICENSE_SERVER_URL=http://your-server:8199

# 分配给客户的 License Key（从管理后台生成）
LICENSE_KEY=TKAIF-XXXX-XXXX-XXXX-XXXX
```

### 验证流程

1. 客户端启动 → 读取 `LICENSE_SERVER_URL` + `LICENSE_KEY`
2. 调用 `POST /api/license/check` 传入 `license_key` + `machine_id`
3. 服务器验证通过 → 进入系统
4. 服务器验证失败（状态为 revoked/expired/超设备）→ **拒绝进入，退出**
5. 服务器不可达 → **降级到离线 license.key 验证**
6. 离线验证也失败 → 退出

## 部署建议

- 使用 `systemd` / `Supervisor` / `NSSM`(Windows) 保持服务运行
- 前面加 Nginx 反向代理 + HTTPS
- 修改默认 `LICENSE_SERVER_API_KEY`
- 定期备份 `license.db`

## 文件清单

```
server/
├── __init__.py
├── requirements.txt
└── license_server/
    ├── __init__.py
    ├── database.py          # SQLite 数据库层 (~280 行)
    ├── license_api.py       # FastAPI + 管理后台 HTML (~420 行)

license/
└── license_manager.py       # ✏️ 新增 _try_online_validation()

LICENSE_SERVER.md            # 本文档
```
