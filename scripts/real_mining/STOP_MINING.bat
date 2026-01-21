@echo off
echo Stopping XMRig mining...
taskkill /IM xmrig.exe /F 2>nul
echo Mining stopped.
pause
