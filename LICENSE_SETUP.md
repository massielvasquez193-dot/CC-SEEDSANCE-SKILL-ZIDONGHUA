# LICENSE SETUP — TikTok AI Factory Pro

## 概述

TikTok AI Factory Pro 使用**机器码+授权码**的商业授权系统。

启动时自动验证 `license.key`，授权通过才能运行。

---

## 客户获取授权流程

### 第1步: 获取机器码

```bash
python -c "from license.license_manager import LicenseManager; lm=LicenseManager(); print(f'Machine Code: {lm.machine_code}')"
```

输出示例:
```
Machine Code: A1B2C3D4E5F6G7H8
```

### 第2步: 发送给供应商

将机器码发送给供应商，获取 `license.key` 文件。

### 第3步: 放置授权文件

将 `license.key` 放在项目根目录:

```
TikTok-AI-Factory-Pro/
├── license.key          ← 放这里
├── run_factory.py
└── ...
```

### 第4步: 启动验证

```bash
python run_factory.py
```

授权通过显示:
```
╔══════════════════════════════════════╗
║  ✅ TikTok AI Factory Pro — 已授权   ║
╠══════════════════════════════════════╣
║  客户: Licensed User                ║
║  版本: 3.0.0                        ║
║  到期: 2027-06-11 (剩余 365 天)      ║
╚══════════════════════════════════════╝
```

---

## 供应商生成授权

### 生成 license.key

```python
from license.license_manager import LicenseManager

# 客户的机器码
machine_code = "A1B2C3D4E5F6G7H8"

# 生成授权
license_content = LicenseManager.generate_license_key(
    machine_code=machine_code,
    product_version="3.0.0",
    expiry_date="2027-06-11",
    client_name="Acme Corp",
    secret="YOUR-PRIVATE-SECRET-KEY",
)

# 保存
with open("license.key", "w") as f:
    f.write(license_content)

print("license.key generated.")
```

### license.key 格式

```json
{
  "machine_code": "A1B2C3D4E5F6G7H8",
  "product": "TikTok AI Factory Pro",
  "version": "3.0.0",
  "client": "Acme Corp",
  "issued_at": "2026-06-11",
  "expiry_date": "2027-06-11",
  "type": "commercial",
  "features": [
    "full_pipeline",
    "batch_mode",
    "watch_mode",
    "seedance_integration",
    "gpt_image_keyframes",
    "elevenlabs_tts",
    "ugc_scoring"
  ],
  "signature": "abc123..."
}
```

---

## 验证维度

| 验证项 | 说明 |
|--------|------|
| 机器码匹配 | 授权机器码 = 当前机器码 (SHA256硬件指纹) |
| 签名校验 | HMAC-SHA256 防篡改 |
| 到期时间 | now < expiry_date (到期前30天提醒) |
| 版本号 | 主版本号必须匹配 |

---

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `授权文件未找到` | license.key 不存在 | 放 license.key 到项目根目录 |
| `机器码不匹配` | 换了机器 | 联系供应商重新授权 |
| `签名无效` | 文件被修改 | 重新获取原始 license.key |
| `授权已过期` | 超过到期日 | 续费 |
| `版本不兼容` | 软件升级但授权未更新 | 升级授权或降级软件 |

---

## 安全特性

- ✅ SHA256 硬件指纹 (MAC + CPU + 磁盘 + 主机名)
- ✅ HMAC-SHA256 签名防篡改
- ✅ 到期前30天自动警告
- ✅ 离线验证 (不需要联网)
- ✅ 版本锁定 (主版本不匹配拒绝运行)

---

## 测试授权

开发测试用 `license.key` (1年有效期):

```bash
python -c "
from license.license_manager import LicenseManager
lm = LicenseManager()
key = LicenseManager.generate_license_key(
    machine_code=lm.machine_code,
    product_version='3.0.0',
    expiry_date='2027-06-11',
    client_name='Dev Test',
)
with open('license.key', 'w') as f:
    f.write(key)
print(f'Test license created for {lm.machine_code}')
"
```
