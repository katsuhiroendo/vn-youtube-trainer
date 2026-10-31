@echo off
chcp 65001 >nul
cd /d "%~dp0"
set CMD=
where py >nul 2>nul && set CMD=py -3
if not defined CMD where python >nul 2>nul && set CMD=python
if not defined CMD (
  echo Python が見つかりません。https://www.python.org/downloads/ からインストールしてください（Add to PATH にチェック）。
  pause
  exit /b
)
echo ベトナム語トレーナーを起動しています... このウィンドウは学習中は閉じないでください。
start "" http://localhost:8765/
%CMD% -m http.server 8765 --bind 127.0.0.1
