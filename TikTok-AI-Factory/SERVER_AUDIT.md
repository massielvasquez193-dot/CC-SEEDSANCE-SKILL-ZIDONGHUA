# Server 目录审计报告

## 审计范围

`release/client/server/` — 87 KB, 6 个文件

## 文件清单与分析

### 1. `server/__init__.py`
- **大小:** 105 字节
- **用途:** Python 包标记文件。声明为 "Online authorization system with FastAPI + SQLite"。
- **分类:** License 后台 — 服务端包定义
- **客户运行必须:** ❌ 否

### 2. `server/license_server/__init__.py`
- **大小:** 172 字节
- **用途:** License Server 子包标记。导出 `Database`、`app`、`create_app` 三个符号。
- **分类:** License 后台 — 服务端包定义
- **客户运行必须:** ❌ 否

### 3. `server/license_server/database.py`
- **大小:** 425 行, ~15 KB
- **用途:** **SaaS License Server 数据库层**。管理以下数据表：
  - `plans` — 套餐定义 (STARTER/PRO/ENTERPRISE)
  - `clients` — 客户注册信息
  - `devices` — 设备绑定与在线状态
  - `renewals` — 续费历史
  - `upgrades` — 升级记录
  - `license_logs` — 审计日志
- **分类:** License 后台 — 供应商管理工具
- **客户运行必须:** ❌ 否
- **说明:** 此文件运行在供应商的 License Server 上。客户端的 `license/license_manager.py` 通过 HTTP API 调用服务端，不需要本地运行此代码。

### 4. `server/license_server/license_api.py`
- **大小:** 415 行, ~17 KB
- **用途:** **SaaS License Server FastAPI 应用**。提供：
  - `POST /api/license/check` — 客户端验证授权
  - `POST /api/license/heartbeat` — 设备心跳
  - `POST /api/admin/register` — 注册新客户
  - `POST /api/admin/revoke` — 远程禁用授权
  - `POST /api/admin/renew` — 续费管理
  - `POST /api/admin/upgrade` — 升级管理
  - `GET /api/admin/stats` — MRR/收入统计
  - `GET /api/admin/clients` — 客户列表
  - `GET /api/admin/devices` — 在线设备管理
  - `GET /api/admin/logs` — 审计日志
  - `GET /admin` — 内嵌 SPA 管理后台 HTML
- **分类:** License 后台 + 管理后台 — 供应商管理工具
- **客户运行必须:** ❌ 否
- **说明:** 这是供应商运营用的后台系统。客户不需要启动 License Server，只需在 `.env` 中配置 `LICENSE_SERVER_URL` 指向供应商已部署的服务器。

### 5. `server/license_server/license.db-shm`
- **大小:** 32 KB
- **用途:** SQLite WAL (Write-Ahead Log) 共享内存文件。**这是测试运行时产生的临时文件，不是源代码。**
- **分类:** 🗑️ 测试残留文件 — 应从发布包中删除
- **客户运行必须:** ❌ 否
- **说明:** 此文件是 `license.db` 数据库的 WAL 索引，由 SQLite 在运行时自动创建。正常情况下不应出现在发布包中。关闭数据库连接后此文件会被自动清理。

### 6. `server/requirements.txt`
- **大小:** 42 字节
- **内容:** `fastapi>=0.110.0` / `uvicorn>=0.27.0` / `pydantic>=2.0.0`
- **用途:** License Server 的 Python 依赖声明
- **分类:** License 后台 — 服务端依赖
- **客户运行必须:** ❌ 否
- **说明:** 客户的 `requirements.txt` 已包含所有需要的依赖。这三个包是 Web 服务框架，客户运行视频工厂不需要。

---

## 分类汇总

| 文件 | 分类 | 客户必须? | 建议 |
|------|------|:--:|------|
| `__init__.py` | License 后台 | ❌ | 删除 |
| `license_server/__init__.py` | License 后台 | ❌ | 删除 |
| `license_server/database.py` | License 后台 | ❌ | 删除 |
| `license_server/license_api.py` | License 后台 + 管理后台 | ❌ | 删除 |
| `license_server/license.db-shm` | 🗑️ 测试残留 | ❌ | 删除 |
| `requirements.txt` | License 后台 | ❌ | 删除 |

---

## 最终判定

### ✅ 建议：从客户发布包中删除整个 `server/` 目录

**理由:**

1. **客户不需要运行 License Server。** License Server 是供应商的基础设施，部署在供应商的云服务器上。客户只需在 `.env` 中配置 `LICENSE_SERVER_URL` 指向供应商服务器。

2. **server/ 引入了不必要的依赖。** `fastapi`、`uvicorn`、`pydantic` 三个包合计约 15 MB，客户完全不需要安装这些 Web 框架。

3. **server/ 包含管理后台代码。** 客户不应拥有管理后台的访问能力（即使有代码也需要 API Key），这会带来安全风险。

4. **server/ 包含测试残留文件。** `license.db-shm` 是运行时的临时文件，不应发布。

5. **客户授权功能已由 `license/license_manager.py` 完整覆盖。** 客户端的 `_try_online_validation()` 方法通过 HTTP 调用远程服务器，`send_heartbeat()` 维持设备在线状态，`get_plan_info()` 获取套餐能力。所有客户端功能已完备。

### 删除后客户体验不受影响

| 功能 | 依赖 server/? | 说明 |
|------|:--:|------|
| 离线授权 (license.key) | ❌ | 纯本地验证 |
| 在线授权 (SaaS) | ❌ | 通过 HTTP 调用远程服务器 |
| 设备心跳 | ❌ | `POST /api/license/heartbeat` |
| 套餐功能查询 | ❌ | `GET /api/plans` → 本地缓存 |
| 续费提醒 | ❌ | `check_renewal_needed()` 基于服务器返回的到期时间 |

### 删除后节省

| 指标 | 节省 |
|------|------|
| 文件数 | 6 个 |
| 磁盘空间 | 87 KB |
| 依赖包 | fastapi + uvicorn + pydantic (~15 MB) |
| 安全风险 | 移除管理后台源码暴露 |

---

*审计时间: 2026-06-14*
*审计范围: release/client/server/*
