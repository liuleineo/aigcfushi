@echo off
REM Windows 打包脚本
REM 需要在 Windows 环境下运行，且已安装 Python 和依赖
cd /d "%~dp0"
pip install pyinstaller PyQt5 requests
pyinstaller --noconfirm --windowed --onefile ^
    --name "女装AI创作画布" ^
    --add-data "config.py;." ^
    main.py
echo Windows exe 已生成在 dist\ 目录
pause
