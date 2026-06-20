"""
Final Release Audit — scans release/client/, classifies every file, removes non-client artifacts.
"""
import os, json, shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENT = ROOT / "release" / "client"

# Classification rules
RUNTIME_DIRS = {"agents","app","providers","config","license","updater","workflows","skills","prompts"}
RUNTIME_FILES = {"launcher.py","run_factory.py","version.txt","requirements.txt",".env.example"}
CLIENT_DOCS = {"README.md","QUICK_START.md"}

# Files to DELETE (dev, test, audit, build)
REMOVE_PATTERNS = {
    "RELEASE_MANIFEST.md",              # build artifact
    "installer/setup_script.py",         # build tool (keep only in dev project)
    "case_library/*/10_PERFORMANCE_REPORT_*.md",  # dev performance reports in case lib
    "case_library/*/06_STORYBOARD_*.png", # case storyboards keep? No — too large, dev asset
}

# Also remove: anything in installer/ that isn't setup_script.py? Actually, only setup_script.py exists

def classify(rel: str) -> str:
    """Classify a single file by its relative path."""
    # Normalize path
    path = rel.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]

    # RUNTIME — matches directories
    for d in RUNTIME_DIRS:
        if path.startswith(f"{d}/"):
            return "RUNTIME"

    # RUNTIME — root files
    if path in RUNTIME_FILES:
        return "RUNTIME"

    # CLIENT DOCS
    if path in CLIENT_DOCS:
        return "CLIENT_DOC"

    # CASE LIBRARY
    if path.startswith("case_library/") and "PERFORMANCE_REPORT" not in path:
        return "CASE_LIBRARY"

    # DEV / TEST / AUDIT
    bn = os.path.basename(path).upper()
    dev_keywords = ["PERFORMANCE_REPORT", "RELEASE_MANIFEST"]
    if any(kw in bn for kw in dev_keywords):
        return "DEV_ARTIFACT"

    # BUILD TOOLS
    if path.startswith("installer/"):
        return "BUILD_TOOL"

    # UNKNOWN
    return "UNKNOWN"


