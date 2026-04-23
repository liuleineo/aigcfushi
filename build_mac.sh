#!/bin/bash
# macOS 打包脚本
cd "$(dirname "$0")"
source venv/bin/activate
pyinstaller --noconfirm --windowed --onefile \
    --name "女装AI创作画布" \
    --add-data "config.py:." \
    main.py
echo "macOS 应用已生成在 dist/ 目录"
