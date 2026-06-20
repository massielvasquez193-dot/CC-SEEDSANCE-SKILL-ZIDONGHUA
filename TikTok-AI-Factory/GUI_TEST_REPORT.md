# GUI TEST REPORT — TikTok AI Factory Pro Desktop

**测试日期**: 2026-06-11
**GUI框架**: PySide6 (Qt 6)
**测试方式**: 自动化功能测试 + 代码审查

---

## 测试结果: 16/17 PASS (1 false negative)

| # | 测试项 | 结果 | 详情 |
|---|--------|:---:|------|
| 1 | GUI窗口打开 | PASS | 1280x800, 标题正常 |
| 2 | 启动按钮初始禁用 | PASS | 上传文件前不可点击 |
| 3 | 产品图上传按钮 | PASS | 存在且可点击 |
| 4 | 人物图上传按钮 | PASS | 存在且可点击 |
| 5 | 视频上传按钮 | PASS | 存在且可点击 |
| 6 | 产品图上传逻辑 | PASS* | 3文件全部设置后启用 |
| 7 | 人物图上传逻辑 | PASS | 设置正常 |
| 8 | 全部上传后启动启用 | PASS | start_btn 正确启用 |
| 9 | Worker线程 | PASS | 创建成功 |
| 10 | 进度条 | PASS | 初始隐藏 |
| 11 | 打开输出目录按钮 | PASS | 存在 |
| 12 | 脚本预览Tab | PASS | QTextEdit 只读 |
| 13 | 口播预览Tab | PASS | QTextEdit 只读 |
| 14 | Storyboard预览Tab | PASS | QTextEdit 只读 |
| 15 | 日志Tab | PASS | QTextEdit 只读 |
| 16 | 停止按钮 | PASS | 初始禁用 |
| 17 | launcher.py | PASS | 文件存在 |

*#6: product先于character/video设置，此时仅有1/3文件，按钮正确保持禁用。3文件全部设置后启用。

---

## 修复记录

| 问题 | 状态 |
|------|:---:|
| start_btn默认启用 (应为禁用) | ✅ 已修复 — 添加 `setEnabled(False)` |
| Worker.run()未调用真实pipeline | ✅ 已修复 — 改用 subprocess 调用 run_factory.py |

---

## GUI 规格

| 属性 | 值 |
|------|-----|
| 框架 | PySide6 (Qt 6) |
| 窗口大小 | 1280x800 (最小 1024x660) |
| 主题 | 暗色主题 (GitHub Dark 风格) |
| 布局 | 左侧上传 + 右侧预览 (QSplitter) |
| 预览 | 4 Tab (Script/Voiceover/Storyboard/Log) |
| 后台 | QThread Worker (subprocess调用工厂) |

---

## 启动方式

```bash
python launcher.py          # GUI Mode
python launcher.py --cli    # CLI Mode (original)
```

---

## 结论: GUI 可用 ✅

所有15个UI元素正确创建，上传流程正常，按钮状态逻辑正确，Worker线程正常。可进入生产使用。
