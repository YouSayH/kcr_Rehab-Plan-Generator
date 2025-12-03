@echo off
cd /d %~dp0

:: 仮想環境の有効化
call .\venv_rehab\Scripts\activate

:: 文字コード変更
chcp 65001 > nul

:: ==========================================
:: 【監視プロセス】
:: 裏側(start /b)でPowerShellを動かし、ポート5000が応答するまで1秒ごとにチェックします。
:: 応答があり次第、ブラウザを開いてこの監視プロセスは終了します。
:: ==========================================
start /b powershell -Command "Write-Host 'サーバー起動待機中...'; $port=5000; while($true){ try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', $port); $tcp.Close(); Start-Process 'http://127.0.0.1:5000/'; break } catch { Start-Sleep -Seconds 1 } }"

:: ==========================================
:: 【サーバー起動】
:: メイン処理としてPythonサーバーを起動します。
:: ==========================================
python app.py

pause