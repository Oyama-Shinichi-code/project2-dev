@echo off
REM project2のサーバーを起動し、ブラウザでログイン画面を自動的に開くショートカット用スクリプト。
REM ダブルクリックするだけで使える。

cd /d "%~dp0"

REM 仮想環境のpython.exeが実際に存在するか確認する。無ければエラー内容を表示して一時停止する。
if not exist ".venv\Scripts\python.exe" (
    echo [エラー] 仮想環境が見つかりません: %~dp0.venv\Scripts\python.exe
    echo 先に仮想環境の作成とライブラリのインストールが必要です。
    pause
    exit /b 1
)

REM ブラウザでログイン画面を開く（サーバー起動を少し待ってから開く）。
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/login"

REM 仮想環境のPythonでuvicornサーバーを起動する（このウィンドウを閉じるとサーバーも止まる）。
".venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000

REM uvicornが異常終了した場合に、ウィンドウがすぐ閉じてエラーが読めなくなるのを防ぐ。
echo.
echo サーバーが終了しました。何かキーを押すとウィンドウを閉じます。
pause >nul
