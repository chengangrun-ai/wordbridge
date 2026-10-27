@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo   词桥 WordBridge - 一键装进清风输入法
echo ============================================
echo.

set "PY="
for %%p in (
  "C:\Users\Administrator\.workbuddy-ai\binaries\python\versions\3.13.12\python.exe"
  "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
) do (
  if exist %%p if not defined PY set "PY=%%~p"
)
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo   [!] 没找到 Python。请先装 Python 3.10 以上版本。
  echo       下载：https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

echo 使用 Python: %PY%
echo.

if not exist "data\wordbridge_comment.dict.yaml" (
  echo   [1/2] 首次运行，正在生成注释库...
  "%PY%" tools\build_comment_dict.py
  if errorlevel 1 ( echo   [!] 生成失败 & pause & exit /b 1 )
  echo.
) else (
  echo   [1/2] 注释库已存在，跳过生成
)

echo   [2/2] 安装到清风输入法...
echo.
"%PY%" tools\install.py
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%
