# TikTok AI Factory Pro — Release Package Report

## 版本
**TikTok AI Factory Pro v1.0.0**

## 发布日期
2026-06-14

---

## 客户交付物 (client/)

客户获得的完整运行时文件。

### 核心运行文件

| 文件 | 说明 |
|------|------|
| `launcher.py` | GUI/CLI 启动器 |
| `run_factory.py` | CLI 工厂入口 |
| `version.txt` | 版本文件 |
| `requirements.txt` | Python 依赖 |
| `.env` | 配置文件（需填入 API Key） |
| `license.key` | 授权文件 |

### Python 包 (13 个)

| 目录 | 说明 | 文件数 |
|------|------|--------|
| `agents/` | AI Agent 模块（剧本/分镜/口播/关键帧/一致性） | 17 |
| `app/` | 应用核心（流水线/扫描器/GUI/控制器） | 18 |
| `config/` | 配置文件（settings/provider/factory/update） | 6 |
| `providers/` | AI 提供商（OpenAI/Claude/DeepSeek/Seedance/...） | 10 |
| `license/` | 授权管理（在线+离线） | 2 |
| `updater/` | 自动更新系统（检查/下载/安装/回滚） | 5 |
| `workflows/` | 工厂工作流 | 2 |
| `skills/` | 视频复刻技能 | 2 |
| `prompts/` | 系统提示词 | 1 |
| `tools/` | 工具（成本报告/环境检测） | 4 |
| `input/` | 素材输入目录（空） | — |
| `output/` | 视频输出目录（空） | — |
| `server/` | License Server | 4 |

### 客户交付文件总数
**117 个文件**

### 安装包大小
**1.9 MB**

---

## 文档 (docs/) — 26 个文档

### 用户指南 (user-guides/)
- CLIENT_USER_GUIDE.md — 客户端使用指南
- CLIENT_INSTALL_GUIDE.md — 安装指南
- CUSTOMER_DASHBOARD_GUIDE.md — 客户后台使用指南
- FAQ.md — 常见问题
- README.md — 项目说明

### 功能文档 (features/)
- ONE_CLICK_MODE.md — 一键生成
- BATCH_FACTORY_MODE.md — 批量工厂
- SETTINGS_CENTER.md — 设置中心
- CUSTOMER_PORTAL.md — 客户后台
- AUTO_UPDATE_SYSTEM.md — 自动更新

### 技术文档 (technical/)
- LICENSE_SERVER.md — 授权服务器
- RC_TEST_REPORT.md — RC 测试报告

---

## 开发文件 (dev/) — 12 个文件

以下文件**已从客户交付包中排除**：

- 开发阶段报告（Phase 2/3、Production Acceptance）
- 项目审计报告（Project/Provider/Video Audit）
- GUI 测试报告
- Seedance 调试报告
- Installer 构建脚本

---

## 测试文件 (tests/) — 5 个文件

- RC_TEST_REPORT.md — 100 任务压力测试报告
- UPDATE_TEST_REPORT.md — 更新系统测试报告
- rc_stress_test.py — 压力测试脚本
- rc_stress_test_results.json — 原始测试数据

---

## 客户端安装步骤

### 1. 解压
解压 `TikTok-AI-Factory-Pro-v1.0.0.zip` 到任意目录。

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置 API Key
编辑 `.env`，填入：
```bash
OPENAI_API_KEY=sk-...
ARK_API_KEY=ark-...
ELEVENLABS_API_KEY=el_...
```

### 4. 放入素材
将产品图/人物图/参考视频放入 `input/` 对应目录。

### 5. 启动
```bash
# GUI
python launcher.py

# CLI
python run_factory.py --max-tasks 1
```

### 6. 授权
将 `license.key` 放在项目根目录，或配置在线 License Server。

---

## 更新方式

软件启动时自动检查 `config/update.json` 中配置的更新服务器。
发现新版本后弹窗提示，一键下载安装自动重启。

详见：docs/features/AUTO_UPDATE_SYSTEM.md

---

## 授权方式

