#!/usr/bin/env python3
"""
生成交付压缩包脚本

用法：
    python scripts/build_release.py

输出：
    hotel_ai_butler_v2.0.zip （包含所有交付文件）

排除：
    - hotel_ai_butler.db - 本地数据库
    - .env - 环境配置（含敏感信息）
    - .DS_Store / __MACOSX - macOS 系统文件
    - .idea/ / .vscode/ - IDE 配置
    - .pytest_cache/ / __pycache__/ / *.pyc - Python 缓存
    - .git/ - Git 版本控制
    - releases/ - 历史发布包
    - tests/ - 测试代码
    - 本地调试/监视脚本 - 非交付功能
"""

import os
import shutil
import zipfile
from datetime import datetime

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_NAME = "hotel_ai_butler"
RELEASE_DIR = os.path.join(BASE_DIR, "releases")

# 版本号
VERSION = "v2.0"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
ZIP_FILENAME = f"{PROJECT_NAME}_{VERSION}_{TIMESTAMP}.zip"
ZIP_PATH = os.path.join(RELEASE_DIR, ZIP_FILENAME)

# 排除的文件/目录
EXCLUDE_PATTERNS = [
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".DS_Store",
    "__MACOSX",
    ".idea",
    ".vscode",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    "hotel_ai_butler.db",
    "hotel_ai_butler_test.db",
    ".env",
    "releases",
    ".trae",
    "*.log",
    "tests",
    "seed_demo_data.py",
    "watch_wechat_dialog.py",
    "watch_wechat_ocr.py",
    "wechat_clipboard_assistant.py",
]


def should_exclude(filepath: str) -> bool:
    """判断文件是否应排除"""
    filename = os.path.basename(filepath)
    rel_path = os.path.relpath(filepath, BASE_DIR)

    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if filename.endswith(pattern[1:]):
                return True
        elif pattern.endswith("/"):
            if f"/{pattern}" in rel_path or rel_path.startswith(pattern):
                return True
        else:
            if filename == pattern or rel_path == pattern:
                return True

    return False


def build_release():
    print("=" * 60)
    print(f"开始构建 {PROJECT_NAME} {VERSION} 交付包")
    print("=" * 60)

    # 创建 releases 目录
    os.makedirs(RELEASE_DIR, exist_ok=True)

    # 统计
    file_count = 0
    excluded_count = 0
    total_size = 0

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # 排除特定目录
            dirs[:] = [
                d
                for d in dirs
                if not should_exclude(os.path.join(root, d))
            ]

            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, BASE_DIR)

                # 排除自身（构建脚本输出）
                if rel_path.startswith("releases/"):
                    excluded_count += 1
                    continue

                if should_exclude(filepath):
                    excluded_count += 1
                    continue

                # 添加到压缩包
                arcname = os.path.join(PROJECT_NAME, rel_path)
                zipf.write(filepath, arcname)
                file_count += 1
                total_size += os.path.getsize(filepath)

    # 输出结果
    zip_size = os.path.getsize(ZIP_PATH)
    print("\n构建完成")
    print(f"   输出路径: {ZIP_PATH}")
    print(f"   文件数量: {file_count}")
    print(f"   排除数量: {excluded_count}")
    print(f"   压缩大小: {zip_size / 1024:.1f} KB")
    print(f"   原始大小: {total_size / 1024:.1f} KB")
    print("\n压缩包内容:")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        for name in sorted(zf.namelist()):
            size = zf.getinfo(name).file_size
            suffix = " (目录)" if name.endswith("/") else f" ({size} B)"
            print(f"   {name}{suffix}")

    print("\n交付包已就绪，可以发送给客户。")
    return ZIP_PATH


if __name__ == "__main__":
    build_release()
