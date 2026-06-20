# TikTok AI Factory Pro — Release Manifest

## 版本信息
- **版本号:** v1.0.0
- **发布日期:** 2026-06-14
- **包大小:** 2.0 MB
- **总文件数:** 158
- **Python 文件:** 75

## 包含的运行时包
- **app/** — 25 个文件
- **agents/** — 21 个文件
- **providers/** — 12 个文件
- **config/** — 8 个文件
- **license/** — 1 个文件
- **updater/** — 5 个文件
- **workflows/** — 2 个文件
- **skills/** — 2 个文件
- **prompts/** — 1 个文件
- **installer/** — 5 个文件
- **case_library/** — 52 个文件

## 包含的根文件
- `launcher.py`
- `run_factory.py`
- `version.txt`
- `requirements.txt`
- `.env.example`
- `.env` (从 .env.example 生成)
- `README.md`
- `QUICK_START.md`

## 从客户包中排除的文件

### 开发报告 (已排除)
- `\installer\build_installer.bat`
- `\installer\setup.iss`
- `.env`

### 排除类别
- 所有 *REPORT*.md / *AUDIT*.md
- 开发阶段文档 (PHASE2/3, PRODUCTION_ACCEPTANCE 等)
- 测试文件 (RC_TEST_REPORT, UPDATE_TEST_REPORT 等)
- 构建脚本 (setup.iss, build_installer.bat)
- 开发工具源码 (demo_generator.py, rc_stress_test.py 等)
- 缓存文件 (__pycache__/, *.pyc)
- 数据库文件 (*.db)
- 敏感文件 (.env 真实 Key)
- .docx 文件
- .gitignore, .git/

## 空目录 (运行时填充)
- `input/products/`
- `input/characters/`
- `input/reference_videos/`
- `output/`
- `logs/`

## 目录树
```
├── agents/ (21 files)
│   ├── character_consistency.py
│   ├── character_generator.py
│   ├── character_library.py
│   ├── continuity_engine.py
│   ├── export_manager.py
│   ├── image_prompt_generator.py
│   ├── jimeng_generator.py
│   ├── keyframe_generator.py
│   ├── master_script_generator.py
│   ├── script_generator.py
│   ├── seedance_generator.py
│   ├── storyboard_generator.py
│   ├── subtitle_alignment.py
│   ├── subtitle_generator.py
│   ├── ugc_director.py
│   ├── ugc_score.py
│   ├── veo3_generator.py
│   ├── viral_analyzer.py
│   ├── voice_style_analyzer.py
│   └── voiceover_generator.py
├── app/ (24 files)
│   ├── gui/ (13 files)
│   │   ├── api_wizard.py
│   │   ├── batch_controller.py
│   │   ├── batch_factory_tab.py
│   │   ├── batch_scheduler.py
│   │   ├── case_browser.py
│   │   ├── cost_tracker.py
│   │   ├── customer_portal.py
│   │   ├── gui.py
│   │   ├── one_click_controller.py
│   │   ├── one_click_tab.py
│   │   ├── settings_tab.py
│   │   └── video_history.py
│   ├── character_extractor.py
│   ├── ffmpeg_voice_merge.py
│   ├── pipeline.py
│   ├── product_extractor.py
│   ├── scanner.py
│   ├── task_manager.py
│   ├── ugc_director.py
│   ├── video_analyzer.py
│   ├── voice_engine.py
│   └── watcher.py
├── case_library/ (43 files)
│   ├── Anua/ (14 files)
│   │   ├── 05_KEYFRAMES/ (6 files)
│   │   ├── _frames/ (0 files)
│   │   ├── 01_PRODUCT_Anua.png
│   │   ├── 02_CHARACTER_Anua.png
│   │   ├── 03_SCRIPT_Anua.md
│   │   ├── 04_CHARACTER_SETTING_Anua.json
│   │   ├── 06_STORYBOARD_Anua.png
│   │   ├── 07_VOICEOVER_Anua.md
│   │   ├── 08_SUBTITLES_Anua.srt
│   │   └── 10_PERFORMANCE_REPORT_Anua.md
│   ├── COSRX/ (14 files)
│   │   ├── 05_KEYFRAMES/ (6 files)
│   │   ├── _frames/ (0 files)
│   │   ├── 01_PRODUCT_COSRX.png
│   │   ├── 02_CHARACTER_COSRX.png
│   │   ├── 03_SCRIPT_COSRX.md
│   │   ├── 04_CHARACTER_SETTING_COSRX.json
│   │   ├── 06_STORYBOARD_COSRX.png
│   │   ├── 07_VOICEOVER_COSRX.md
│   │   ├── 08_SUBTITLES_COSRX.srt
│   │   └── 10_PERFORMANCE_REPORT_COSRX.md
│   ├── Medicube/ (14 files)
│   │   ├── 05_KEYFRAMES/ (6 files)
│   │   ├── _frames/ (0 files)
│   │   ├── 01_PRODUCT_Medicube.png
│   │   ├── 02_CHARACTER_Medicube.png
│   │   ├── 03_SCRIPT_Medicube.md
│   │   ├── 04_CHARACTER_SETTING_Medicube.json
│   │   ├── 06_STORYBOARD_Medicube.png
│   │   ├── 07_VOICEOVER_Medicube.md
│   │   ├── 08_SUBTITLES_Medicube.srt
│   │   └── 10_PERFORMANCE_REPORT_Medicube.md
│   └── case_index.json
├── config/ (8 files)
│   ├── api_keys.py
│   ├── api_validator.py
│   ├── factory.json
│   ├── providers.json
│   ├── settings.py
│   ├── settings_manager.py
│   ├── update.json
│   └── voices.json
├── input/ (0 files)
│   ├── characters/ (0 files)
│   ├── products/ (0 files)
│   └── reference_videos/ (0 files)
├── installer/ (5 files)
│   ├── BUILD_INSTRUCTIONS.md
│   ├── install_deps.bat
│   ├── launcher.spec
│   ├── setup_script.py
│   └── setup_v1.iss
├── license/ (1 files)
│   └── license_manager.py
├── logs/ (0 files)
├── output/ (0 files)
├── prompts/ (1 files)
│   └── system_prompts.py
├── providers/ (12 files)
│   ├── base_provider.py
│   ├── claude_provider.py
│   ├── deepseek_provider.py
│   ├── elevenlabs_provider.py
│   ├── gemini_provider.py
│   ├── jimeng_provider.py
│   ├── kling_provider.py
│   ├── openai_provider.py
│   ├── runway_provider.py
│   ├── seedance_provider.py
│   └── veo3_provider.py
├── skills/ (2 files)
│   └── video_replication.py
├── updater/ (5 files)
│   ├── download_manager.py
│   ├── update_installer.py
│   ├── update_manager.py
│   └── version_checker.py
├── workflows/ (2 files)
│   └── factory_workflow.py
├── .env.example
├── QUICK_START.md
├── README.md
├── launcher.py
├── requirements.txt
├── run_factory.py
└── version.txt
```

---
*生成时间: 2026-06-14T16:20:11.893196*
*构建工具: tools/release_builder.py*