### 离线模式
将 `license.key` 放在项目根目录，软件启动时自动验证。

### 在线模式
配置 `.env`：
```bash
LICENSE_SERVER_URL=http://your-server:8199
LICENSE_KEY=TKAIF-XXXX-XXXX-XXXX-XXXX
```

启动时先在线验证，服务器不可达时降级到离线验证。

详见：docs/technical/LICENSE_SERVER.md

---

## 排除项

以下内容**未包含**在客户交付包中：

| 类别 | 排除内容 |
|------|----------|
| 开发数据 | `output/` 目录内容、`logs/` 目录内容 |
| 缓存 | `__pycache__/`、`*.pyc` |
| 数据库 | `*.db` (License Server 运行时生成) |
| 开发报告 | Phase 报告、Audit 报告 |
| 测试数据 | 压力测试输出、测试日志 |
| 原始素材 | `sample_input/` 中的示例文件 |
| 敏感信息 | `.env` 中的真实 API Key（已替换为空） |

---

## 目录树 (client/)

```
client/
├── launcher.py                 # 启动器
├── run_factory.py              # CLI 入口
├── version.txt                 # 版本 v1.0.0
├── requirements.txt            # Python 依赖
├── .env                        # 配置模板
├── .env.example                # 配置示例
├── license.key                 # 授权文件
│
├── agents/                     # AI Agent 引擎
│   ├── master_script_generator.py
│   ├── script_generator.py
│   ├── storyboard_generator.py
│   ├── keyframe_generator.py
│   ├── seedance_generator.py
│   ├── veo3_generator.py
│   ├── jimeng_generator.py
│   ├── voiceover_generator.py
│   ├── character_consistency.py
│   ├── character_generator.py
│   ├── character_library.py
│   ├── continuity_engine.py
│   ├── ugc_director.py
│   ├── ugc_score.py
│   ├── subtitle_generator.py
│   ├── subtitle_alignment.py
│   ├── image_prompt_generator.py
│   ├── viral_analyzer.py
│   ├── voice_style_analyzer.py
│   └── export_manager.py
│
├── app/                        # 应用核心
│   ├── pipeline.py
│   ├── scanner.py
│   ├── task_manager.py
│   ├── watcher.py
│   ├── product_extractor.py
│   ├── character_extractor.py
│   ├── video_analyzer.py
│   ├── ugc_director.py
│   ├── voice_engine.py
│   ├── ffmpeg_voice_merge.py
│   └── gui/
│       ├── gui.py              # 主 GUI (5 标签页)
│       ├── one_click_tab.py
│       ├── one_click_controller.py
│       ├── batch_factory_tab.py
│       ├── batch_controller.py
│       ├── batch_scheduler.py
│       ├── settings_tab.py
│       ├── customer_portal.py
│       ├── cost_tracker.py
│       └── video_history.py
│
├── config/                     # 配置
│   ├── settings.py
│   ├── settings_manager.py
│   ├── api_validator.py
│   ├── api_keys.py
│   ├── factory.json
│   ├── providers.json
│   ├── update.json
│   └── voices.json
│
├── providers/                  # AI 提供商 (9 个)
│   ├── base_provider.py
│   ├── openai_provider.py
│   ├── claude_provider.py
│   ├── deepseek_provider.py
│   ├── gemini_provider.py
│   ├── seedance_provider.py
│   ├── veo3_provider.py
│   ├── jimeng_provider.py
│   ├── runway_provider.py
│   ├── kling_provider.py
│   └── elevenlabs_provider.py
│
├── license/                    # 授权系统
├── updater/                    # 自动更新
├── workflows/                  # 工作流
├── skills/                     # 视频复刻
├── prompts/                    # 提示词
├── tools/                      # 工具集
├── server/                     # License Server
├── input/                      # 素材目录 (空)
├── output/                     # 输出目录 (空)
├── logs/                       # 日志目录 (空)
├── installer/                  # 打包工具
└── sample_input/               # 示例素材
```

---

*报告生成时间: 2026-06-14T14:26:30.434357*
*构建工具: tools/build_release.py*
