# -*- mode: python ; coding: utf-8 -*-
"""
TikTok AI Factory Pro — PyInstaller Spec
==========================================
Builds launcher.exe from the Python project.

Usage:
    pip install pyinstaller
    pyinstaller installer/launcher.spec

Output:
    dist/launcher.exe
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

a = Analysis(
    [str(PROJECT_ROOT / 'launcher.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # Configuration files
        (str(PROJECT_ROOT / '.env.example'), '.'),
        (str(PROJECT_ROOT / 'version.txt'), '.'),
        (str(PROJECT_ROOT / 'requirements.txt'), '.'),
        # Config directory
        (str(PROJECT_ROOT / 'config' / 'factory.json'), 'config'),
        (str(PROJECT_ROOT / 'config' / 'providers.json'), 'config'),
        (str(PROJECT_ROOT / 'config' / 'update.json'), 'config'),
        (str(PROJECT_ROOT / 'config' / 'voices.json'), 'config'),
        # Prompts
        (str(PROJECT_ROOT / 'prompts' / 'system_prompts.py'), 'prompts'),
        # Empty dirs (created at runtime if needed)
    ],
    hiddenimports=[
        # Core
        'agents', 'app', 'config', 'providers', 'license', 'updater',
        'workflows', 'skills', 'prompts', 'tools',
        # Agents
        'agents.master_script_generator', 'agents.script_generator',
        'agents.storyboard_generator', 'agents.keyframe_generator',
        'agents.seedance_generator', 'agents.veo3_generator',
        'agents.jimeng_generator', 'agents.voiceover_generator',
        'agents.character_consistency', 'agents.character_generator',
        'agents.character_library', 'agents.continuity_engine',
        'agents.ugc_director', 'agents.ugc_score', 'agents.export_manager',
        'agents.subtitle_generator', 'agents.subtitle_alignment',
        'agents.image_prompt_generator', 'agents.viral_analyzer',
        'agents.voice_style_analyzer',
        # App
        'app.pipeline', 'app.scanner', 'app.task_manager', 'app.watcher',
        'app.product_extractor', 'app.character_extractor',
        'app.video_analyzer', 'app.ugc_director', 'app.voice_engine',
        'app.ffmpeg_voice_merge',
        # GUI
        'app.gui.gui', 'app.gui.one_click_tab', 'app.gui.one_click_controller',
        'app.gui.batch_factory_tab', 'app.gui.batch_controller',
        'app.gui.batch_scheduler', 'app.gui.settings_tab',
        'app.gui.customer_portal', 'app.gui.cost_tracker',
        'app.gui.video_history', 'app.gui.case_browser',
        'app.gui.api_wizard',
        # Config
        'config.settings', 'config.settings_manager', 'config.api_validator',
        'config.api_keys',
        # Providers
        'providers.base_provider', 'providers.openai_provider',
        'providers.claude_provider', 'providers.deepseek_provider',
        'providers.gemini_provider', 'providers.seedance_provider',
        'providers.veo3_provider', 'providers.jimeng_provider',
        'providers.runway_provider', 'providers.kling_provider',
        'providers.elevenlabs_provider',
        # License
        'license.license_manager',
        # Updater
        'updater.version_checker', 'updater.download_manager',
        'updater.update_installer', 'updater.update_manager',
        # Workflows & Skills
        'workflows.factory_workflow', 'skills.video_replication',
        # Tools
        'tools.cost_report',
        # Third-party
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
        'requests', 'dotenv', 'json', 'logging', 'hashlib',
        'subprocess', 'threading', 'queue', 'dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test', 'unittest', 'test', 'pydoc',
        'email', 'http', 'xml', 'html',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # GUI mode — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'installer' / 'factory.ico') if (PROJECT_ROOT / 'installer' / 'factory.ico').exists() else None,
)