def main():
    files = sorted(CLIENT.rglob("*"))
    files = [f for f in files if f.is_file() and "__pycache__" not in str(f)]

    classified = {"RUNTIME":[],"CLIENT_DOC":[],"CASE_LIBRARY":[],
                  "DEV_ARTIFACT":[],"BUILD_ARTIFACT":[],"BUILD_TOOL":[],"UNKNOWN":[]}
    removed = []

    for f in files:
        rel = str(f.relative_to(CLIENT)).replace("\\","/")
        cat = classify(rel)

        # Override: case library performance reports are DEV
        if "case_library" in rel and "PERFORMANCE_REPORT" in os.path.basename(rel).upper():
            cat = "DEV_ARTIFACT"
        # Override: RELEASE_MANIFEST is BUILD_ARTIFACT
        if "RELEASE_MANIFEST" in os.path.basename(rel).upper():
            cat = "BUILD_ARTIFACT"

        classified[cat].append(rel)

        # Auto-delete non-client files
        if cat in ("DEV_ARTIFACT", "BUILD_ARTIFACT", "BUILD_TOOL"):
            try:
                f.unlink()
                removed.append(rel)
            except Exception as e:
                print(f"  ✗ Failed to remove {rel}: {e}")

    # Clean empty dirs
    for d in sorted(CLIENT.rglob("*"), key=lambda x: len(str(x)), reverse=True):
        if d.is_dir() and d != CLIENT and not any(d.iterdir()):
            try:
                d.rmdir()
                removed.append(f"{d.relative_to(CLIENT).as_posix()}/ (empty dir)")
            except Exception:
                pass

    # Generate report
    total_size = sum(f.stat().st_size for f in CLIENT.rglob("*") if f.is_file())
    total_files = len([f for f in CLIENT.rglob("*") if f.is_file()])

    report = f"""# TikTok AI Factory Pro — Final Release Audit

## 审计日期
{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 版本
v1.0.0

---

## 审计结果

| 分类 | 保留 | 删除 |
|------|------|------|
| RUNTIME (运行时) | {len(classified['RUNTIME'])} | 0 |
| CLIENT_DOC (文档) | {len(classified['CLIENT_DOC'])} | 0 |
| CASE_LIBRARY (案例库) | {len(classified['CASE_LIBRARY'])} | 0 |
| DEV_ARTIFACT (开发) | 0 | {len([r for r in removed if r in classified.get('DEV_ARTIFACT',[])])} |
| BUILD_ARTIFACT (构建) | 0 | {len([r for r in removed if r in classified.get('BUILD_ARTIFACT',[])])} |
| BUILD_TOOL (构建工具) | 0 | {len([r for r in removed if r in classified.get('BUILD_TOOL',[])])} |
| UNKNOWN | {len(classified['UNKNOWN'])} | — |

---

## 已删除文件 ({len(removed)} 个)

"""
    for r in removed:
        report += f"- `{r}`\n"

    report += f"""
---

## 保留文件清单 ({total_files} 个文件, {total_size/1024:.1f} KB)

### RUNTIME — 客户运行必需 ({len(classified['RUNTIME'])} 个)

"""
    for f in sorted(classified['RUNTIME']):
        report += f"- `{f}`\n"

    report += f"""
### CLIENT_DOC — 客户文档 ({len(classified['CLIENT_DOC'])} 个)

"""
    for f in sorted(classified['CLIENT_DOC']):
        report += f"- `{f}`\n"

    report += f"""
### CASE_LIBRARY — 案例库 ({len(classified['CASE_LIBRARY'])} 个)

"""
    for f in sorted(classified['CASE_LIBRARY']):
        report += f"- `{f}`\n"

    if classified['UNKNOWN']:
        report += f"""
### UNKNOWN — 未分类 ({len(classified['UNKNOWN'])} 个)

"""
        for f in sorted(classified['UNKNOWN']):
            report += f"- `{f}`\n"

    report += f"""
---

## 最终包统计

| 指标 | 值 |
|------|-----|
| 总文件数 | {total_files} |
| 总大小 | {total_size/1024/1024:.1f} MB |
| Python 文件 | {len([f for f in CLIENT.rglob('*.py') if f.is_file()])} |
| 运行时文件 | {len(classified['RUNTIME'])} |
| 客户文档 | {len(classified['CLIENT_DOC'])} |
| 案例资产 | {len(classified['CASE_LIBRARY'])} |
| 已删除 | {len(removed)} |

## 判定

"""
    if classified['UNKNOWN']:
        report += "⚠️ 存在未分类文件，需人工审核。\n"
    else:
        report += "✅ **所有文件已正确分类，客户包清洁。**\n"

    report += f"""
---

*审计工具: tools/final_audit.py*
*审计时间: {datetime.now().isoformat()}*
"""

    # Write report
    (CLIENT / "FINAL_RELEASE_AUDIT.md").write_text(report, encoding="utf-8")
    (ROOT / "FINAL_RELEASE_AUDIT.md").write_text(report, encoding="utf-8")

    # Print summary
    print(f"  RUNTIME:     {len(classified['RUNTIME'])}")
    print(f"  CLIENT_DOC:  {len(classified['CLIENT_DOC'])}")
    print(f"  CASE_LIBRARY:{len(classified['CASE_LIBRARY'])}")
    print(f"  DEV:         {len(classified['DEV_ARTIFACT'])} (removed)")
    print(f"  BUILD:       {len(classified['BUILD_ARTIFACT'])} (removed)")
    print(f"  TOOL:        {len(classified['BUILD_TOOL'])} (removed)")
    print(f"  UNKNOWN:     {len(classified['UNKNOWN'])}")
    print(f"  Removed:     {len(removed)} files")
    print(f"  Kept:        {total_files} files, {total_size/1024/1024:.1f} MB")
    print(f"  Report:      FINAL_RELEASE_AUDIT.md")


if __name__ == "__main__":
    main()
